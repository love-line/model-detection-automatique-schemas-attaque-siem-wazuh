import pandas as pd
import json
import ast
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from detection import check_prefixspan, check_hmm, check_order_independent
from explanation import expliquer_detection
from config import HMM_THRESHOLD

def parse_mitre_field(value):
    if pd.isna(value):
        return []
    try:
        parsed = ast.literal_eval(value)
        return parsed if isinstance(parsed, list) else [parsed]
    except:
        return [value]

base_dir = os.path.dirname(__file__)

df_train = pd.read_csv(os.path.join(base_dir, "..", "data", "all_sequences.csv"))
df_train["sequence"] = df_train["sequence"].apply(ast.literal_eval)
df_train_reel = df_train[df_train["source"] != "synthetique_augmentation"]

df = pd.read_csv(os.path.join(base_dir, "..", "data", "alerts_extracted.csv"))
df = df[df["rule.mitre.id"].notna()]
df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.sort_values("timestamp")

print(f"{len(df)} alertes avec mapping MITRE")
detections = []
log_lines = []

for agent, group in df.groupby("agent.name"):
    sequence = []
    for value in group["rule.mitre.id"]:
        sequence.extend(parse_mitre_field(value))

    print(f"\n--- Agent : {agent} ---")
    print(f"Techniques : {sorted(set(sequence))}")

    detection = None

    match = check_prefixspan(sequence)
    if match:
        detection = {"agent": agent, "type": "correspondance_exacte_ordonnee", "pattern": match["pattern"], "confiance": "haute"}
        print(f"[PrefixSpan] {match['pattern']}")
    else:
        hmm_score = check_hmm(sequence)
        if hmm_score and hmm_score >= HMM_THRESHOLD:
            detection = {"agent": agent, "type": "correspondance_probabiliste", "score_hmm": hmm_score, "confiance": "moderee"}
            print(f"[HMM] {hmm_score:.2f}")
        else:
            match_j, jaccard = check_order_independent(sequence, df_train_reel)
            if match_j is not None:
                detection = {"agent": agent, "type": "correspondance_ensemble_sans_ordre", "similarite_jaccard": jaccard, "confiance": "faible_a_moderee"}
                print(f"[Jaccard] {jaccard:.2f}")

    if detection:
        print("  Explication Ollama...")
        explication = expliquer_detection(detection, sequence)
        detection["explication"] = explication
        detections.append(detection)
        print(f"  Explication : {explication}")

        # CONSTRUCTION DE LA LIGNE DE LOG POUR WAZUH
        pattern_str = " -> ".join(sequence)
        explication_compacte = explication.replace("\n", " ").replace("|", ";")[:300]
        log_line = f"IA_DETECTION | AGENT={agent} | TYPE={detection['type']} | CONFIANCE={detection['confiance']} | PATTERN={pattern_str} | EXPLICATION={explication_compacte}"
        log_lines.append(log_line)

output_path = os.path.join(base_dir, "..", "data", "detections_enrichies.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(detections, f, indent=2, ensure_ascii=False, default=str)

log_path = os.path.join(base_dir, "..", "data", "detections_wazuh.log")
with open(log_path, "w", encoding="utf-8") as f:
    f.write("\n".join(log_lines))

print(f"\n{len(detections)} détections expliquées")
