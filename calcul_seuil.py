import pandas as pd
import ast
import numpy as np
import pickle
import json

# 1. CHARGEMENT DU MODELE HMM
with open("data/hmm_model.pkl", "rb") as f:
    saved = pickle.load(f)

A = saved["A"]
B = saved["B"]
pi = saved["pi"]
technique_to_id = saved["technique_to_id"]
n_states = saved["n_states"]

# 2. CHARGEMENT DES SEQUENCES D'ENTRAINEMENT
df = pd.read_csv("data/all_sequences.csv")
df["sequence"] = df["sequence"].apply(ast.literal_eval)

sources_synthetiques = ["synthetique_augmentation"]
df_real = df[~df["source"].isin(sources_synthetiques)]
df_synth = df[df["source"].isin(sources_synthetiques)]

print("=" * 80)
print("CALCUL DU SEUIL DE DETECTION HMM")
print("=" * 80)

# 3. FONCTION FORWARD
def forward(seq, A, B, pi):
    T = len(seq)
    alpha = np.zeros((T, A.shape[0]))
    c = np.zeros(T)
    
    alpha[0] = pi * B[:, seq[0]]
    c[0] = alpha[0].sum()
    alpha[0] /= c[0]
    
    for t in range(1, T):
        alpha[t] = (alpha[t-1] @ A) * B[:, seq[t]]
        c[t] = alpha[t].sum()
        alpha[t] /= c[t]
    
    return np.sum(np.log(c))

def score_sequence(technique_list):
    seq = [technique_to_id[t] for t in technique_list if t in technique_to_id]
    if len(seq) == 0:
        return None
    score = forward(seq, A, B, pi)
    return score / len(seq)

# 4. SCORES DES SEQUENCES REELLES (POSITIFS = ATTAQUES)
print("\n1. SCORES DES SEQUENCES REELLES (ATTAQUES)")
print("-" * 80)

scores_reels = []
for idx, row in df_real.iterrows():
    score = score_sequence(row["sequence"])
    if score is not None:
        scores_reels.append(score)
        print(f"  Score={score:8.2f} | {row['title'][:50]:50s}")

scores_reels = np.array(scores_reels)
print(f"\n  Nombre : {len(scores_reels)}")
print(f"  Moyenne : {scores_reels.mean():.2f}")
print(f"  Ecart-type : {scores_reels.std():.2f}")
print(f"  Min : {scores_reels.min():.2f}")
print(f"  Max : {scores_reels.max():.2f}")

# 5. SCORES DES SEQUENCES SYNTHETIQUES (pour comparaison)
print("\n2. SCORES DES SEQUENCES SYNTHETIQUES")
print("-" * 80)

scores_synth = []
for idx, row in df_synth.iterrows():
    score = score_sequence(row["sequence"])
    if score is not None:
        scores_synth.append(score)

scores_synth = np.array(scores_synth)
print(f"\n  Nombre : {len(scores_synth)}")
print(f"  Moyenne : {scores_synth.mean():.2f}")
print(f"  Ecart-type : {scores_synth.std():.2f}")
print(f"  Min : {scores_synth.min():.2f}")
print(f"  Max : {scores_synth.max():.2f}")

# 6. GENERATION DE BRUIT ALEATOIRE (NEGATIFS = NON-ATTAQUES)
print("\n3. SCORES DE BRUIT ALEATOIRE (NON-ATTAQUES)")
print("-" * 80)

all_techniques = list(technique_to_id.keys())
np.random.seed(42)

scores_bruit = []
for _ in range(100):
    longueur = np.random.randint(3, 10)
    seq_bruit = np.random.choice(all_techniques, size=longueur, replace=False).tolist()
    score = score_sequence(seq_bruit)
    if score is not None:
        scores_bruit.append(score)

