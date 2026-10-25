# Historique d'implémentation — FactCheck Mada

> **Dernière mise à jour : 25 octobre 2026** — version 1.0 du backend, avec
> documentation OpenAPI/Swagger.

Ce document retrace les étapes réalisées, les décisions techniques et les
vérifications effectuées sur le backend. Il complète le guide pratique
[GUIDE_ETAPES.md](GUIDE_ETAPES.md), qui détaille les commandes et les erreurs
fréquentes.

> **Principe produit** : l'application ne prononce jamais de verdict de vérité.
> Elle fournit des indices, une chronologie, des alertes et une aide à la
> décision. La décision finale reste humaine.

---

## 1. Cadrage et environnement

### Réalisé

- Création du projet Django `config` et de l'application `investigation`.
- Environnement Python local `env/` et fichier `requirements.txt` épinglé.
- Configuration de SQLite pour le MVP, avec variables permettant de basculer
  vers PostgreSQL.
- Configuration du français (`fr-fr`), du fuseau `Indian/Antananarivo` et de
  l'utilisation des dates avec fuseau (`USE_TZ=True`).
- Configuration de `python-dotenv`, des fichiers `.env` et `.env.example`.

### Décision

Le projet reste simple à lancer en local tout en isolant la configuration
sensible dans `.env`. Un garde-fou empêche le démarrage en production si la clé
secrète de développement est conservée.

---

## 2. Modèles métier et authentification

### Réalisé

- Modèle utilisateur personnalisé `Journaliste(AbstractUser)` avec :
  - `role` : journaliste, rédacteur en chef, administrateur ;
  - `redaction` ;
  - e-mail unique et obligatoire.
- `AUTH_USER_MODEL = "investigation.Journaliste"` défini avant la première
  migration.
- Modèles `Rumeur`, `PublicationSource`, `LienPropagation`, `AlerteCompte`,
  `AlerteTexte` et `RapportVerification`.
- Champs, relations, index, contraintes d'intégrité et tri en français.
- Suppression automatique des captures et des exports PDF/PNG lorsque les
  objets correspondants sont supprimés.
- Authentification JWT avec les claims `role` et `redaction`.
- Inscription publique, connexion, rafraîchissement et profil.
- Isolation des données par journaliste ; les administrateurs et membres du
  staff voient l'ensemble des données.
- Administration Django complète pour toutes les tables métier.

### Décisions

- Un rapport unique par rumeur (`OneToOneField`).
- Une publication enfant ne peut avoir qu'un seul parent.
- Les liens de propagation sont orientés de la publication la plus ancienne
  vers la plus récente, ce qui empêche les cycles.
- Les alertes automatiques sont régénérées de manière idempotente ; les alertes
  manuelles de type `autre` sont conservées.

---

## 3. Détection de doublons et similarité

### Réalisé

- Normalisation des textes : Unicode, accents, ligatures, casse, ponctuation,
  emojis et espaces.
- Empreinte SHA-256 pour la détection exacte.
- Similarité TF-IDF sur n-grammes de caractères (3 et 4), combinée à un
  recouvrement de n-grammes :
  `score = 0,5 × cosinus + 0,5 × recouvrement`.
- Seuil de doublon de rumeur : `0,90`.
- Seuil de lien de propagation : `0,80`.
- Création d'une rumeur :
  - `201` avec `cree: true` si elle est nouvelle ;
  - `200` avec `cree: false` et la rumeur existante si un doublon est détecté.
- Les rumeurs proches sous le seuil sont retournées dans `similaires` sans
  bloquer la création.

### Décision

L'implémentation reste en Python pur, sans scikit-learn, pour limiter les
dépendances et rendre les scores explicables.

---

## 4. Publications, propagation et analyses

### Réalisé

- Saisie manuelle des publications publiques : plateforme, auteur, URL, date,
  audience, texte brut et capture d'écran.
- Validation des dates, des URL, de la taille des images et du contenu réel des
  images avec Pillow.
- Détection de la première publication (« Source Zéro »), avec départage par
  identifiant en cas d'égalité de date.
- Création de liens de propagation chronologiques et mise à jour du meilleur
  parent lorsque plusieurs correspondances existent.
- Arbre JSON destiné à React : nœuds, liens, première publication et
  statistiques de diffusion.
- Analyse des comptes : compte récent, faible audience, nom trompeur, profil
  anonyme.
- Analyse des textes : langage alarmiste, appel au partage, absence de source,
  promesse financière, urgence artificielle et contenu sensible, avec lexiques
  français et malagasy.
- Scores de risque explicables et alertes idempotentes.

### Corrections apportées

- Validation réelle des fichiers image avec Pillow en plus de l'extension et du
  Content-Type.
