# FactCheck Mada — Description et fonctionnement

> **En une phrase** : une plateforme d'investigation qui aide une rédaction
> malgache à documenter la diffusion d'une rumeur, à retrouver sa première
> occurrence publique et à produire une fiche de vérification — sans jamais
> prononcer de verdict de vérité.

| Élément | Valeur |
|---|---|
| Nature | Application web full-stack (API + interface) |
| Domaine | Journalisme d'investigation, vérification de l'information (OSINT) |
| Langue de l'interface | Français |
| Backend | Django 5.2, Django REST Framework 3.16, SQLite / PostgreSQL |
| Frontend | Angular 21, TypeScript strict, SCSS |
| Authentification | JWT (SimpleJWT) |
| Déploiement actuel | Local : API `:8000`, interface `:5173` |
| État | MVP fonctionnel, testé (41 tests backend, 15 tests unitaires, 3 parcours E2E) |

---

## 1. Le problème

À Madagascar, une rumeur naît souvent sur WhatsApp, passe dans des groupes
Facebook, puis se retrouve reprise par des pages d'information et parfois par des
médias. Trois difficultés reviennent :

1. **Reconstituer la chronologie** : qui a publié quoi, quand, et où pour la
   première fois ? Les partages ne laissent pas de trace consultable.
2. **Documenter sans preuve** : les publications sont supprimées, les captures
   d'écran se perdent, les URL changent.
3. **Décider vite, sans outil** : la rédaction doit choisir entre ignorer la
   rumeur et la relayer imprudemment, souvent sans disposer d'un dossier
   structuré.

Les outils disponibles sont soit des réseaux sociaux (qui ne fournissent pas
d'historique exploitable), soit des détecteurs automatiques de « fake news » qui
produisent des verdicts non fiables et non défendables juridiquement.

## 2. La réponse : un outil de triage, pas un juge

FactCheck Mada ne dit jamais « c'est vrai » ou « c'est faux ». Il produit :

- une **chronologie documentée** des publications ;
- une **première occurrence** identifiée dans les données saisies ;
- des **signaux d'alerte** explicables (texte et compte) ;
- un **score de crédibilité** et un **niveau de risque** ;
- une **fiche de vérification** exportable en PDF et en image, destinée à la
  salle de rédaction.

La décision éditoriale reste entièrement humaine. Cette position n'est pas une
précaution de langage : c'est un choix de conception qui traverse les modèles, les
algorithmes, les textes de l'interface et les rapports.

## 3. Public visé

| Utilisateur | Usage principal |
|---|---|
| Journaliste | Documenter une rumeur, saisir les publications, préparer un fact-check |
| Rédacteur en chef | Arbitrer la publication à partir de la fiche de vérification |
| Administrateur | Superviser les comptes et l'ensemble des dossiers |
| Étudiant en journalisme | Apprendre une méthode de vérification traçable |

Chaque journaliste ne voit que ses propres dossiers ; les administrateurs voient
toutes les rédactions. L'inscription publique crée uniquement des comptes
« journaliste » en lecture seule sur les rôles : aucune escalade de privilèges
n'est possible depuis l'interface.

## 4. Le parcours réel, étape par étape

### Étape 1 — Créer le dossier

Le journaliste saisit un **titre**, le **contenu** de la rumeur et sa **langue**
(français, malagasy, anglais, autre). Le backend calcule immédiatement une
empreinte SHA-256 du texte normalisé.

Avant l'enregistrement, il recherche :

- un **doublon exact** par empreinte ;
- des **rumeurs similaires** par similarité textuelle.

Si une rumeur très proche existe déjà (score ≥ 0,90), la création renvoie un
succès `200` avec `cree: false` et le dossier existant : on évite les doublons
sans bloquer le journaliste.

### Étape 2 — Saisir les publications sources

Pour chaque trace publique, le journaliste renseigne :

- la plateforme (Facebook, Messenger, WhatsApp, TikTok, YouTube, site web, autre) ;
- l'URL de la publication et, si disponible, celle du profil ;
- le nom de l'auteur ;
- la date de publication ;
- la date de création du compte et le nombre d'abonnés, s'ils sont visibles ;
- le texte brut, et éventuellement une capture d'écran (JPEG/PNG, 5 Mo maximum).

À l'enregistrement, le backend :

1. analyse le **texte de la rumeur** et crée les alertes correspondantes ;
2. analyse le **compte** de la publication et crée ses alertes ;
3. recalcule la **première publication** de la rumeur ;
4. crée les **liens de propagation** avec les publications déjà saisies.

### Étape 3 — Lire les alertes

Deux familles d'alertes, toutes explicables et affichées avec leur gravité :

- **alertes de texte** : langage alarmiste, appel au partage, absence de source,
  promesse financière, urgence artificielle, contenu sensible ;
- **alertes de compte** : compte récent, faible audience, nom potentiellement
  trompeur, profil anonyme, comportement suspect.

Chaque alerte contient une **explication en français** et, pour le texte,
l'**expression détectée**. Rien n'est présenté comme une preuve.

### Étape 4 — Visualiser la propagation

L'écran de propagation affiche une **timeline CSS** (sans bibliothèque de
graphes) construite à partir de l'API :

