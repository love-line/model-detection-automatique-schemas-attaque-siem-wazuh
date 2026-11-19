# Intégration avec Wazuh

## Présentation

Ce guide décrit la procédure d'intégration du système intelligent de détection des chaînes d'attaque avec **Wazuh SIEM**.

L'objectif est de permettre au système d'analyser les alertes générées par Wazuh, d'identifier des séquences correspondant à des schémas d'attaque connus et de réinjecter les résultats de l'analyse dans Wazuh sous forme d'alertes natives.

L'intégration repose sur trois mécanismes complémentaires :

- **PrefixSpan** : identification des motifs d'attaque appris.
- **Similarité de Jaccard** : détection des variantes présentant une similarité avec les motifs connus.
- **Modèle de Markov caché (HMM)** : évaluation probabiliste des séquences d'événements.

---

## 1. Prérequis

Avant de procéder à l'intégration, assurez-vous de disposer des éléments suivants :

| Composant | Description |
|---|---|
| Wazuh Manager | Installé et opérationnel |
| Wazuh Agent | Déployé sur la machine cible |
| Sysmon | Installé sur la machine Windows cible (recommandé) |
| inotify-tools | Nécessaire à la surveillance des fichiers d'alertes |

Installation de `inotify-tools` sur le serveur Wazuh :

```bash
sudo apt install inotify-tools
```

## 2. Architecture du mécanisme de détection

Le système applique trois niveaux d'analyse successifs afin d'identifier les comportements pouvant révéler une chaîne d'attaque.

### 2.1. Méthodes de détection

| Niveau | Méthode | Fonction | Description |
|---|---|---|---|
| 1 | Correspondance exacte | `check_prefixspan()` | Identifie une sous-séquence correspondant à un motif d'attaque appris. |
| 2 | Similarité partielle | `jaccard_similarity()` | Évalue la ressemblance entre une séquence observée et un motif connu. |
| 3 | Analyse probabiliste | `check_hmm()` | Évalue la probabilité qu'une séquence corresponde à une progression d'attaque connue. |

### 2.2. Correspondance avec les niveaux de gravité Wazuh

Chaque mécanisme de détection est associé à un niveau de gravité spécifique dans Wazuh.

| Type de détection | Niveau Wazuh | Interprétation |
|---|---:|---|
| Correspondance exacte PrefixSpan | **12 – Élevé** | Détection d'un motif d'attaque connu. |
| Similarité Jaccard élevée | **10 – Moyen** | Identification d'une variante potentielle d'un motif connu. |
| Score HMM supérieur au seuil | **8 – Faible** | Suspicion probabiliste nécessitant une investigation. |

Cette classification permet de distinguer les correspondances observées selon leur nature et leur niveau de confiance.

---

## 3. Surveillance des alertes Wazuh

Le système surveille automatiquement le fichier contenant les alertes générées par Wazuh Manager.

### 3.1. Démarrer la surveillance

Rendez le script exécutable :

```bash
chmod +x watch_detections.sh
```

Lancez ensuite la surveillance :

```bash
./watch_detections.sh
```

Par défaut, le script surveille le fichier :

```text
/var/ossec/logs/alerts/alerts.json
```

À chaque modification détectée, le processus effectue les opérations suivantes :

1. **Extraction des événements** : `extractor.py` récupère les informations nécessaires à l'analyse.
2. **Analyse des séquences** : `src/main.py` exécute les mécanismes de détection.
3. **Génération des résultats** : les détections sont enregistrées dans un fichier dédié.
4. **Transmission à Wazuh** : les résultats sont copiés vers le répertoire de surveillance du SIEM.

### 3.2. Personnaliser les chemins des fichiers

Il est possible de définir des chemins personnalisés à l'aide des variables d'environnement suivantes :

```bash
export WAZUH_ALERTS_FILE="/chemin/vers/alerts.json"
export DETECTIONS_LOG="/chemin/vers/detections_wazuh.log"

./watch_detections.sh
```

Ces paramètres permettent d'adapter la surveillance à différentes configurations de déploiement.

---

## 4. Réinjection des détections dans Wazuh

Après l'analyse des séquences, les résultats doivent être transmis à Wazuh afin qu'ils puissent être interprétés comme des événements de sécurité.

Cette étape repose sur un décodeur personnalisé et des règles locales.

### 4.1. Créer un décodeur personnalisé

Ouvrez le fichier suivant :

```bash
sudo nano /var/ossec/etc/decoders/local_decoder.xml
```

Ajoutez le décodeur :

```xml
<decoder name="detection_schema_attaque">
  <prematch>IA_DETECTION</prematch>
  <regex offset="after_prematch">TYPE=(\S+)</regex>
  <order>type_detection</order>
</decoder>
```

Ce décodeur permet à Wazuh d'identifier les événements provenant du système de détection et d'extraire leur type.

