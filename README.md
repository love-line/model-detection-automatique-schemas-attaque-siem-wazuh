# 🛡️ Reconnaissance intelligente des chaînes d'attaque dans un SIEM

<p align="center">
  **Détecter les attaques isolément ne suffit plus. Comprendre leur enchaînement change tout.**
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/SIEM-Wazuh-1677B8?logo=elastic&logoColor=white" />
  <img src="https://img.shields.io/badge/Framework-MITRE%20ATT%26CK-red" />
  <img src="https://img.shields.io/badge/IA-Modèle%20probabiliste-purple" />
  <img src="https://img.shields.io/badge/Statut-Prototype%20expérimental-orange" />
</p>

---

## 🎯 Et si une alerte n'était que le début d'une attaque ?

Dans un environnement informatique, une attaque ne se manifeste pas nécessairement par un événement isolé. Elle peut se construire progressivement à travers plusieurs techniques, chacune produisant des alertes qui, prises individuellement, semblent parfois anodines.

Le véritable enjeu est donc de comprendre les relations entre ces événements pour identifier une progression malveillante.

**Ce projet explore une approche de détection intelligente capable de reconnaître des schémas d'attaque multi-étapes à partir des alertes d'un SIEM enrichies par le référentiel MITRE ATT&CK.**

L'objectif : passer d'une lecture individuelle des alertes à une compréhension séquentielle des comportements d'attaque.

## 🔬 Une approche hybride : deux méthodes complémentaires

Le système repose sur la complémentarité de deux approches algorithmiques.

### 01. PrefixSpan — Découvrir les motifs d'attaque

L'algorithme PrefixSpan est utilisé pour extraire automatiquement les motifs séquentiels fréquents à partir des séquences de techniques MITRE ATT&CK.

Il permet notamment de :
- Identifier les enchaînements récurrents de techniques.
- Extraire des motifs discriminants.
- Mettre en évidence des comportements d'attaque structurés.

### 02. HMM — Généraliser la reconnaissance

Le modèle de Markov caché (Hidden Markov Model) intervient pour modéliser les relations probabilistes entre les techniques observées.

Il permet d'explorer :
- La progression probable d'une chaîne d'attaque.
- La reconnaissance de séquences partielles ou variantes.
- La généralisation au-delà des motifs strictement identiques à ceux appris.

**Pourquoi combiner les deux ?**

PrefixSpan découvre les structures récurrentes ; le HMM apporte une capacité de généralisation probabiliste. Leur complémentarité constitue le cœur de l'approche proposée.

## ⚙️ Architecture du système

Le fonctionnement général s'articule autour de plusieurs étapes :

```text
       ALERTES DU SIEM (WAZUH)
                  |
                  ▼
       Extraction des événements
                  |
                  ▼
       Enrichissement MITRE ATT&CK
                  |
                  ▼
       Construction des séquences
                  |
          ┌───────┴────────┐
          ▼                ▼
      PREFIXSPAN           HMM
          |                |
          ▼                ▼
    Motifs fréquents   Modélisation
                       probabiliste
          |                |
          └───────┬────────┘
                  ▼
         Reconnaissance des
         chaînes d'attaque
                  |
                  ▼
        Réinjection de l'alerte
             dans Wazuh
                  |
                  ▼
       Explication en français
       avec un modèle local (LLM)
```

Le système est conçu pour enrichir les capacités d'analyse de Wazuh en apportant une lecture séquentielle des événements.

## 🧠 Technologies et outils

| Technologie | Utilisation |
|---|---|
| Python | Développement du système |
| Pandas | Préparation et manipulation des données |
| PrefixSpan | Extraction de motifs séquentiels |
| HMM | Modélisation probabiliste |
| MITRE ATT&CK | Référentiel des techniques d'attaque |
| Wazuh | Collecte, supervision et gestion des alertes |
| Ollama | Explication locale des détections par LLM |
| JSON / CSV | Stockage et échange des données |

## 📂 Organisation du projet

