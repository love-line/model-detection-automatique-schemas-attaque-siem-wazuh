#!/bin/bash

ALERTS_FILE="/var/ossec/logs/alerts/alerts.json"
PROJET_DIR="/home/ser-waz/projet-memoire"
VENV="$PROJET_DIR/venv/bin/activate"

echo "Surveillance inotify démarrée sur $ALERTS_FILE"

# Surveiller les modifications du fichier d'alertes
inotifywait -m -e modify --format '%w%f' "$ALERTS_FILE" | while read CHANGED_FILE
do
    echo "Changement détecté à $(date)"
    
    # Se déplacer dans le projet et activer le venv
    cd "$PROJET_DIR"
    source "$VENV"
    
    # 1. Extraire les alertes Wazuh
    python extractor.py
    
    # 2. Lancer la détection IA
    cd src
    python main.py
    
    # 3. Copier le fichier de détections vers Wazuh
    sudo cp "$PROJET_DIR/data/detections_wazuh.log" /var/ossec/logs/detections_wazuh.log
    sudo chown wazuh:wazuh /var/ossec/logs/detections_wazuh.log
    sudo chmod 644 /var/ossec/logs/detections_wazuh.log
    
    echo "Détection terminée à $(date)"
done
