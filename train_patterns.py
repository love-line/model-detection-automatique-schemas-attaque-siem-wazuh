import pandas as pd
import ast
import json
from prefixspan import PrefixSpan
from datetime import datetime

# 1. CHARGEMENT
df = pd.read_csv("data/all_sequences.csv")
df["sequence"] = df["sequence"].apply(ast.literal_eval)

# 2. SEPARATION REEL / SYNTHETIQUE
sources_synthetiques = ["synthetique_augmentation"]
df_reel = df[~df["source"].isin(sources_synthetiques)]
df_synth = df[(df["source"].isin(sources_synthetiques)) | (df["label"] == 0)]

print("=" * 80)
print("ENTRAINEMENT PREFIXSPAN - CORPUS 59 SEQUENCES")
print("=" * 80)
print(f"\nTotal sequences     : {len(df)}")
print(f"  - reelles         : {len(df_reel)}")
print(f"  - synthetiques    : {len(df_synth)}")
print(f"  - longueur moyenne : {df['sequence_length'].mean():.2f}")

# 3. ENTRAINEMENT SUR TOUT LE CORPUS (réel + synthétique)
sequences = df["sequence"].tolist()
ps = PrefixSpan(sequences)

# 4. MINSUP = 3
MINSUP = 3
print(f"\nMinsup : {MINSUP}")

frequent_patterns = ps.frequent(MINSUP)

# 5. FILTRAGE LONGUEUR >= 2
filtered_patterns = [(s, p) for s, p in frequent_patterns if len(p) >= 2]
filtered_patterns.sort(key=lambda x: (x[0], len(x[1])), reverse=True)

print(f"\nMotifs bruts : {len(frequent_patterns)}")
print(f"Motifs longueur >= 2 : {len(filtered_patterns)}")

# 6. AFFICHAGE TOP 30
print("\n" + "=" * 80)
print("TOP 30 MOTIFS")
print("=" * 80)
for support, pattern in filtered_patterns[:30]:
    print(f"Support={support:2d} | Long={len(pattern):2d} | {' -> '.join(pattern)}")

# 7. SAUVEGARDE
output = {
    "metadata": {
        "date_entrainement": datetime.now().isoformat(),
        "nb_sequences_totales": len(sequences),
        "nb_sequences_reelles": len(df_reel),
        "nb_sequences_synthetiques": len(df_synth),
        "minsup": MINSUP,
        "nb_motifs_bruts": len(frequent_patterns),
        "nb_motifs_longueur_2_plus": len(filtered_patterns)
    },
    "patterns": [
        {"support": s, "pattern": p}
        for s, p in filtered_patterns
    ]
}

with open("data/patterns.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nSauvegarde : data/patterns.json")
