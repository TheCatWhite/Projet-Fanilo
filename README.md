# FactCheck Mada — Application full-stack

Plateforme d'investigation pour journalistes malgaches. Elle aide à retrouver la
première occurrence publique d'une rumeur (« Source Zéro »), à documenter sa
propagation sur Facebook, Messenger, WhatsApp, TikTok, YouTube et le web, puis à
produire une fiche de vérification pour la salle de rédaction.

Le dépôt est organisé en deux applications côte à côte : le backend Django/DRF
dans `backend/` et le frontend Angular dans `factcheck-mada-front/`.

- Description détaillée et fonctionnement : [DESCRIPTION-PROJET.md](DESCRIPTION-PROJET.md)
- Argumentaire et perspectives d'évolution : [PITCH-ET-PERSPECTIVES.md](PITCH-ET-PERSPECTIVES.md)

> **Principe fondamental** : l'application ne dit jamais si une information est
> vraie ou fausse. Elle fournit des indices, une traçabilité, des alertes et une
> aide à la décision. La décision finale appartient au journaliste.

---

## 1. Fonctionnalités

- Authentification JWT (inscription, connexion, rafraîchissement, profil).
- CRUD des rumeurs, avec détection de doublons par empreinte SHA-256 et similarité.
- Saisie manuelle des publications sources (URLs, captures d'écran, métadonnées publiques).
- Détection de la première publication, liens de propagation et arbre JSON pour React.
- Alertes de compte : compte récent, faible audience, nom trompeur, profil anonyme.
- Alertes de texte : langage alarmiste, appel au partage, absence de source, promesse
  financière, urgence artificielle, contenu sensible (français et malagasy).
- Rapport de vérification : score de crédibilité, niveau de risque, résumé neutre,
  recommandations, export PDF et image PNG.
- Tableau de bord agrégé.
- Aucun scraping : seules les données publiques saisies par le journaliste sont utilisées.
- Frontend Angular responsive, en français, avec navigation protégée, formulaires
  réactifs, timeline CSS, téléchargements PDF/PNG authentifiés et tests unitaires
  et end-to-end.

---

## 2. Stack et architecture

- Python 3.12, Django 5.2, Django REST Framework 3.16.
- SimpleJWT, django-cors-headers, drf-spectacular, Pillow, ReportLab,
  python-dotenv.
- Angular 21.2.25, TypeScript strict, SCSS, RxJS, Reactive Forms, Vitest et
  Playwright.
- SQLite pour le MVP, PostgreSQL préparé par variables d'environnement.

```text
backend/                 API Django/DRF
  manage.py
  config/                configuration (settings, urls, wsgi/asgi)
  investigation/
    models.py            modèles métier en français
    serializers.py       validation et sérialisation
    schemas.py           schémas de réponse pour OpenAPI
    views.py             endpoints (vues minces) et annotations Swagger
    urls.py              routes françaises
    admin.py             administration complète
    permissions.py       contrôle d'accès
    pagination.py        pagination aux clés françaises
    gestion_erreurs.py   messages d'erreur français
    services/
      service_similarite.py
      service_propagation.py
      service_analyse_compte.py
      service_analyse_texte.py
      service_rapport.py
      integrations/      stubs d'API officielles (non actifs)
    management/commands/seed_donnees_demo.py
    tests.py             tests automatisés
  db.sqlite3             base de développement
  media/                 captures, PDF et images générés
factcheck-mada-front/    frontend Angular (sources, tests unitaires et e2e)
docs/                    documentation API, historique, scénario, Postman
env/                     environnement virtuel Python (non versionné)
DESCRIPTION-PROJET.md    description fonctionnelle et technique
PITCH-ET-PERSPECTIVES.md argumentaire et feuille de route
```

Les vues ne contiennent pas de logique métier : elles délèguent aux services,
ce qui facilite les tests et l'évolution du produit.

---

## 3. Installation

### Backend Django

```bash
cd /home/catwhite/Bureau/Fanilo
python3 -m venv env                  # déjà présent dans ce dépôt
source env/bin/activate
pip install -r backend/requirements.txt

cd backend
cp .env.example .env
# Modifier au minimum CLE_SECRETE dans .env
```

Le fichier `backend/.env` est ignoré par Git. Les chemins de la base, de `media/`
et du `.env` sont relatifs au dossier `backend/` : il faut donc lancer toutes les
commandes Django depuis ce dossier.

### Frontend Angular

```bash
cd /home/catwhite/Bureau/Fanilo/factcheck-mada-front
npm install
npm start
```

Le frontend est servi sur [http://localhost:5173](http://localhost:5173). Voir
[factcheck-mada-front/README.md](factcheck-mada-front/README.md) pour le détail
des cinq étapes, l'arborescence et les tests.

### Base de données et compte administrateur

```bash
cd backend
../env/bin/python manage.py migrate
../env/bin/python manage.py createsuperuser
../env/bin/python manage.py seed_donnees_demo
../env/bin/python manage.py runserver
```

Ou, plus simplement, avec les scripts fournis à la racine :

```bash
./demarrer-backend.sh      # http://localhost:8000/api/
./demarrer-front.sh        # http://localhost:5173
```

Comptes créés par le jeu de démonstration :

| Identifiant | Mot de passe | Rôle |
|---|---|---|
| `demo` | `Demo1234!` | journaliste |
| `redaction` | `Demo1234!` | rédacteur en chef |

> Ces identifiants sont réservés à la démonstration locale. Ne pas les utiliser
> en production.

`seed_donnees_demo` est idempotente. Pour recréer les données :

```bash
cd backend
../env/bin/python manage.py seed_donnees_demo --reinitialiser
```

---

## 4. Configuration

Variables principales (`.env`) :

| Variable | Défaut | Description |
|---|---|---|
| `CLE_SECRETE` | clé de dev | Clé secrète Django |
| `MODE_DEBUG` | `True` | Mode debug |
| `HOTES_AUTORISES` | `localhost,127.0.0.1` | Hôtes autorisés |
| `ORIGINES_CORS` | `http://localhost:3000,http://localhost:5173` | Origines du frontend |
| `DOCUMENTATION_ACTIVE` | `True` | Expose Swagger/Redoc et le schéma OpenAPI |
| `BASE_DONNEES_MOTEUR` | `sqlite3` | `sqlite3` ou `postgresql` |
| `BASE_DONNEES_NOM` | `db.sqlite3` | Nom de la base |
| `BASE_DONNEES_UTILISATEUR` / `_MOT_DE_PASSE` / `_HOTE` / `_PORT` | — | Connexion PostgreSQL |
| `DUREE_JETON_ACCES_MINUTES` | `60` | Durée de l'access token |
| `DUREE_JETON_RAFRAICHISSEMENT_JOURS` | `7` | Durée du refresh token |

Passage à PostgreSQL :

```env
BASE_DONNEES_MOTEUR=postgresql
BASE_DONNEES_NOM=factcheck_mada
BASE_DONNEES_UTILISATEUR=factcheck
BASE_DONNEES_MOT_DE_PASSE=motdepasse
BASE_DONNEES_HOTE=localhost
BASE_DONNEES_PORT=5432
```

Puis installez le pilote PostgreSQL et appliquez les migrations :

```bash
cd backend
../env/bin/pip install -r requirements-postgresql.txt
../env/bin/python manage.py migrate
```

Le code métier ne change pas.

---

## 5. Endpoints

Toutes les routes sont préfixées par `/api/`. Sauf mention contraire, elles
exigent l'en-tête `Authorization: Bearer <jeton_acces>`.

| Méthode | Route | Description |
|---|---|---|
| GET | `/sante/` | Santé publique de l'API |
| GET | `/schema/` | Schéma OpenAPI 3 (public) |
| GET | `/docs/` | Swagger UI (public) |
| GET | `/redoc/` | Documentation Redoc (public) |
| POST | `/authentification/inscription/` | Créer un compte journaliste |
| POST | `/authentification/connexion/` | Obtenir les jetons |
| POST | `/authentification/rafraichir-token/` | Renouveler l'access token |
| GET | `/authentification/profil/` | Profil connecté |
| GET/POST | `/rumeurs/` | Lister / créer une rumeur |
| GET/PATCH/DELETE | `/rumeurs/{id}/` | Détail / modifier / supprimer |
| GET/POST | `/rumeurs/{id}/publications/` | Lister / ajouter une publication |
| GET | `/rumeurs/{id}/arbre-propagation/` | Arbre JSON pour la timeline Angular |
| POST | `/publications/{id}/analyser-compte/` | Relancer l'analyse du compte |
| POST | `/rumeurs/{id}/analyser-texte/` | Relancer l'analyse du texte |
| POST | `/rumeurs/{id}/generer-rapport/` | Générer / mettre à jour le rapport |
| GET | `/rumeurs/{id}/rapport/` | Consulter le rapport |
| GET | `/rumeurs/{id}/rapport/pdf/` | Télécharger le PDF |
| GET | `/rumeurs/{id}/rapport/image/` | Télécharger l'image PNG |
| GET | `/tableau-de-bord/statistiques/` | Statistiques agrégées |

- Documentation interactive : [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
- Documentation détaillée : [docs/API.md](docs/API.md)
- Guide des cinq étapes backend : [docs/GUIDE_ETAPES.md](docs/GUIDE_ETAPES.md)
- Guide du frontend : [factcheck-mada-front/README.md](factcheck-mada-front/README.md)
- Historique d'implémentation : [docs/HISTORIQUE.md](docs/HISTORIQUE.md)
- Scénario complet : [docs/SCENARIO_TEST.md](docs/SCENARIO_TEST.md)
- Collection Postman : [docs/collection_postman.json](docs/collection_postman.json)

### Tester avec Swagger

1. Lancer le serveur : `cd backend && ../env/bin/python manage.py runserver`.
2. Ouvrir `http://localhost:8000/api/docs/`.
3. Appeler `POST /api/authentification/connexion/` avec `demo` / `Demo1234!`.
4. Cliquer sur **Authorize** et coller le `jeton_acces`.
5. Tester les routes protégées, y compris l'upload multipart d'une capture.

La documentation est désactivable avec `DOCUMENTATION_ACTIVE=False`, notamment
en production.

---

## 6. Détection de similarité

Méthode retenue : **TF-IDF sur n-grammes de caractères (3 et 4) + recouvrement**,
implémentée en Python pur (aucune dépendance lourde).

1. Normalisation : Unicode, suppression des accents, minuscules, suppression des
   emojis et de la ponctuation, compactage des espaces.
2. Empreinte SHA-256 du texte normalisé (recherche exacte immédiate).
3. Score = `0,5 × cosinus(TF-IDF) + 0,5 × recouvrement des n-grammes`.
4. Seuils : **0,90** pour considérer une rumeur comme doublon, **0,80** pour créer
   un lien de propagation.

Cette combinaison détecte les copier-coller et les versions raccourcies ou
légèrement réécrites, fréquentes sur WhatsApp et TikTok. Les scores sont exposés
dans les réponses pour rester explicables.

---

## 7. Scores et alertes

### Score de risque texte (0–100)

| Signal | Points | Plafond |
|---|---|---|
| Langage alarmiste | 8 / expression | 25 |
| Appel au partage | 10 / expression | 20 |
| Absence de source | 20 | 20 |
| Promesse financière | 10 / expression | 25 |
| Urgence artificielle | 7 / expression | 15 |
| Contenu sensible | 7 / expression | 20 |

### Score de crédibilité (0–100)

Départ à 100, puis pénalités : alertes texte (max −45), alertes compte (max −30),
absence de source (−8), aucune publication (−15), compte source récent (−5),
propagation rapide (−5). Le score est borné entre 0 et 100.

| Score | Niveau de risque |
|---|---|
| 80–100 | faible |
| 60–79 | moyen |
| 40–59 | élevé |
| 0–39 | très élevé |

Toutes les formules sont visibles dans `investigation/services/` et couvertes par
les tests.

---

## 8. Tests

```bash
cd backend
../env/bin/python manage.py check
../env/bin/python manage.py makemigrations --check --dry-run
../env/bin/python manage.py test investigation -v 2
../env/bin/python manage.py spectacular --file /tmp/factcheck-openapi.yaml --validate
```

Un script regroupe toutes les vérifications :

```bash
./verifier-tout.sh
```

Les tests couvrent : normalisation et similarité, inscription/connexion/JWT,
isolation entre journalistes, doublons, filtres, propagation, première détection,
alertes compte et texte, upload d'image, rapport, exports PDF/PNG, tableau de bord,
administration, commande de démonstration et disponibilité de Swagger/OpenAPI.

Frontend :

```bash
cd factcheck-mada-front
npm run build
npm test -- --watch=false
npm run test:e2e        # backend et frontend lancés, Google Chrome disponible
```

Résultats de la dernière validation complète :

| Vérification | Résultat |
|---|---|
| `manage.py check` | 0 problème |
| Migrations | aucune modification détectée |
| Tests backend | **41 tests réussis** |
| `pip check` | aucune dépendance cassée |
| Schéma OpenAPI | valide |
| Build Angular | réussi |
| Tests unitaires frontend | **15 réussis** |
| Scénarios Playwright | **3 réussis** |

---

## 9. Sécurité et limites

- JWT uniquement sur l'API ; permission `IsAuthenticated` par défaut.
- Chaque journaliste ne voit que ses rumeurs ; les administrateurs voient tout.
- Inscription limitée au rôle `journaliste` (aucune escalade de privilèges).
- Uploads limités aux images de 5 Mo, noms de fichiers générés.
- CORS restreint aux deux origines React, throttling activé.
- Swagger/Redoc peuvent être désactivés avec `DOCUMENTATION_ACTIVE=False`.
- `SECRET_KEY`, `DEBUG`, base et CORS pilotés par `.env`.
- En production, le démarrage est refusé si `CLE_SECRETE` conserve une valeur de
  développement.
- En production, servir `/media/` via un stockage privé ou des URLs signées : les
  captures et rapports peuvent contenir des données sensibles ; le MVP les sert
  publiquement uniquement en mode `DEBUG`.
- Aucun accès aux données privées WhatsApp/Messenger, aucun scraping.
- Les comptes et messages publics saisis restent soumis aux règles éditoriales et
  légales applicables (protection des données personnelles).
- La similarité est heuristique : elle doit être calibrée sur un corpus réel et ne
  remplace pas le jugement du journaliste.
- SQLite convient à la démonstration ; PostgreSQL est recommandé en production.

---

## 10. Licence et éthique

Projet de démonstration pour un hackathon. L'outil est une aide à l'investigation :
il ne produit jamais de verdict de vérité et doit être utilisé avec une vérification
humaine systématique.
