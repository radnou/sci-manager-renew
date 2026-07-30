"""Garde-fou : le seed et le cleanup démo doivent écrire en service_role.

Depuis la migration 043 (audit C3), la policy `associes_member_insert` exige
d'être déjà gérant de la SCI ciblée. La SCI de démonstration vient d'être créée
et n'a encore aucun associé : avec le client utilisateur, l'insertion du gérant
est rejetée par RLS et **tout le parcours demo-first casse en production**.

Pourquoi un test au niveau du source et non un test HTTP : le faux client
Supabase des tests n'applique pas RLS, donc aucun appel d'endpoint ne peut
constater la violation. Une première version passait par `POST /demo/seed` en
capturant le client transmis, mais la route déclare `status_code=201` et ses
retours anticipés (« données déjà chargées », « abonnement actif ») répondent 201
eux aussi ; selon l'ordre d'exécution des tests, le faux client partagé
(session-scoped, mutualisé entre les tests d'un même worker xdist) faisait
court-circuiter l'appel et le test devenait vert en local, rouge en CI.

L'invariant réel est syntaxique : les deux services reçoivent le client
service_role. On le vérifie sur l'AST, ce qu'aucun monkeypatch ne peut masquer.
"""

import ast
import pathlib

import pytest

DEMO_MODULE = (
    pathlib.Path(__file__).resolve().parent.parent.parent
    / "app"
    / "api"
    / "v1"
    / "demo.py"
)

SERVICES_ATTENDUS = ("seed_demo_data", "cleanup_demo_data")


def _appels(nom_fonction: str) -> list[ast.Call]:
    tree = ast.parse(DEMO_MODULE.read_text(encoding="utf-8"))
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == nom_fonction
    ]


@pytest.mark.parametrize("service", SERVICES_ATTENDUS)
def test_demo_service_recoit_un_client_service_role(service: str):
    appels = _appels(service)
    assert appels, f"aucun appel à {service} trouvé dans {DEMO_MODULE.name}"

    for appel in appels:
        assert appel.args, f"{service} appelé sans argument de client"
        premier = appel.args[0]
        assert isinstance(premier, ast.Call) and isinstance(premier.func, ast.Name), (
            f"{service} doit recevoir get_supabase_service_client() en premier "
            f"argument, pas une variable — sinon l'identité du client n'est plus "
            f"vérifiable ici."
        )
        assert premier.func.id == "get_supabase_service_client", (
            f"{service} reçoit {premier.func.id}() : avec le client utilisateur, "
            f"la policy associes_member_insert de la migration 043 rejette "
            f"l'insertion du gérant sur une SCI neuve et le parcours demo-first "
            f"casse en production."
        )


def test_demo_importe_la_factory_service_role():
    """L'import doit exister, sinon l'appel lèverait un NameError (cf. MED-14)."""
    tree = ast.parse(DEMO_MODULE.read_text(encoding="utf-8"))
    importes = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    assert "get_supabase_service_client" in importes