### 4.2. Définir les règles de détection

Les règles personnalisées permettent d'associer chaque type de détection à un niveau de gravité.

Ouvrez le fichier de règles locales :

```bash
sudo nano /var/ossec/etc/rules/local_rules.xml
```

Ajoutez le groupe de règles suivant :

```xml
<group name="detection_schema_attaque">
  <rule id="100100" level="12">
    <decoded_as>detection_schema_attaque</decoded_as>
    <field name="type_detection">correspondance_exacte_ordonnee</field>
    <description>Schéma d'attaque multi-étapes détecté (correspondance exacte)</description>
  </rule>

  <rule id="100101" level="10">
    <decoded_as>detection_schema_attaque</decoded_as>
    <field name="type_detection">correspondance_probabiliste</field>
    <description>Schéma d'attaque probable (score HMM)</description>
  </rule>

  <rule id="100102" level="8">
    <decoded_as>detection_schema_attaque</decoded_as>
    <field name="type_detection">correspondance_ensemble_sans_ordre</field>
    <description>Variante de schéma d'attaque (similarité partielle)</description>
  </rule>
</group>
```

### 4.3. Configurer la surveillance du fichier de détections

Pour permettre à Wazuh de lire les résultats produits par le système, ajoutez la configuration suivante dans :

```text
/var/ossec/etc/ossec.conf
```

Configuration à intégrer :

```xml
<localfile>
  <log_format>json</log_format>
  <location>/var/ossec/logs/detections_wazuh.log</location>
</localfile>
```

Cette configuration indique à Wazuh le fichier contenant les résultats à surveiller.

### 4.4. Redémarrer Wazuh Manager

Une fois les modifications effectuées, redémarrez le service :

```bash
sudo systemctl restart wazuh-manager
```

---

## 5. Format des données de détection

Les résultats générés par le système sont enregistrés dans `detections_wazuh.log`.

Chaque événement doit être représenté par un objet JSON indépendant, enregistré sur une ligne distincte.

### Exemple de sortie

```json
{
  "schema_attaque": true,
  "niveau_detection": "prefixspan_exact",
  "pattern": [
    "T1587",
    "T1608",
    "T1204",
    "T1082",
    "T1033",
    "T1003"
  ],
  "score_hmm": -2.34,
  "jaccard": 0.85,
  "timestamp": "2026-11-19T10:00:00"
}
```

### Description des champs

| Champ | Description |
|---|---|
| `schema_attaque` | Indique si un schéma d'attaque a été identifié. |
| `niveau_detection` | Identifie le mécanisme de détection ayant produit le résultat. |
| `pattern` | Contient la séquence de techniques MITRE ATT&CK identifiée. |
| `score_hmm` | Représente le score calculé par le modèle HMM. |
| `jaccard` | Indique le niveau de similarité entre les séquences. |
| `timestamp` | Date et heure de la détection. |

Le champ `niveau_detection` permet notamment de distinguer les résultats selon leur mécanisme de détection.

---

## 6. Vérification de l'intégration

Après le redémarrage de Wazuh Manager, vérifiez que les événements générés par le système sont correctement pris en charge.

Les résultats attendus sont :

- La réception des événements issus du système de détection.
- Leur interprétation par les décodeurs personnalisés.
- L'application des règles correspondant aux différents mécanismes de détection.
- L'apparition des alertes dans le tableau de bord Wazuh.

Les alertes doivent être classées selon les trois niveaux de gravité configurés : **8, 10 et 12**.

---

## 7. Dépannage

Voici quelques problèmes susceptibles de survenir lors de l'intégration, ainsi que les premières vérifications à effectuer.

| Problème rencontré | Solution proposée |
|---|---|
| `inotifywait: command not found` | Installer `inotify-tools` avec `sudo apt install inotify-tools`. |
| Permission refusée sur `alerts.json` | Vérifier les droits d'accès au fichier et l'appartenance au groupe `wazuh`. |
| Détections absentes du dashboard | Vérifier la configuration de `ossec.conf`, les décodeurs et les règles, puis redémarrer Wazuh Manager. |
| Toutes les détections apparaissent au niveau 12 | Vérifier la correspondance entre les valeurs de détection produites et les règles Wazuh configurées. |

---

## Conclusion

L'intégration avec Wazuh permet d'étendre les capacités classiques de surveillance du SIEM en lui ajoutant un mécanisme d'identification des chaînes d'attaque.

En combinant **PrefixSpan, la similarité de Jaccard et les modèles de Markov cachés (HMM)**, le système ne se limite plus à l'analyse isolée des alertes : il cherche également à reconnaître des enchaînements d'événements caractéristiques de comportements offensifs.

Les résultats sont ensuite réinjectés dans Wazuh afin de centraliser leur visualisation et leur investigation au sein d'une même interface de supervision de la sécurité.
