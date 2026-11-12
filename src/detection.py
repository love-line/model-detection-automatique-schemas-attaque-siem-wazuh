import json
import pickle
import numpy as np
import ast
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from config import HMM_THRESHOLD, JACCARD_THRESHOLD

with open(os.path.join(os.path.dirname(__file__), "..", "data", "patterns_filtered.json"), "r", encoding="utf-8") as f:
    patterns = json.load(f)["patterns"]

with open(os.path.join(os.path.dirname(__file__), "..", "data", "hmm_model.pkl"), "rb") as f:
    hmm_data = pickle.load(f)

A = hmm_data["A"]
B = hmm_data["B"]
pi = hmm_data["pi"]
technique_to_id = hmm_data["technique_to_id"]

def is_subsequence(short, long):
    it = iter(long)
    return all(item in it for item in short)

def check_prefixspan(sequence):
    matches = []
    for p in patterns:
        if is_subsequence(p["pattern"], sequence):
            matches.append(p)
    if matches:
        return max(matches, key=lambda x: len(x["pattern"]))
    return None

def jaccard_similarity(set1, set2):
    set1, set2 = set(set1), set(set2)
    if not set1 or not set2:
        return 0.0
    return len(set1 & set2) / len(set1 | set2)

def check_order_independent(sequence, df_train_reel):
    best_match = None
    best_score = 0.0
    for idx, row in df_train_reel.iterrows():
        score = jaccard_similarity(sequence, row["sequence"])
        if score > best_score:
            best_score = score
            best_match = row
    if best_score >= JACCARD_THRESHOLD:
        return best_match, best_score
    return None, best_score

def forward_score(seq_ids, A, B, pi):
    T = len(seq_ids)
    n_states = A.shape[0]
    alpha = np.zeros((T, n_states))
    c = np.zeros(T)
    alpha[0] = pi * B[:, seq_ids[0]]
    c[0] = alpha[0].sum()
    if c[0] == 0:
        return None
    alpha[0] /= c[0]
    for t in range(1, T):
        alpha[t] = (alpha[t-1] @ A) * B[:, seq_ids[t]]
        c[t] = alpha[t].sum()
        if c[t] == 0:
            return None
        alpha[t] /= c[t]
    return np.sum(np.log(c))

def check_hmm(sequence):
    seq_ids = [technique_to_id[t] for t in sequence if t in technique_to_id]
    if len(seq_ids) < 2:
        return None
    score = forward_score(seq_ids, A, B, pi)
    if score is None:
        return None
    return score / len(seq_ids)
