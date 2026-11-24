# RoomBooking — Première partie (10/20)

Un seul microservice Python : **Room Service**, une API REST de gestion des salles
avec FastAPI. Les salles sont stockées dans un dictionnaire en mémoire.

Cette étape comprend l'application, Docker et Kubernetes (Deployment + Service).
Le Booking Service, les réservations par créneau, la gateway, la base de données,
gRPC et le frontend seront ajoutés dans les étapes suivantes.

## Fichiers

```text
main.py                 Point d'entrée : création de l'application
models/room.py          Modèles, validation et stockage des salles
controllers/room_controller.py  Routes HTTP et gestion des erreurs
views/room_view.py      Format des réponses JSON
requirements.txt        Dépendances de l'application
requirements-dev.txt    Dépendances pour les tests
Dockerfile              Construction de l'image
k8s/deployment.yaml     Exécution du conteneur dans Kubernetes
k8s/service.yaml        Accès au service sur le port 8000 (NodePort 30080)
tests/test_rooms.py      Tests de l'API
repo_prof/              Exemples du professeur, ignorés par Git et Docker
```

## Architecture MVC

- **Modèle** (`models/`) : définit une salle, valide ses données et gère les
  opérations de lecture, ajout, modification et suppression en mémoire.
- **Vue** (`views/`) : définit les champs renvoyés au client en JSON avec
  `RoomView`. FastAPI utilise cette vue via `response_model` pour produire les
  réponses. Pour cette API REST, la vue est une représentation JSON ; le
  frontend graphique reste une étape ultérieure.
- **Contrôleur** (`controllers/`) : reçoit les requêtes HTTP, appelle le modèle,
  choisit la vue et transforme une salle inexistante en réponse HTTP `404`.

Exemple : `GET /rooms/1` arrive dans le contrôleur, qui demande la salle au
modèle. FastAPI présente ensuite cette salle en JSON selon `RoomView`.
`main.py` assemble l'application et ses routes. Les fichiers `k8s/` restent
la configuration de déploiement, en dehors du MVC.

## 1. Lancer en Python

Prérequis : Python 3.14. Exécuter les commandes depuis la racine du projet.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Ouvrir http://localhost:8000/docs pour tester l'API avec les boutons
**Try it out**, puis **Execute**. La liste est accessible à
http://localhost:8000/rooms.

Trois salles sont présentes au démarrage : A101, B205 et C302.
`available` indique si une salle est utilisable (par exemple hors travaux),
pas sa disponibilité sur un créneau horaire.

| Méthode | URL | Fonction |
| --- | --- | --- |
| GET | `/health` | Vérifier que le service répond |
| GET | `/rooms` | Lister les salles |
| GET | `/rooms?min_capacity=20&available=true` | Filtrer les salles |
| GET | `/rooms/1` | Consulter une salle |
| POST | `/rooms` | Ajouter une salle |
| PUT | `/rooms/1` | Remplacer les informations d'une salle |
| DELETE | `/rooms/1` | Supprimer une salle |

Exemple d'ajout :

```bash
curl -X POST http://localhost:8000/rooms \
  -H 'Content-Type: application/json' \
  -d '{"name":"D104","capacity":12,"floor":1,"equipment":["Wi-Fi"],"available":true}'
```

