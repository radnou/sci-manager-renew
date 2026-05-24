import sys

with open('frontend/src/lib/components/fiche-bien/FicheBienBail.svelte', 'r') as f:
    lines = f.readlines()

out = []
i = 0
while i < len(lines):
    line = lines[i]
    if line.strip() == "import BailModal from '$lib/components/fiche-bien/modals/BailModal.svelte';":
        out.append(line)
        out.append("\timport FicheBienBailRegularisation from './FicheBienBailRegularisation.svelte';\n")
    elif line.strip() == "// ── Régularisation charges ─────────────────────────":
        # Skip until the end of handleConfirmRegularisation
        while not lines[i].strip().startswith('const motifOptions'):
            i += 1
        out.append(lines[i])
    elif line.strip() == "<!-- Régularisation des charges -->":
        # Check if next line is {#if bail.statut === 'en_cours'}
        out.append("\t\t\t<!-- Régularisation des charges -->\n")
        out.append("\t\t\t<FicheBienBailRegularisation {bail} {sciId} {bienId} {isGerant} {onRefresh} />\n")
        
        # Skip until we hit <!-- Locataires Cards -->
        while i < len(lines) and lines[i].strip() != "<!-- Locataires Cards -->":
            i += 1
        # Now we are at <!-- Locataires Cards -->
        out.append("\n")
        out.append(lines[i])
    else:
        out.append(line)
    i += 1

with open('frontend/src/lib/components/fiche-bien/FicheBienBail.svelte', 'w') as f:
    f.writelines(out)

