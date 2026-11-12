import json

# 1. CHARGEMENT
with open("data/patterns.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Gérer l'ancien format (liste simple) et le nouveau format (dict avec metadata)
if isinstance(data, list):
    patterns = data
    metadata = {}
else:
    patterns = data.get("patterns", [])
    metadata = data.get("metadata", {})

print("=" * 80)
print("FILTRAGE DES MOTIFS PREFIXSPAN")
print("=" * 80)

if metadata:
    print(f"\nCorpus : {metadata.get('nb_sequences_totales', '?')} sequences")
    print(f"Minsup : {metadata.get('minsup', '?')}")
    print(f"Motifs bruts : {metadata.get('nb_motifs_bruts', len(patterns))}")

# 2. GARDER SEULEMENT LES MOTIFS DE LONGUEUR >= 3
patterns = [p for p in patterns if len(p["pattern"]) >= 3]
print(f"\nApres filtre longueur >= 3 : {len(patterns)} motifs")

# 3. SUPPRIMER LES SOUS-MOTIFS REDONDANTS
def is_subsequence_correct(short, long):
    """Vérifie si 'short' est une sous-séquence de 'long' (ordre préservé)"""
    iterator = iter(long)
    for item in short:
        found = False
        for candidate in iterator:
            if candidate == item:
                found = True
                break
        if not found:
            return False
    return True

# Trier par support décroissant puis longueur décroissante
patterns.sort(key=lambda x: (x["support"], len(x["pattern"])), reverse=True)

filtered = []
for p in patterns:
    is_redundant = False
    for kept in filtered:
        if (is_subsequence_correct(p["pattern"], kept["pattern"]) 
            and p["pattern"] != kept["pattern"]
            and kept["support"] >= p["support"]):
            is_redundant = True
            break
    if not is_redundant:
        filtered.append(p)

print(f"Apres suppression des sous-motifs : {len(filtered)} motifs")

# 4. AFFICHAGE
print("\n" + "=" * 80)
print(f"MOTIFS DISCRIMINANTS RETENUS ({len(filtered)})")
print("=" * 80)
for p in filtered[:20]:
    print(f"Support={p['support']:2d} | Long={len(p['pattern']):2d} | {' -> '.join(p['pattern'])}")

# 5. SAUVEGARDE
output = {
    "metadata": {
        **metadata,
        "nb_motifs_apres_filtrage": len(filtered)
    },
    "patterns": filtered
}

with open("data/patterns_filtered.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nSauvegarde : data/patterns_filtered.json")