L'identifiant est généré par le serveur. Pour modifier une salle, envoyer le même
format avec `PUT /rooms/4` (adapter l'identifiant à la réponse reçue).
`PUT` remplace les informations : fournir au minimum `name`, `capacity` et `floor`.
Les champs facultatifs omis reprennent leurs valeurs par défaut
(`equipment: []`, `available: true`).

Réponses : `201` pour un ajout, `204` pour une suppression, `404` si la salle
n'existe pas, `422` si les données sont invalides (nom vide, capacité ≤ 0, etc.).

## 2. Construire et lancer l'image Docker

Démarrer Docker Desktop, puis arrêter le serveur Python avec `Ctrl+C`
pour libérer le port 8000.

```bash
docker build -t sarusman/roombooking-room-service:1.0 .
docker run --rm --name room-service -p 127.0.0.1:8000:8000 sarusman/roombooking-room-service:1.0
```

Tester à nouveau http://localhost:8000/docs. `Ctrl+C` arrête le conteneur.
Le Dockerfile installe les dépendances, copie l'application et lance Uvicorn.

## 3. Publier sur Docker Hub

Le compte utilisé est `sarusman` et le dépôt est
[`sarusman/roombooking-room-service`](https://hub.docker.com/r/sarusman/roombooking-room-service).
Le dépôt doit être public pour que Kubernetes puisse télécharger l'image
sans configuration supplémentaire. La connexion se fait dans ton terminal.

```bash
docker login
docker push sarusman/roombooking-room-service:1.0
```

Vérifier que le tag `1.0` apparaît sur Docker Hub. L'image publiée depuis ce Mac
est pour `linux/arm64`. Pour une démonstration sur une autre architecture
(Mac ARM et PC Intel, par exemple), publier les deux :

```bash
docker buildx build --platform linux/amd64,linux/arm64 \
  -t sarusman/roombooking-room-service:1.0 --push .
```

## 4. Déployer dans Kubernetes avec Minikube

Prérequis : Docker Desktop démarré, Minikube et kubectl installés.
On utilise un cluster local dédié nommé `roombooking`.

### Essayer avec l'image locale

Après la construction Docker de l'étape 2 :

```bash
minikube start -p roombooking --driver=docker --cpus=2 --memory=2200
minikube -p roombooking image load sarusman/roombooking-room-service:1.0
kubectl --context=roombooking apply -f k8s/
kubectl --context=roombooking rollout status deployment/room-service --timeout=120s
kubectl --context=roombooking get deployments,pods,services
```

Le **Deployment** crée le Pod qui exécute l'application. Le **Service** retrouve
ce Pod grâce au label `app: room-service` et lui transmet les requêtes.

Pour accéder à l'application, y compris sur macOS avec Docker :

```bash
kubectl --context=roombooking port-forward service/room-service 8000:8000
```

Garder ce terminal ouvert, puis ouvrir http://localhost:8000/docs.
Le port 8000 doit être libre. Le NodePort peut aussi être exposé avec
`minikube -p roombooking service room-service --url` ; ouvrir l'URL retournée
suivie de `/docs` et conserver le terminal ouvert si Minikube crée un tunnel.

### Utiliser l'image publiée sur Docker Hub

Le fichier `k8s/deployment.yaml` référence déjà
`sarusman/roombooking-room-service:1.0`. Sur un cluster sans image locale,
la commande `image load` n'est pas nécessaire :

```bash
kubectl --context=roombooking apply -f k8s/
kubectl --context=roombooking rollout status deployment/room-service --timeout=120s
```

Kubernetes téléchargera cette image publique depuis Docker Hub si elle n'est
pas déjà présente dans le cluster (`imagePullPolicy: IfNotPresent`).
Si le Pod affiche `ImagePullBackOff`, vérifier le nom, le tag et la visibilité
du dépôt avec `kubectl --context=roombooking describe pods`.
Les logs sont disponibles avec
`kubectl --context=roombooking logs deployment/room-service`.

Pour arrêter la démonstration : `Ctrl+C` dans le terminal de port-forward,
puis `minikube stop -p roombooking`. Pour supprimer les ressources de l'application :
`kubectl --context=roombooking delete -f k8s/`.

## Tests

```bash
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

Les tests vérifient le cycle ajout/lecture/modification/suppression, les filtres,
les salles inexistantes et le rejet des données invalides.

Vérifications de la première version publiée (`1.0`), le 24 novembre 2026 :

- Les 7 tests automatisés passent.
- L'image Docker est construite et les opérations CRUD sont testées via HTTP.
- L'image `sarusman/roombooking-room-service:1.0` est publiée dans un dépôt public.
- Minikube télécharge cette image depuis Docker Hub ; le Pod est `1/1 Running`.
- Les opérations CRUD fonctionnent via le Service et le NodePort répond sur `/health`.

La réorganisation MVC est vérifiée séparément avec les 7 tests de l'API et
une construction Docker locale (`roombooking-room-service:mvc`). La version
MVC n'a pas encore été publiée sur Docker Hub ni redéployée dans Minikube.

## Limites de cette étape

Les modifications disparaissent au redémarrage du service ou du Pod.
Garder **un seul processus et un seul replica**, car la mémoire n'est pas
partagée entre instances. Il n'y a pas encore d'authentification : toutes les
routes sont accessibles pour la démonstration locale.

## Références du professeur

Les huit dépôts cités dans l'énoncé sont clonés dans `repo_prof/`.
Leurs README servent de références ; ces projets ne sont pas exécutés.

- [kubernetes-minikube](https://github.com/charroux/kubernetes-minikube) : référence principale pour Docker, Docker Hub, Deployment et Service NodePort.
- [gRPCSpring](https://github.com/charroux/gRPCSpring) : option gRPC pour une étape ultérieure.
- [servicemesh](https://github.com/charroux/servicemesh), [CodingWithKubernetes](https://github.com/charroux/CodingWithKubernetes), [servicemesh-kubernetes](https://github.com/charroux/servicemesh-kubernetes) : communication et routage entre plusieurs services.
- [rentalservice](https://github.com/charroux/rentalservice), [noops](https://github.com/charroux/noops), [kubernetes-volumes](https://github.com/charroux/kubernetes-volumes) : exemples pour la suite du projet.

L'API suit la [documentation FastAPI](https://fastapi.tiangolo.com/tutorial/body/)
et le conteneur son [guide Docker](https://fastapi.tiangolo.com/deployment/docker/).