```text
.
├── README.md
├── requirements.txt
├── extractor.py
├── train_patterns.py
├── train_hmm.py
├── filter_patterns.py
├── calcul_seuil.py
├── watch_detections.sh
│
├── src/
│   ├── config.py
│   ├── detection.py
│   ├── explanation.py
│   ├── main.py
│   └── mitre_data.py
│
└── data/
    ├── mordor_sequences.csv
    ├── synthetic_sequences.csv
    ├── patterns.json
    ├── patterns_filtered.json
    ├── hmm_model.pkl
    ├── seuil_hmm.json
    ├── technique_to_tactic.json
    └── attackflow_sequences.csv
```

*Cette arborescence présente les principaux composants du projet. Les fichiers et jeux de données disponibles peuvent varier selon la version publiée.*

## 🚀 Installation et expérimentation

### Prérequis

- Python 3.10 ou supérieur
- Un environnement Linux
- Git
- Wazuh pour l'expérimentation de l'intégration
- Ollama pour le module d'explication locale (facultatif)

### 1. Cloner le dépôt

```bash
git clone https://github.com/love-line/model-detection-automatique-schemas-attaque-siem-wazuh.git

cd model-detection-automatique-schemas-attaque-siem-wazuh
```

### 2. Créer un environnement virtuel

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Lancer le processus expérimental

Les principales étapes du pipeline sont :

```bash
# Extraction des alertes
python3 extractor.py

# Extraction des motifs séquentiels
python3 train_patterns.py

# Filtrage des motifs
python3 filter_patterns.py

# Entraînement du modèle HMM
python3 train_hmm.py

# Calcul du seuil de décision
python3 calcul_seuil.py

# Lancement du système de détection
python3 src/main.py
```

*L'exécution nécessite les données et les fichiers intermédiaires attendus par chaque module.*

## 📊 Données et expérimentation

L'approche expérimentale s'appuie sur plusieurs sources de données :

- **Mordor (OTRF)** : scénarios et séquences d'attaque issus de jeux de données publics.
- **Données synthétiques** : augmentation du corpus expérimental.
- **Scénarios MITRE ATT&CK** : séquences construites à partir de techniques et de relations d'attaque documentées.
- **Alertes Wazuh** : données issues de l'environnement expérimental.

Les données réelles de l'environnement de supervision ne sont pas publiées lorsqu'elles contiennent des informations sensibles.

## 💡 Ce qui rend cette approche intéressante

- **Détection séquentielle :** considérer les attaques comme des enchaînements de comportements plutôt que comme des alertes indépendantes.
- **Extraction automatique :** découvrir des motifs sans devoir définir manuellement toutes les chaînes d'attaque.
- **Généralisation probabiliste :** explorer la reconnaissance de variantes de séquences apprises.
- **Explicabilité :** accompagner les résultats d'une explication en français générée localement.
- **Intégration SIEM :** enrichir les alertes Wazuh avec les informations issues de l'analyse séquentielle.

## 🔭 Perspectives d'évolution

Ce travail ouvre plusieurs pistes :
- Amélioration de la généralisation sur des scénarios d'attaque inconnus.
- Évaluation sur des corpus plus diversifiés.
- Optimisation des seuils de décision.
- Amélioration de l'explicabilité des détections.
- Extension des mécanismes d'intégration avec les plateformes SIEM.

## 📚 Références scientifiques et techniques

- [MITRE ATT&CK](https://attack.mitre.org/)
- [OTRF – Security Datasets (Mordor)](https://github.com/OTRF/Security-Datasets)
- [Wazuh – Documentation officielle](https://documentation.wazuh.com/)
- [PrefixSpan – Pei et al. (2001)](https://doi.org/10.1109/ICDE.2001.914830)
- [Ollama](https://ollama.com/)

---

## 👩🏽‍💻 À propos du projet

Ce projet s'inscrit dans le cadre d'un travail de recherche de fin d'études consacré à l'amélioration de la détection des chaînes d'attaque dans les systèmes SIEM.

**Auteur :** Loveline Yemeli  
**Domaine :** Cybersécurité | Détection d'intrusion | Intelligence artificielle appliquée à la sécurité  
**Année :** 2026

---

<p align="center">
  **La cybersécurité ne consiste pas seulement à détecter les événements, mais à comprendre ce qu'ils racontent.**
</p>

<p align="center">
  ⭐ Si cette approche vous intéresse, explorez le dépôt, examinez les algorithmes et découvrez comment les séquences d'attaque peuvent enrichir la détection SIEM.
</p>
