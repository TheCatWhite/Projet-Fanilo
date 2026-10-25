# Guide des cinq étapes

Ce document décrit l'implémentation réalisée, les fichiers concernés, les
commandes de vérification et les erreurs fréquentes. Le code complet se trouve
dans le dépôt ; chaque section pointe vers les fichiers à lire.

---

## Étape 1 — Socle Django, configuration et santé

### Objectif

Disposer d'un projet Django/DRF configuré pour le JWT, le CORS, les médias, le
français et le fuseau de Madagascar, avec un endpoint de santé.

### Fichiers

- `config/settings.py` : applications, base de données, JWT, CORS, DRF,
  pagination française, médias, i18n.
- `config/urls.py` : `admin/`, `api/`, médias en développement.
- `investigation/urls.py` : routes françaises.
- `investigation/views.py` : `SanteAPIView`.
- `investigation/pagination.py` : `total`, `suivant`, `precedent`, `resultats`.
- `investigation/gestion_erreurs.py` : traduction des erreurs.
- `.env.example`, `requirements.txt`, `.gitignore`.

### Commandes

```bash
source env/bin/activate
pip install -r requirements.txt
python manage.py check
python manage.py runserver
```

### Vérification

```bash
curl http://localhost:8000/api/sante/
# {"statut":"ok","service":"API FactCheck Mada"}
```

Contrôler aussi le préflight CORS :

```bash
curl -i -X OPTIONS http://localhost:8000/api/rumeurs/ \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: POST"
```

La réponse doit contenir `access-control-allow-origin: http://localhost:5173`.

### Erreurs fréquentes

| Erreur | Cause | Solution |
|---|---|---|
| `No module named django` | environnement non activé | `source env/bin/activate` |
| CORS absent | origine non listée | ajouter l'URL React dans `ORIGINES_CORS` |
| Mauvais fuseau | `TIME_ZONE` modifié | conserver `Indian/Antananarivo` |
| Médias en 404 | `DEBUG=False` | servir `/media/` via le serveur web ou un stockage dédié |

---

## Étape 2 — Modèles français et authentification JWT

### Objectif

Modéliser les journalistes, rumeurs, publications, liens, alertes et rapports,
puis sécuriser l'API avec SimpleJWT.

### Fichiers

- `investigation/models.py` : 7 modèles, contraintes, nettoyage des médias.
- `investigation/serializers.py` : inscription, connexion, rafraîchissement,
  profil, validations françaises.
- `investigation/views.py` : routes `/authentification/...`.
- `investigation/admin.py` : administration complète.
- `investigation/migrations/0001_initial.py`.
- `investigation/tests.py` : classes `AuthentificationTests`, `AdminTests`.

### Commandes

```bash
python manage.py makemigrations investigation
python manage.py migrate
python manage.py createsuperuser
python manage.py test investigation.tests.AuthentificationTests -v 2
```

> `AUTH_USER_MODEL = "investigation.Journaliste"` doit être défini **avant** la
> première migration. Si la base a déjà été migrée avec le modèle par défaut,
> supprimer `db.sqlite3` et relancer `migrate` en développement.

### Vérification

```bash
curl -X POST http://localhost:8000/api/authentification/inscription/ \
  -H "Content-Type: application/json" \
  -d '{
    "nom_utilisateur":"demo2",
    "email":"demo2@factcheck.mg",
    "mot_de_passe":"MotDePasse123!",
    "confirmation_mot_de_passe":"MotDePasse123!",
    "redaction":"La Gazette"
  }'
```

Attendu : `201`, `jeton_acces`, `jeton_rafraichissement`, rôle `journaliste`.

```bash
curl -X POST http://localhost:8000/api/authentification/connexion/ \
  -H "Content-Type: application/json" \
  -d '{"nom_utilisateur":"demo2","mot_de_passe":"MotDePasse123!"}'
```

### Erreurs fréquentes

| Erreur | Cause | Solution |
|---|---|---|
| `no such table: investigation_journaliste` | migrations non appliquées | `python manage.py migrate` |
| `Cannot change AUTH_USER_MODEL` | base créée avant le modèle personnalisé | repartir d'une base neuve en développement |
| `401` sur toutes les routes | en-tête absent | `Authorization: Bearer <jeton_acces>` |
| Mot de passe refusé | trop proche du nom d'utilisateur | choisir un mot de passe distinct |
| `email already exists` | e-mail unique | utiliser une autre adresse |

---

## Étape 3 — Rumeurs, doublons et similarité

### Objectif

Créer et consulter des rumeurs, détecter les doublons sans bloquer les contenus
seulement proches, et isoler les données par journaliste.

### Fichiers

- `investigation/services/service_similarite.py` : normalisation, SHA-256,
  TF-IDF sur n-grammes, recouvrement, recherche.
- `investigation/views.py` : `RumeurListCreateView`, `RumeurDetailView`.
- `investigation/serializers.py` : `RumeurEcritureSerializer`,
  `RumeurModificationSerializer`, `RumeurListeSerializer`,
  `RumeurDetailSerializer`.
- `investigation/tests.py` : `ServiceSimilariteTests`, `RumeurAPITests`.

### Commandes

```bash
python manage.py test investigation.tests.ServiceSimilariteTests -v 2
python manage.py test investigation.tests.RumeurAPITests -v 2
```

### Vérification

