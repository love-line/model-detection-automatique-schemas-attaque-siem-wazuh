import json
import pandas as pd

ALERTS_FILE = "/var/ossec/logs/chemin ou sont stoques les alertes wazuh"
OUTPUT_FILE = "/home/le chemin vers le fichier.cvs ou les alertes extraitent seront stoques"

events = []
with open(ALERTS_FILE, "r", encoding="utf-8", errors="replace") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
            level = event.get("rule", {}).get("level", 0)
            mitre = event.get("rule", {}).get("mitre", {})
            
            # FILTRE : niveau >= 7 ET mapping MITRE present
            if level >= 7 and mitre:
                events.append(event)
        except json.JSONDecodeError:
            continue

print(f"Alertes filtrees (niveau >= 7 + MITRE) : {len(events)}")

if len(events) == 0:
    print("Aucune alerte trouvee.")
else:
    df = pd.json_normalize(events)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    print(f"Fichier sauvegarde : {OUTPUT_FILE}")
