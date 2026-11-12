import pandas as pd
import ast
import numpy as np
import pickle

# 1. CHARGEMENT
df = pd.read_csv("data/all_sequences.csv")
df["sequence"] = df["sequence"].apply(ast.literal_eval)

# 2. SELECTION DES SEQUENCES REELLES (exclure uniquement les synthétiques)
sources_synthetiques = ["synthetique_augmentation"]
df_real = df[(~df["source"].isin(sources_synthetiques)) & (df["label"] != 0)]
sequences = df_real["sequence"].tolist()
titles = df_real["title"].tolist()
sources = df_real["source"].tolist()

print("=" * 80)
print("ENTRAINEMENT HMM - SEQUENCES REELLES UNIQUEMENT")
print("=" * 80)
print(f"\nTotal sequences reelles : {len(sequences)}")
print(f"Total sequences synthetiques exclues : {len(df) - len(sequences)}")

# Afficher la répartition des sources
source_counts = df_real["source"].value_counts()
print("\nRepartition des sources reelles :")
for source, count in source_counts.items():
    print(f"  - {source} : {count}")

# 3. ENCODAGE DES TECHNIQUES
all_techniques = sorted(set(t for seq in sequences for t in seq))
technique_to_id = {t: i for i, t in enumerate(all_techniques)}
id_to_technique = {i: t for t, i in technique_to_id.items()}
n_obs = len(all_techniques)
n_states = 8

print(f"\nNombre de techniques distinctes : {n_obs}")
print(f"Nombre d'etats caches : {n_states}")

encoded_sequences = [[technique_to_id[t] for t in seq] for seq in sequences]

# 4. INITIALISATION ALEATOIRE
np.random.seed(42)
A = np.random.dirichlet(np.ones(n_states), size=n_states)
B = np.random.dirichlet(np.ones(n_obs), size=n_states)
pi = np.random.dirichlet(np.ones(n_states))

EPSILON = 0.01

# 5. FORWARD-BACKWARD (CORRIGÉ)
def forward_backward(seq, A, B, pi):
    T = len(seq)
    alpha = np.zeros((T, n_states))
    beta = np.zeros((T, n_states))
    c = np.zeros(T)
    
    alpha[0] = pi * B[:, seq[0]]
    c[0] = alpha[0].sum()
    alpha[0] /= c[0]
    
    for t in range(1, T):
        alpha[t] = (alpha[t-1] @ A) * B[:, seq[t]]
        c[t] = alpha[t].sum()
        alpha[t] /= c[t]
    
    beta[T-1] = 1
    for t in range(T-2, -1, -1):
        beta[t] = (A @ (B[:, seq[t+1]] * beta[t+1])) / c[t+1]
    
    return alpha, beta, c

# 6. ALGORITHME BAUM-WELCH
N_ITER = 50
print(f"\nEntrainement Baum-Welch ({N_ITER} iterations)...")

for iteration in range(N_ITER):
    A_num = np.zeros((n_states, n_states))
    B_num = np.zeros((n_states, n_obs))
    pi_num = np.zeros(n_states)
    A_den = np.zeros(n_states)
    B_den = np.zeros(n_states)
    
    for seq in encoded_sequences:
        T = len(seq)
        alpha, beta, c = forward_backward(seq, A, B, pi)
        gamma = alpha * beta
        
        pi_num += gamma[0]
        
        for t in range(T-1):
            xi = np.outer(alpha[t], B[:, seq[t+1]] * beta[t+1]) * A / c[t+1]
            A_num += xi
        
        A_den += gamma[:-1].sum(axis=0)
        
        for t in range(T):
            B_num[:, seq[t]] += gamma[t]
        
        B_den += gamma.sum(axis=0)
    
    pi = (pi_num + EPSILON) / (len(encoded_sequences) + EPSILON * n_states)
    A = (A_num + EPSILON) / (A_den[:, None] + EPSILON * n_states)
    B = (B_num + EPSILON) / (B_den[:, None] + EPSILON * n_obs)
    
    if (iteration + 1) % 10 == 0:
        print(f"  Iteration {iteration + 1}/{N_ITER} terminee")

print("Entrainement termine")

# 7. SAUVEGARDE
with open("data/hmm_model.pkl", "wb") as f:
    pickle.dump({
        "A": A,
        "B": B,
        "pi": pi,
        "technique_to_id": technique_to_id,
        "id_to_technique": id_to_technique,
        "n_states": n_states,
        "n_sequences_entrainement": len(sequences),
        "n_techniques": n_obs
    }, f)
print("Modele sauvegarde : data/hmm_model.pkl")

# 8. SCORES DE VRAISEMBLANCE
def log_likelihood(seq, A, B, pi):
    _, _, c = forward_backward(seq, A, B, pi)
    return np.sum(np.log(c))

print("\n" + "=" * 80)
print("SCORES DE VRAISEMBLANCE (sequences d'entrainement)")
print("=" * 80)
scores = []
for i in range(len(encoded_sequences)):
    score = log_likelihood(encoded_sequences[i], A, B, pi)
    normalized = score / len(encoded_sequences[i])
    scores.append((normalized, titles[i], sources[i]))

scores.sort(key=lambda x: x[0], reverse=True)
for score, titre, source in scores:
    print(f"Score normalise={score:8.2f} | {titre[:50]:50s} | {source}")