```bash
TOKEN=... # jeton obtenu à l'étape 2
curl -X POST http://localhost:8000/api/rumeurs/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "titre":"Pénurie de carburant",
    "contenu":"Urgence : une pénurie de carburant toucherait Antananarivo.",
    "langue":"fr"
  }'
```

Attendu : `201` avec `"cree": true`. Relancer le même appel : `200` avec
`"cree": false`, le même identifiant et le message de doublon.

### Erreurs fréquentes

| Erreur | Cause | Solution |
|---|---|---|
| Doublon détecté à tort | seuil ou corpus trop large | vérifier `score_similarite`, ajuster le seuil dans le service |
| `404` sur une rumeur | rumeur d'un autre journaliste | utiliser le compte propriétaire ou un administrateur |
| `400` sur `date_debut` | format non ISO | utiliser `AAAA-MM-JJ` |
| `empreinte_contenu` vide | contenu non enregistré par `save()` | passer par l'API ou `Rumeur.objects.create` |

---

## Étape 4 — Publications, propagation et analyses

### Objectif

Saisir les publications publiques, identifier la source zéro, créer les liens
chronologiques et produire les alertes de compte et de texte.

### Fichiers

- `investigation/services/service_propagation.py` : première détection, liens,
  arbre, statistiques.
- `investigation/services/service_analyse_compte.py` : règles de compte.
- `investigation/services/service_analyse_texte.py` : lexiques et score de risque.
- `investigation/views.py` : publications, arbre, analyse compte, analyse texte.
- `investigation/tests.py` : `PropagationTests`.

### Commandes

```bash
python manage.py test investigation.tests.PropagationTests -v 2
```

### Vérification

```bash
# Ajouter une publication (texte obligatoire pour la propagation)
curl -X POST http://localhost:8000/api/rumeurs/1/publications/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "plateforme":"facebook",
    "nom_auteur":"Alerte Info Madagascar",
    "url_profil_auteur":"https://facebook.com/alerte.info",
    "date_creation_compte":"2026-10-15",
    "nombre_abonnes":80,
    "date_publication":"2026-10-23T08:30:00Z",
    "texte_brut":"Urgence : pénurie de carburant à Antananarivo."
  }'

curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/rumeurs/1/arbre-propagation/
```

Attendu : `publication.est_premiere_detection`, `liens_crees`,
`alertes_compte`, `analyse_texte.score_risque_texte`, puis un arbre avec
`premiere_publication_detectee`, `noeuds`, `liens` et
`statistiques_propagation`.

### Erreurs fréquentes

| Erreur | Cause | Solution |
|---|---|---|
| Aucun lien créé | textes trop différents ou vides | vérifier `texte_brut` et le score (seuil 0,80) |
| Mauvaise source zéro | dates de publication incorrectes | corriger les dates ; la première détection est recalculée |
| `400` sur la capture | fichier trop lourd ou non image | 5 Mo max, JPG/PNG/WEBP/GIF |
| `415 Unsupported Media Type` | multipart mal envoyé | utiliser `-F` avec curl ou `FormData` côté React |
| Alertes en double | analyse manuelle hors service | les endpoints suppriment puis recréent les alertes automatiques |

---

## Étape 5 — Rapport, exports, tableau de bord et démonstration

### Objectif

Calculer le score de crédibilité, générer une fiche de synthèse, produire les
exports PDF/PNG, alimenter le tableau de bord et fournir un jeu de démonstration.

### Fichiers

- `investigation/services/service_rapport.py` : score, niveau, résumé,
  recommandations, PDF, image.
- `investigation/views.py` : rapport, exports, tableau de bord.
- `investigation/management/commands/seed_donnees_demo.py`.
- `investigation/tests.py` : `RapportTests`, `SeedDemoTests`.
- `docs/collection_postman.json`, `docs/SCENARIO_TEST.md`.

### Commandes

```bash
python manage.py seed_donnees_demo
python manage.py test investigation.tests.RapportTests -v 2
python manage.py test investigation.tests.SeedDemoTests -v 2
```

### Vérification

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/rumeurs/1/generer-rapport/

curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/rumeurs/1/rapport/

curl -H "Authorization: Bearer $TOKEN" \
  -o rapport.pdf \
  http://localhost:8000/api/rumeurs/1/rapport/pdf/

curl -H "Authorization: Bearer $TOKEN" \
  -o rapport.png \
  http://localhost:8000/api/rumeurs/1/rapport/image/
```

Attendu : score entre 0 et 100, niveau cohérent, quatre recommandations de base,
PDF valide (`%PDF`) et PNG 1080 × 1080.

### Erreurs fréquentes

| Erreur | Cause | Solution |
|---|---|---|
| `501` export PDF | ReportLab absent | `pip install -r requirements.txt` |
| `501` export image | Pillow absent | `pip install -r requirements.txt` |
| PDF avec accents cassés | police système absente | le service utilise DejaVu puis Helvetica en repli |
| `404` sur le rapport | rapport non généré | appeler d'abord `generer-rapport` |
| Rapport dupliqué | OneToOne | `update_or_create` est utilisé ; appeler l'endpoint est idempotent |
| Données demo en double | seed relancé | utiliser `--reinitialiser` |

---

## Vérification finale

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test investigation -v 2
python manage.py seed_donnees_demo
```

Le scénario complet, de l'inscription aux exports, est détaillé dans
`docs/SCENARIO_TEST.md`. La collection Postman correspondante est dans
`docs/collection_postman.json`.