- les publications, de la plus ancienne à la plus récente ;
- la **Source Zéro** mise en évidence ;
- les liens parent → enfant lorsque deux textes se ressemblent ;
- des statistiques : nombre de publications, plateformes, première et dernière
  date, durée, et une phrase décrivant la vitesse de diffusion.

### Étape 5 — Générer la fiche de vérification

Un clic calcule et enregistre :

- le **score de crédibilité** (0–100) ;
- le **niveau de risque** (faible, moyen, élevé, très élevé) ;
- un **résumé neutre** rédigé à partir des faits collectés ;
- des **recommandations** éditoriales ;
- deux exports : **PDF** (ReportLab) et **image PNG** (Pillow).

La fiche porte la mention « Analyse automatique — vérification humaine
requise ». Les téléchargements passent par des requêtes authentifiées : les
fichiers ne sont jamais exposés par une URL publique.

### Étape 6 — Décider et archiver

La rédaction utilise la fiche pour décider : publier un fact-check, attendre une
confirmation officielle, ou archiver le dossier. Le statut de la rumeur
(`en analyse`, `analyse terminée`, `archivée`) reflète cette décision.

---

## 5. Les mécanismes, expliqués simplement

### 5.1 Empreinte SHA-256

Le contenu de la rumeur est normalisé (accents supprimés, minuscules, ponctuation
retirée), puis transformé en une empreinte unique de 64 caractères. Deux textes
identiques après normalisation produisent la même empreinte : la détection de
doublon exact est instantanée et ne dépend d'aucun modèle.

### 5.2 Similarité TF-IDF sur n-grammes de caractères

Pour reconnaître un texte **réécrit** (majuscules, emojis, fautes, version
raccourcie), le backend découpe le texte en séquences de 3 et 4 caractères
(« n-grammes »), calcule leur importance relative (TF-IDF) et compare deux textes
avec deux mesures complémentaires :

```text
score = 0,5 × similarité cosinus(TF-IDF)
      + 0,5 × recouvrement des n-grammes du texte le plus court
```

Le score va de 0 (aucun rapport) à 1 (identique). Cette approche, implémentée en
Python pur, évite une dépendance lourde comme scikit-learn et reste robuste sur
des textes courts en français ou en malagasy.

### 5.3 Seuils métier

| Seuil | Usage |
|---|---|
| ≥ 0,90 | Considérer une nouvelle rumeur comme un doublon |
| ≥ 0,80 | Créer un lien de propagation entre deux publications |
| ≥ 0,50 | Afficher une similarité comme indice, sans créer de lien |

Ces seuils sont des paramètres, pas des vérités : ils devront être recalibrés sur
un corpus réel.

### 5.4 Source Zéro

