# Intégration d'Ollama – Module d'explication en langage naturel

## 1. Présentation

Le projet utilise **[Ollama](https://ollama.com/)** pour intégrer un modèle de langage local (LLM) chargé de produire des explications compréhensibles à partir des schémas d'attaque détectés.

Cette fonctionnalité est implémentée dans le module `src/explanation.py`.

Contrairement aux solutions reposant sur des API cloud, Ollama permet d'exécuter un modèle directement sur la machine hébergeant le projet. Les explications peuvent ainsi être générées localement, sans dépendre d'un service externe.

Dans l'architecture du système, Ollama intervient comme un composant complémentaire :

- **PrefixSpan** extrait les motifs séquentiels fréquents.
- **Le HMM** contribue à l'analyse et à la généralisation probabiliste des séquences.
- **Ollama** transforme les résultats de détection en explications rédigées en langage naturel.

L'objectif est de faciliter la compréhension des détections par un analyste, notamment en présentant les comportements observés et leur signification dans un langage accessible.

## 2. Prérequis

Avant de commencer, assurez-vous de disposer des éléments suivants :

- Une machine fonctionnant sous Debian ou une distribution Linux compatible.
- Un accès Internet pour installer Ollama et télécharger le modèle.
- Un espace disque suffisant pour stocker le modèle.
- Une mémoire RAM adaptée à l'exécution d'un modèle de 3 milliards de paramètres.

Le projet utilise par défaut le modèle `llama3.2:3b`, qui constitue un compromis entre taille, consommation de ressources et capacité de génération.

## 3. Installation d'Ollama

L'installation s'effectue directement depuis le terminal.

Téléchargez et exécutez le script officiel d'installation :

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Ce script installe Ollama et configure son service système lorsqu'il est pris en charge par l'environnement.

Vérifiez ensuite que le service fonctionne :

```bash
sudo systemctl status ollama
```

Si le service n'est pas actif, démarrez-le et activez son lancement automatique au démarrage de la machine :

```bash
sudo systemctl enable --now ollama
```

Pour vérifier la version installée :

```bash
ollama --version
```

## 4. Téléchargement du modèle Llama 3.2

Le système utilise par défaut le modèle **`llama3.2:3b`**.

Il s'agit d'un modèle relativement léger, adapté à une exécution locale, notamment sur une machine ne disposant pas nécessairement d'un GPU dédié.

Téléchargez-le avec la commande suivante :

```bash
ollama pull llama3.2:3b
```

Le téléchargement peut prendre quelques minutes selon la qualité de votre connexion Internet.

Une fois le téléchargement terminé, vérifiez que le modèle est disponible :

```bash
ollama list
```

Le modèle `llama3.2:3b` doit apparaître dans la liste.

Pour consulter les informations relatives au modèle :

```bash
ollama show llama3.2:3b
```

## 5. Vérification du fonctionnement d'Ollama

Ollama expose une API HTTP locale, accessible par défaut à l'adresse :

```text
http://localhost:11434
```

Cette API permet au projet de communiquer avec le modèle sans passer par une interface graphique.

### 5.1. Vérifier la disponibilité de l'API

Exécutez :

```bash
curl http://localhost:11434/api/tags
```

La réponse doit contenir les informations relatives aux modèles installés.

Vérifiez notamment que `llama3.2:3b` figure dans les résultats.

### 5.2. Effectuer un premier test de génération

Pour vérifier que le modèle est capable de produire une réponse, exécutez :

```bash
ollama run llama3.2:3b "Explique en une phrase ce qu'est une attaque par force brute."
```

Si le modèle retourne une explication cohérente, son installation et son fonctionnement de base sont corrects.

Vous pouvez quitter l'interface interactive d'Ollama avec `Ctrl + D`.

## 6. Configuration dans le projet

Le module `src/explanation.py` utilise l'API locale d'Ollama pour transmettre les informations issues du système de détection et obtenir une explication en langage naturel.

Les paramètres utilisés par défaut sont :

| Paramètre | Valeur par défaut | Description |
|---|---|---|
| `OLLAMA_URL` | `http://localhost:11434` | Adresse de l'API Ollama |
| `OLLAMA_MODEL` | `llama3.2:3b` | Modèle de langage utilisé |

### 6.1. Configuration dans `src/config.py`

Si le projet utilise ces constantes dans `src/config.py`, elles peuvent être définies de la manière suivante :

```python
import os

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "llama3.2:3b"
)
```

Cette configuration permet de modifier l'adresse du service ou le modèle sans avoir à réécrire les valeurs directement dans le code.

**Important :** les noms des variables et leur utilisation doivent correspondre à ceux effectivement attendus par `src/explanation.py`.

### 6.2. Modifier les paramètres temporairement

Il est également possible de définir les paramètres directement dans le terminal avant de lancer le projet :

```bash
export OLLAMA_URL="http://localhost:11434"
export OLLAMA_MODEL="llama3.2:3b"
```

Ces variables restent disponibles dans le terminal courant et les processus lancés depuis celui-ci.

## 7. Tester l'intégration avec le projet

Après avoir installé Ollama et téléchargé le modèle, vérifiez que les différents composants communiquent correctement.

Procédez dans cet ordre :

1. Vérifiez que le service Ollama est actif.
2. Vérifiez que le modèle `llama3.2:3b` est installé.
3. Vérifiez que l'API locale répond.
4. Lancez le projet selon sa procédure habituelle.
5. Déclenchez ou utilisez une détection disponible.
6. Vérifiez que le module `src/explanation.py` parvient à obtenir une réponse du modèle.

Le test réalisé avec `ollama run` valide le fonctionnement du modèle, mais ne suffit pas à prouver que le module Python communique correctement avec lui. La validation finale doit donc être effectuée à travers le projet.

## 8. Dépannage

Voici les problèmes les plus courants susceptibles de survenir lors de l'installation ou de l'utilisation d'Ollama.

| Problème rencontré | Cause probable | Solution |
|---|---|---|
| `Connection refused` sur le port `11434` | Le service Ollama n'est pas démarré. | Exécuter `sudo systemctl start ollama`. |
| `model not found` | Le modèle demandé n'est pas installé. | Exécuter `ollama pull llama3.2:3b`. |
| Réponse très lente | Le modèle est en cours de chargement ou les ressources matérielles sont limitées. | Attendre le chargement et vérifier l'utilisation du CPU et de la RAM. |
| Mémoire insuffisante | La machine ne dispose pas de suffisamment de RAM disponible. | Fermer les applications inutiles ou choisir un modèle plus léger compatible avec le projet. |
| L'API ne retourne aucun modèle | Aucun modèle n'a encore été téléchargé. | Vérifier avec `ollama list`, puis télécharger le modèle requis. |
| Le modèle répond dans le terminal, mais pas dans le projet | Problème de configuration ou de communication entre Python et l'API. | Vérifier `OLLAMA_URL`, `OLLAMA_MODEL` et les erreurs remontées par `src/explanation.py`. |

Pour consulter les journaux du service Ollama :

```bash
sudo journalctl -u ollama -f
```

Cette commande permet de suivre les événements du service en temps réel.

## 9. Considérations de sécurité et de confidentialité

L'utilisation d'Ollama en local présente plusieurs avantages pour un environnement de cybersécurité :

- Les requêtes peuvent être traitées localement, sans transmission obligatoire à une API cloud.
- Le fonctionnement du modèle ne dépend pas d'une connexion Internet permanente une fois le modèle téléchargé.
- Les paramètres du modèle peuvent être adaptés aux ressources disponibles sur la machine.

Par défaut, l'API Ollama écoute sur l'interface locale. Il est préférable de conserver cette configuration lorsque l'accès distant n'est pas nécessaire.

Évitez d'exposer directement le port `11434` sur un réseau non maîtrisé.

## 10. Résumé des commandes

Pour faciliter l'installation sur une nouvelle machine, voici les principales commandes à exécuter :

```bash
# Installer Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Démarrer et activer le service
sudo systemctl enable --now ollama

# Télécharger le modèle utilisé par le projet
ollama pull llama3.2:3b

# Vérifier les modèles installés
ollama list

# Tester l'API locale
curl http://localhost:11434/api/tags

# Tester la génération d'une explication
ollama run llama3.2:3b "Explique en une phrase ce qu'est une attaque par force brute."

# Consulter les journaux du service
sudo journalctl -u ollama -f
```

---

**En résumé :** Ollama fournit au projet une capacité d'explication locale fondée sur un modèle de langage. Il intervient en complément du moteur de détection afin de rendre les schémas d'attaque identifiés plus faciles à interpréter par un analyste.