- Suppression de doublons dans les lexiques.
- Ajout d'une contrainte d'unicité sur la publication enfant pour garantir un
  seul parent au niveau de la base.
- Neutralisation des titres de démonstration afin de ne pas préjuger de la
  véracité d'une information.

---

## 5. Rapports, exports et tableau de bord

### Réalisé

- Score de crédibilité de 0 à 100 avec pénalités documentées.
- Niveaux de risque : faible, moyen, élevé, très élevé.
- Résumé neutre et recommandations éditoriales.
- Export PDF avec ReportLab, avec police DejaVu et repli Helvetica.
- Export image PNG 1080 × 1080 avec Pillow.
- Routes séparées pour générer, consulter et télécharger le rapport.
- Tableau de bord agrégé et isolé selon le périmètre du journaliste.
- Dégradation contrôlée en `501` si ReportLab ou Pillow est absent.

### Décision

Le rapport ne conclut jamais à la véracité. Il contient un avertissement
explicite et présente les limites de l'analyse automatique.

---

## 6. Qualité, seed et documentation

### Réalisé

- 41 tests automatisés couvrant :
  - la normalisation et la similarité ;
  - l'inscription, la connexion et le rafraîchissement JWT ;
  - l'isolation par journaliste ;
  - les doublons ;
  - la propagation et les contraintes de liens ;
  - l'idempotence des alertes ;
  - les uploads d'images ;
  - les rapports, PDF/PNG et le tableau de bord ;
  - l'administration et la commande de démonstration.
- Commande `seed_donnees_demo` idempotente, avec option
  `--reinitialiser`.
- Jeu de démonstration : 3 rumeurs, 7 publications, 3 liens et 2 rapports.
- Documentation `README.md`, `docs/API.md`, `docs/SCENARIO_TEST.md` et
  collection Postman.
- Guide des cinq étapes avec commandes et erreurs fréquentes.

### Comptes de démonstration

| Identifiant | Mot de passe | Rôle |
|---|---|---|
| `demo` | `Demo1234!` | journaliste |
| `redaction` | `Demo1234!` | rédacteur en chef |

---

## 7. Documentation OpenAPI et Swagger

### Réalisé

- Installation de `drf-spectacular`.
- Génération du schéma OpenAPI 3 :
  - `/api/schema/` ;
  - `/api/docs/` pour Swagger UI ;
  - `/api/redoc/` pour Redoc.
- Ajout du bouton **Authorize** pour les jetons JWT.
- Documentation des routes personnalisées avec `@extend_schema` :
  - réponses d'inscription et de connexion ;
  - doublons de rumeur avec réponses `200` et `201` ;
  - upload multipart des captures d'écran ;
  - arbre de propagation ;
  - analyses et rapports ;
  - exports PDF/PNG binaires ;
  - tableau de bord.
- Paramètres de filtrage de la liste des rumeurs documentés.
- Variable `DOCUMENTATION_ACTIVE` pour désactiver la documentation en
  production.
- Tests de disponibilité du schéma et de Swagger UI.

### Vérification du schéma

```bash
python manage.py spectacular --file /tmp/factcheck-openapi.yaml --validate
```

Le schéma est généré sans erreur ni avertissement.

---

## 8. Vérifications finales

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test investigation -v 2
pip check
```

Résultats attendus :

- aucun problème de configuration Django ;
- aucune migration manquante ;
- suite de tests entièrement verte ;
- aucune dépendance cassée ;
- schéma OpenAPI valide.

Un scénario manuel a également validé :

- la connexion JWT ;
- la liste et la création de rumeurs ;
- la détection de Source Zéro ;
- l'arbre de propagation ;
- le rapport et ses exports PDF/PNG ;
- les réponses `401`, `404` et `400` ;
- le préflight CORS depuis React ;
- le refus d'un faux fichier image.

---

## 9. Limites connues

- Aucun scraping ni connexion non autorisée aux réseaux sociaux.
- Les publications sont saisies manuellement dans le MVP.
- Pas encore de frontend React livré avec ce backend.
- Les médias sont servis publiquement en mode `DEBUG` ; en production, utiliser
  un stockage privé ou des URLs signées.
- Les intégrations Facebook, TikTok et WhatsApp restent des points d'extension.
- PostgreSQL nécessite l'installation de `requirements-postgresql.txt`.

---

## 10. Suites possibles

1. Construire l'interface React et brancher tous les endpoints.
2. Déployer avec PostgreSQL, Gunicorn/Nginx, HTTPS et stockage privé.
3. Ajouter la collaboration, l'historique des modifications et les
   notifications.
4. Intégrer progressivement des API officielles, avec autorisation et
   conformité juridique.
