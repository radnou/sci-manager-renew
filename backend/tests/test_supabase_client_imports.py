"""Garde-fou statique : tout client Supabase utilisé doit être importé.

MED-14 : `import_csv.py` appelait `get_supabase_user_client` sans l'importer —
`NameError`, donc 500 systématique sur l'import CSV. Le bug a survécu à la suite
de tests parce que `conftest.py` fait
`monkeypatch.setattr(mod, "get_supabase_user_client", ..., raising=False)` :
le `raising=False` *crée* l'attribut manquant sur le module, et tous les tests
passent sur du code qui ne peut pas tourner en production.

Aucune assertion runtime ne peut donc attraper cette famille de bugs. On lit le
source à la place.
"""

import ast
import pathlib

import pytest

APP_DIR = pathlib.Path(__file__).resolve().parent.parent / "app"

# Les factories concernées, celles que conftest monkeypatche avec raising=False.
CLIENT_FACTORIES = {
    "get_supabase_user_client",
    "get_supabase_service_client",
    "get_supabase_anon_client",
}


def _python_files() -> list[pathlib.Path]:
    return sorted(p for p in APP_DIR.rglob("*.py") if p.suffix == ".py")


def _names_bound(tree: ast.AST) -> set[str]:
    """Noms disponibles au niveau module : imports, defs, assignations."""
    bound: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                bound.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bound.add(node.name)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            bound.add(node.id)
    return bound


@pytest.mark.parametrize("path", _python_files(), ids=lambda p: str(p.name))
def test_supabase_client_factories_are_imported(path: pathlib.Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    bound = _names_bound(tree)

    used = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in CLIENT_FACTORIES
    }

    manquants = sorted(used - bound)
    assert not manquants, (
        f"{path.relative_to(APP_DIR.parent)} appelle {manquants} sans les importer "
        "→ NameError en production (les tests le masquent via raising=False)."
    )