scores_bruit = np.array(scores_bruit)
print(f"\n  Nombre : {len(scores_bruit)}")
print(f"  Moyenne : {scores_bruit.mean():.2f}")
print(f"  Ecart-type : {scores_bruit.std():.2f}")
print(f"  Min : {scores_bruit.min():.2f}")
print(f"  Max : {scores_bruit.max():.2f}")

# 7. CALCUL DES SEUILS CANDIDATS
print("\n4. SEUILS CANDIDATS")
print("-" * 80)

# Méthode 1 : Percentile 5% des scores réels
seuil_percentile_5 = np.percentile(scores_reels, 5)
print(f"  Percentile 5% des attaques : {seuil_percentile_5:.2f}")

# Méthode 2 : Moyenne - 1 écart-type
seuil_1std = scores_reels.mean() - scores_reels.std()
print(f"  Moyenne - 1 ecart-type     : {seuil_1std:.2f}")

# Méthode 3 : Moyenne - 2 écarts-types
seuil_2std = scores_reels.mean() - 2 * scores_reels.std()
print(f"  Moyenne - 2 ecarts-types   : {seuil_2std:.2f}")

# Méthode 4 : Point médian entre le pire score d'attaque et le meilleur score de bruit
pire_attaque = scores_reels.min()
meilleur_bruit = scores_bruit.max()
seuil_midpoint = (pire_attaque + meilleur_bruit) / 2
print(f"  Point median attaque/bruit : {seuil_midpoint:.2f}")

# 8. CHOIX DU SEUIL RECOMMANDE
print("\n5. SEUIL RECOMMANDE")
print("-" * 80)

# Le percentile 5% est le plus robuste : il accepte 95% des attaques réelles
seuil_recommande = seuil_percentile_5
print(f"  Seuil recommande : {seuil_recommande:.2f}")

# 9. EVALUATION DU SEUIL
print("\n6. EVALUATION DU SEUIL")
print("-" * 80)

vp = np.sum(scores_reels >= seuil_recommande)
fn = np.sum(scores_reels < seuil_recommande)
fp = np.sum(scores_bruit >= seuil_recommande)
vn = np.sum(scores_bruit < seuil_recommande)

print(f"  Vrais positifs (attaques detectees) : {vp}/{len(scores_reels)}")
print(f"  Faux negatifs (attaques manquees)   : {fn}/{len(scores_reels)}")
print(f"  Faux positifs (bruit detecte)       : {fp}/{len(scores_bruit)}")
print(f"  Vrais negatifs (bruit rejete)       : {vn}/{len(scores_bruit)}")

precision = vp / (vp + fp) if (vp + fp) > 0 else 0
rappel = vp / (vp + fn) if (vp + fn) > 0 else 0
f1 = 2 * precision * rappel / (precision + rappel) if (precision + rappel) > 0 else 0

print(f"\n  Precision : {precision:.2f}")
print(f"  Rappel    : {rappel:.2f}")
print(f"  F1-score  : {f1:.2f}")

# 10. SAUVEGARDE DU SEUIL
seuil_config = {
    "seuil_recommande": float(seuil_recommande),
    "methode": "percentile_5_attaques",
    "scores_attaques": {
        "moyenne": float(scores_reels.mean()),
        "ecart_type": float(scores_reels.std()),
        "min": float(scores_reels.min()),
        "max": float(scores_reels.max())
    },
    "scores_bruit": {
        "moyenne": float(scores_bruit.mean()),
        "ecart_type": float(scores_bruit.std()),
        "min": float(scores_bruit.min()),
        "max": float(scores_bruit.max())
    },
    "evaluation": {
        "vrais_positifs": int(vp),
        "faux_negatifs": int(fn),
        "faux_positifs": int(fp),
        "vrais_negatifs": int(vn),
        "precision": float(precision),
        "rappel": float(rappel),
        "f1": float(f1)
    }
}

with open("data/seuil_hmm.json", "w", encoding="utf-8") as f:
    json.dump(seuil_config, f, indent=2, ensure_ascii=False)

print(f"\n  Seuil sauvegarde dans data/seuil_hmm.json")