La « Source Zéro » est la **publication la plus ancienne enregistrée** pour une
rumeur (l'identifiant le plus faible départage les dates égales). Ce n'est donc
pas nécessairement l'origine réelle de la rumeur : c'est la première trace
documentée par la rédaction. L'interface et le rapport emploient le terme
« première détection » pour rester honnêtes sur cette limite.

### 5.5 Alertes de texte (0–100)

| Signal | Points par expression | Plafond |
|---|---|---|
| Langage alarmiste | 8 | 25 |
| Appel au partage | 10 | 20 |
| Absence de source | 20 | 20 |
| Promesse financière | 10 | 25 |
| Urgence artificielle | 7 | 15 |
| Contenu sensible | 7 | 20 |

La détection repose sur des lexiques français et malagasy, des expressions
courtes et des règles explicites. Le score texte est plafonné à 45 points dans le
calcul final.

### 5.6 Alertes de compte

| Règle | Déclenchement | Gravité |
|---|---|---|
| Compte récent | Créé il y a moins de 30 jours | Élevée |
| Faible audience | Moins de 100 abonnés | Moyenne |
| Nom trompeur | Contient « officiel », « alerte », « urgence », « info »… | Variable |
| Profil anonyme | Aucun nom et aucune URL de profil exploitables | Moyenne |
| Comportement suspect | Signalé manuellement par le journaliste | Variable |

Ces règles ne prouvent rien : elles indiquent seulement qu'il faut vérifier
l'identité du compte auprès de l'institution concernée.

### 5.7 Score de crédibilité

Le score part de 100 et retire des points :

```text
− alertes de texte        (maximum 45)
− alertes de compte       (maximum 30)
− absence de source       (−8)
− aucune publication      (−15)
− compte source récent    (−5)
− diffusion rapide        (−5)   [≥ 5 publications en ≤ 24 h]
```

Le résultat est borné entre 0 et 100.

| Score | Niveau de risque |
|---|---|
| 80–100 | Faible |
| 60–79 | Moyen |
| 40–59 | Élevé |
| 0–39 | Très élevé |

Un score bas signifie « dossier préoccupant, à traiter en priorité », jamais
« information fausse ».

---

## 6. Architecture technique

```text
Fanilo/
├── backend/                     API Django/DRF
│   ├── manage.py
│   ├── config/                  settings, URLs, WSGI/ASGI
│   ├── investigation/           application métier
│   │   ├── models.py            7 modèles métier en français
│   │   ├── serializers.py       validation et sérialisation
│   │   ├── views.py             endpoints (vues minces)
│   │   ├── services/
│   │   │   ├── service_similarite.py
│   │   │   ├── service_propagation.py
│   │   │   ├── service_analyse_texte.py
│   │   │   ├── service_analyse_compte.py
│   │   │   └── service_rapport.py
│   │   ├── management/commands/seed_donnees_demo.py
│   │   └── tests.py
│   ├── db.sqlite3
│   └── media/                   captures, PDF, images
├── factcheck-mada-front/        interface Angular
│   └── src/app/
│       ├── core/                services, intercepteur JWT, garde
│       ├── shared/              composants réutilisables
│       └── features/            authentification, tableau de bord,
│                                rumeurs, publications, propagation, rapport
├── docs/                        API, guide, historique, scénario, Postman
├── env/                         environnement virtuel Python
├── DESCRIPTION-PROJET.md
├── PITCH-ET-PERSPECTIVES.md
└── README.md
```

**Principe d'architecture** : les vues HTTP ne contiennent pas de logique métier.
Elles délèguent aux services, ce qui rend chaque règle testable isolément et
permet de faire évoluer l'interface sans toucher au moteur.

### Modèle de données

| Modèle | Rôle |
|---|---|
| `Journaliste` | Utilisateur, rôle, rédaction |
| `Rumeur` | Dossier d'investigation, empreinte, statut, langue |
| `PublicationSource` | Trace publique saisie manuellement |
| `LienPropagation` | Lien de similarité parent → enfant |
| `AlerteTexte` | Signal détecté dans le texte |
| `AlerteCompte` | Signal détecté sur le compte |
| `RapportVerification` | Fiche, score, exports PDF/PNG |

### API

Toutes les routes sont préfixées par `/api/`.

| Méthode | Route | Rôle |
|---|---|---|
| GET | `/sante/` | Santé publique |
| POST | `/authentification/inscription/` | Créer un compte |
| POST | `/authentification/connexion/` | Obtenir les jetons |
| POST | `/authentification/rafraichir-token/` | Renouveler l'accès |
| GET | `/authentification/profil/` | Profil connecté |
| GET/POST | `/rumeurs/` | Lister / créer |
| GET/PATCH/DELETE | `/rumeurs/{id}/` | Détail / modifier / supprimer |
| GET/POST | `/rumeurs/{id}/publications/` | Lister / ajouter |
| GET | `/rumeurs/{id}/arbre-propagation/` | Timeline et statistiques |
| POST | `/publications/{id}/analyser-compte/` | Relancer l'analyse du compte |
| POST | `/rumeurs/{id}/analyser-texte/` | Relancer l'analyse du texte |
| POST | `/rumeurs/{id}/generer-rapport/` | Générer la fiche |
| GET | `/rumeurs/{id}/rapport/` | Consulter la fiche |
| GET | `/rumeurs/{id}/rapport/pdf/` | Télécharger le PDF |
| GET | `/rumeurs/{id}/rapport/image/` | Télécharger le PNG |
| GET | `/tableau-de-bord/statistiques/` | Statistiques agrégées |

Documentation interactive : `http://localhost:8000/api/docs/`.

### Interface

- 9 pages : connexion, inscription, tableau de bord, liste des rumeurs, nouvelle
  rumeur, détail, ajout de publication, propagation, rapport.
- Composants réutilisables : badge de risque, carte d'alerte, chargeur, message
  d'erreur, navigation, carte de publication, carte de statistique, badge Source
  Zéro, état vide.
- Intercepteur JWT avec rafraîchissement unique, garde de route, formulaires
  réactifs, gestion centralisée des erreurs en français.
- Responsive, couleurs bleu foncé, blanc, rouge doux et vert.

---

## 7. Sécurité et données personnelles

- JWT obligatoire sur toutes les routes métier ; permission `IsAuthenticated` par
  défaut.
- Cloisonnement par journaliste ; les administrateurs supervisent l'ensemble.
- Inscription limitée au rôle `journaliste`.
- Uploads limités aux images de 5 Mo, noms de fichiers générés (UUID).
- CORS restreint, limitation de débit activée.
- Clé secrète, mode debug, base de données et origines pilotés par `.env`.
- Aucun scraping, aucune connexion non autorisée à un réseau social.
- Aucune donnée privée WhatsApp ou Messenger collectée.
- En production : stockage privé ou URL signée pour `media/`, HTTPS,
  PostgreSQL, `DEBUG=False`.

---

## 8. Ce que l'outil ne fait pas

Ces limites sont assumées et documentées, car elles conditionnent la crédibilité
du projet.

| Limite | Conséquence |
|---|---|
| **Aucune collecte automatique** | Les publications sont saisies par un journaliste. Facebook, WhatsApp et TikTok ne sont pas accessibles par API pour un média. |
| **Aucun verdict de vérité** | L'outil ne remplace ni la vérification, ni la décision éditoriale. |
| **La Source Zéro est relative** | C'est la plus ancienne publication *saisie*, pas forcément l'origine réelle. |
| **Les captures ne sont pas analysées** | Une capture d'écran est stockée comme preuve, pas interprétée par un modèle d'image. |
| **La similarité est heuristique** | Les seuils doivent être calibrés sur un corpus réel malgache. |
| **Le score n'est pas prédictif** | Il agrège des signaux explicables ; il ne mesure pas une probabilité de fausseté. |
| **Les intégrations sociales sont des stubs** | Les clients Facebook, TikTok et WhatsApp sont des points d'extension, non actifs. |
| **Les tests valident le logiciel** | 41 tests backend et 3 parcours E2E prouvent la robustesse technique, pas la performance de détection. |

---

## 9. Lancer le projet

### Backend

```bash
cd backend
cp .env.example .env        # puis adapter CLE_SECRETE
../env/bin/python manage.py migrate
../env/bin/python manage.py seed_donnees_demo
../env/bin/python manage.py runserver
```

Ou depuis la racine :

```bash
./demarrer-backend.sh
```

### Frontend

```bash
cd factcheck-mada-front
npm install
npm start
```

Ou depuis la racine :

```bash
./demarrer-front.sh
```

Ouvrir `http://localhost:5173`.

Comptes de démonstration : `demo` / `Demo1234!` (journaliste) et `redaction` /
`Demo1234!` (rédacteur en chef).

### Vérifier l'ensemble

```bash
./verifier-tout.sh
```

---

## 10. Validation

| Vérification | Résultat |
|---|---|
| `manage.py check` | 0 problème |
| Migrations | aucune modification détectée |
| Tests backend | 41 réussis |
| `pip check` | aucune dépendance cassée |
| Schéma OpenAPI | valide |
| Build Angular | réussi |
| Tests unitaires frontend | 15 réussis |
| Scénarios Playwright | 3 réussis |

Les tests couvrent : normalisation et similarité, authentification JWT, isolation
entre journalistes, doublons, filtres, propagation, première détection, alertes
de compte et de texte, upload d'image, rapport, exports PDF/PNG, tableau de bord,
administration, jeu de démonstration et disponibilité de Swagger/OpenAPI.

---

## 11. Glossaire

| Terme | Définition |
|---|---|
| **Source Zéro** | Première publication enregistrée pour une rumeur |
| **Empreinte** | SHA-256 du texte normalisé, pour détecter un doublon exact |
| **TF-IDF** | Mesure d'importance des n-grammes dans un texte |
| **N-gramme** | Séquence de 3 ou 4 caractères utilisée pour comparer des textes |
| **Alerte** | Signal explicable, jamais une preuve |
| **Score de crédibilité** | Indice 0–100 agrégant les alertes et le contexte |
| **Niveau de risque** | Traduction éditoriale du score (faible à très élevé) |
| **Triage** | Priorisation des dossiers, sans jugement de vérité |
