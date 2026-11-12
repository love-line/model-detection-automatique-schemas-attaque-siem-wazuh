import requests
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from mitre_data import MITRE_DETAILS

OLLAMA_SERVER = "http://192.168.65.1:5000/explain"

def expliquer_detection(detection, sequence):
    contexte_techniques = []
    
    for tech in sequence:
        info = MITRE_DETAILS.get(tech, {"nom": tech, "tactique": "Inconnue", "description": "technique non documentée"})
        contexte_techniques.append(f"{tech} ({info['nom']}) : {info['description']}")
    
    contexte = " | ".join(contexte_techniques)
    
    prompt = f"""Explique en 3 phrases ces techniques MITRE : {contexte}. Detection sur {detection.get('agent', 'inconnu')}."""
    
    try:
        response = requests.post(
            OLLAMA_SERVER,
            json={"prompt": prompt},
            timeout=300
        )
        if response.status_code == 200:
            return response.json().get("explication", "Pas d'explication")
        else:
            return f"Erreur serveur : {response.status_code}"
    except Exception as e:
        return f"Erreur : {e}"
