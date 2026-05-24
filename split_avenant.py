import sys

with open('frontend/src/lib/components/fiche-bien/FicheBienBail.svelte', 'r') as f:
    lines = f.readlines()

out = []
i = 0
while i < len(lines):
    line = lines[i]
    if line.strip() == "import FicheBienBailRegularisation from './FicheBienBailRegularisation.svelte';":
        out.append(line)
        out.append("\timport FicheBienBailAvenant from './FicheBienBailAvenant.svelte';\n")
    elif line.strip() == "import { updateLocataire, cloturerBail, donnerConge, creerAvenant, updateBail, type ClotureBailPayload } from '$lib/api';":
        out.append("\timport { updateLocataire, cloturerBail, donnerConge, updateBail, type ClotureBailPayload } from '$lib/api';\n")
    elif line.strip() == "// ── Avenant bail ─────────────────────────":
        out.append("\tlet showAvenantForm = $state(false);\n")
        out.append("\tfunction openAvenantForm() {\n")
        out.append("\t\tshowAvenantForm = true;\n")
        out.append("\t}\n")
        while not lines[i].strip().startswith('// ── Congé locataire/bailleur ─────────────────────────'):
            i += 1
        out.append(lines[i])
    elif line.strip() == "<!-- Avenant au bail -->":
        out.append("\t\t\t<!-- Avenant au bail -->\n")
        out.append("\t\t\t<FicheBienBailAvenant bind:showForm={showAvenantForm} {bail} {sciId} {bienId} {onRefresh} />\n")
        while not lines[i].strip() == "<!-- Congé -->":
            i += 1
        out.append(lines[i])
    else:
        out.append(line)
    i += 1

with open('frontend/src/lib/components/fiche-bien/FicheBienBail.svelte', 'w') as f:
    f.writelines(out)

