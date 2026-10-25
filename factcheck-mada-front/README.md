# FactCheck Mada — Frontend Angular

Interface de la plateforme d’investigation **FactCheck Mada**. Elle permet à un
journaliste de suivre une rumeur, de documenter ses sources, d’identifier une
Source Zéro, de visualiser sa propagation et de préparer une fiche de
vérification.

> **Principe fondamental** : aucun verdict « vrai » ou « faux » n’est affiché.
> L’outil produit des indices, des alertes, un score et des recommandations.
> La décision finale reste humaine.

---

## 1. Objectif et périmètre

Le frontend consomme l’API Django/DRF située dans le dossier parent. Il ne
contient aucune logique métier de similarité ou de notation : il affiche les
résultats du backend et transmet les actions de l’utilisateur.

Fonctionnalités livrées :

- connexion, inscription et déconnexion JWT ;
- rafraîchissement automatique du jeton sur une réponse `401` ;
- protection des routes privées ;
- tableau de bord agrégé ;
- liste filtrable et paginée des rumeurs ;
- création d’une rumeur avec gestion du doublon (`cree: false`) ;
- détail d’un dossier, Source Zéro et alertes textuelles ;
- ajout d’une publication avec `FormData` et capture d’écran optionnelle ;
- chronologie de propagation en CSS, sans bibliothèque de graphes ;
- génération et consultation d’une fiche de vérification ;
- téléchargement authentifié du PDF et du PNG en `Blob` ;
- interface responsive et entièrement en français.

---

## 2. Prérequis et lancement

| Outil      | Version utilisée |
| ---------- | ---------------- |
| Node.js    | 24.21.0          |
| npm        | 11.19.0          |
| Angular    | 21.2.25          |
| TypeScript | 5.9.3            |
| Vitest     | 4.1.12           |
| Playwright | 1.55.0           |

Angular 21 a été retenu car Angular CLI 17 n’est pas supporté par Node 24 dans
cet environnement. Le code reste organisé avec des composants **standalone**,
des services injectables, des guards et un intercepteur fonctionnel.

### Démarrer le backend

```bash
cd /home/catwhite/Bureau/Fanilo/backend
../env/bin/python manage.py runserver
```

L’API doit répondre sur `http://localhost:8000/api/`. Le CORS Django autorise
`http://localhost:5173`.

### Démarrer le frontend

```bash
cd /home/catwhite/Bureau/Fanilo/factcheck-mada-front
npm install
npm start
```

Ouvrir [http://localhost:5173](http://localhost:5173).

Comptes de démonstration :

| Identifiant | Mot de passe | Rôle              |
| ----------- | ------------ | ----------------- |
| `demo`      | `Demo1234!`  | journaliste       |
| `redaction` | `Demo1234!`  | rédacteur en chef |

Le backend force le rôle `journaliste` à l’inscription publique. Les autres
rôles se testent avec les comptes de démonstration ou l’administration Django.

### Repli sur le port 4200

Le port `5173` est la configuration normale. Si vous devez utiliser le port
Angular par défaut, lancez le serveur avec le proxy fourni :

```bash
ng serve --port 4200 --proxy-config proxy.conf.json
```

et remplacez temporairement `apiUrl` par `/api/` dans
`src/environments/environment.ts`.

---

## 3. Arborescence

```text
factcheck-mada-front/
├── e2e/
│   └── frontend.spec.ts             parcours Playwright
├── src/
│   ├── app/
│   │   ├── core/
│   │   │   ├── guards/              gardeAuthentification
│   │   │   ├── interceptors/        intercepteurJwt
│   │   │   ├── models/              contrats TypeScript de l’API
│   │   │   └── services/            authentification, rumeurs, publications…
│   │   ├── features/
│   │   │   ├── authentification/    connexion, inscription
│   │   │   ├── tableau-de-bord/     statistiques et activité récente
│   │   │   ├── rumeurs/             liste, création, détail
│   │   │   ├── publications/        ajout avec FormData
│   │   │   ├── propagation/         timeline CSS
│   │   │   └── rapport/             fiche et téléchargements
│   │   ├── shared/
│   │   │   ├── composants/          chargeur, badges, cartes, navigation…
│   │   │   ├── pipes/               pipeDateFrancaise
│   │   │   ├── utilitaires/         téléchargement Blob
│   │   │   └── validateurs/         confirmation du mot de passe
│   │   ├── app.component.*          coquille et navigation
│   │   ├── app.config.ts            providers Angular
│   │   └── app.routes.ts            routes et lazy loading
│   ├── environments/environment.ts  URL de l’API et nom de l’application
│   ├── styles.scss                  thème global bleu/blanc/rouge doux/vert
│   └── main.ts
├── playwright.config.ts
├── proxy.conf.json
└── package.json
```

Les composants réutilisables demandés sont présents :

- `badge-risque` ;
- `carte-alerte` ;
- `chargeur` ;
- `message-erreur` ;
- `barre-navigation`, `carte-publication`, `carte-statistique`,
  `badge-source-zero` et `etat-vide` en complément.

---

## 4. Les cinq étapes

### Étape 1 — Socle technique, modèles et services

**Objectif** : poser une base stricte, typée et testable avant les écrans.

Points clés :

- environnements et `apiUrl = http://localhost:8000/api/` ;
- modèles TypeScript alignés sur les noms réels de Django :
  `jeton_acces`, `jeton_rafraichissement`, `nom_utilisateur`,
  `score_credibilite`, `niveau_risque`, etc. ;
- `ServiceJetons` centralise `localStorage` et expose un signal réactif pour que
  la navigation disparaisse immédiatement après une déconnexion ;
- `intercepteurJwt` ajoute le `Bearer` et tente un seul rafraîchissement sur
  `401` ; le refresh utilise `HttpBackend` pour éviter une boucle d’interception ;
- `gardeAuthentification` redirige vers `/connexion` avec l’URL de retour ;
- `ServiceErreur` transforme les erreurs DRF en messages français ;
- `app.config.ts` active le router, `HttpClient` et la locale `fr-FR`.

Validation : `npm run build` OK.

### Étape 2 — Authentification et navigation

**Objectif** : permettre la connexion, l’inscription et la déconnexion.

Fichiers principaux :

- `features/authentification/connexion/` ;
- `features/authentification/inscription/` ;
- `shared/composants/message-erreur/` ;
- `shared/composants/chargeur/` ;
- `shared/validateurs/mots-de-passe.validator.ts` ;
- `app.component.*`.

Après connexion, les jetons sont stockés sous `factcheck.jeton_acces` et
`factcheck.jeton_rafraichissement`, le profil est chargé, puis l’utilisateur est
redirigé vers son tableau de bord ou vers l’URL de retour.

Validation : build OK, tests du service d’authentification et du guard OK.

### Étape 3 — Rumeurs

**Objectif** : lister, filtrer, créer et consulter les dossiers.

Fichiers principaux :

- `features/rumeurs/liste-rumeurs/` : recherche avec debounce, filtre de statut,
  pagination côté serveur, badge de risque ;
- `features/rumeurs/creer-rumeur/` : formulaire réactif et gestion du doublon ;
- `features/rumeurs/detail-rumeur/` : contenu, Source Zéro, publications,
  alertes, accès rapides, suppression ;
- `core/services/service-rumeur.ts` et `service-analyse.ts`.

Un doublon renvoie un HTTP `200` avec `cree: false` : ce n’est pas une erreur.
L’écran affiche le dossier existant et les similarités.

Validation : tests du service de rumeurs, création/suppression couvertes par
Playwright.

### Étape 4 — Publications et propagation

**Objectif** : documenter une occurrence et visualiser la chronologie.

- `features/publications/ajouter-publication/` utilise `FormData` ;
- la capture est limitée à 5 Mo et aux formats JPG, PNG, WEBP et GIF ;
- les champs vides ne sont pas envoyés ;
- `features/propagation/arbre-propagation/` affiche une timeline CSS, le score
  de similarité avec l’étape précédente, les plateformes et la Source Zéro.

Validation : test `FormData`, build et parcours Playwright vers la propagation.

### Étape 5 — Rapport et tableau de bord

**Objectif** : produire une synthèse exploitable et télécharger les exports.

- `features/rapport/fiche-verification/` charge en parallèle le dossier, l’arbre
  et le rapport ; un `404` signifie simplement qu’aucune fiche n’existe encore ;
- la génération recharge le contexte (alertes, chronologie) ;
- le PDF et le PNG sont récupérés en `Blob` avec le JWT puis téléchargés via un
  `ObjectURL` ;
- le rapport affiche la mention
  **« Analyse automatique — vérification humaine requise »** ;
- `features/tableau-de-bord/` affiche les statistiques et les dernières rumeurs.

Validation : génération, affichage et téléchargement PDF couverts par Playwright.

---

## 5. Contrats API consommés

Toutes les routes sont préfixées par `http://localhost:8000/api/`.

| Méthode          | Route                                | Usage frontend                      |
| ---------------- | ------------------------------------ | ----------------------------------- |
| POST             | `authentification/connexion/`        | connexion                           |
| POST             | `authentification/inscription/`      | inscription                         |
| POST             | `authentification/rafraichir-token/` | refresh JWT                         |
| GET              | `authentification/profil/`           | profil au rechargement              |
| GET              | `tableau-de-bord/statistiques/`      | tableau de bord                     |
| GET/POST         | `rumeurs/`                           | liste / création                    |
| GET/PATCH/DELETE | `rumeurs/{id}/`                      | détail / modification / suppression |
| GET              | `rumeurs/{id}/publications/`         | publications du dossier             |
| POST             | `rumeurs/{id}/publications/`         | ajout multipart                     |
| GET              | `rumeurs/{id}/arbre-propagation/`    | timeline et statistiques            |
| POST             | `rumeurs/{id}/analyser-texte/`       | relance de l’analyse                |
| POST             | `rumeurs/{id}/generer-rapport/`      | génération de la fiche              |
| GET              | `rumeurs/{id}/rapport/`              | lecture de la fiche                 |
| GET              | `rumeurs/{id}/rapport/pdf/`          | PDF en Blob                         |
| GET              | `rumeurs/{id}/rapport/image/`        | PNG en Blob                         |

La liste des rumeurs renvoie `total`, `suivant`, `precedent` et `resultats`.
La création renvoie `cree`, `message`, `rumeur` et `similaires`.

---

## 6. Tests et validation

### Build

```bash
npm run build
```

Résultat obtenu : compilation de production réussie, sans erreur.

### Tests unitaires Angular

```bash
npm test -- --watch=false
```

Résultat obtenu : **15 tests réussis** dans 6 fichiers.

Couverture des tests :

- création de la coquille et absence de navigation sans jeton ;
- stockage des jetons et du profil après connexion ;
- déconnexion ;
- rafraîchissement du jeton ;
- ajout du `Bearer` et rejeu après `401` ;
- guard avec et sans jeton ;
- filtres et pagination des rumeurs ;
- création avec drapeau de doublon ;
- analyse textuelle ;
- construction du `FormData` avec capture ;
- analyse de compte.

### Tests end-to-end Playwright

Le backend et le frontend doivent être lancés. Le test utilise Google Chrome
installé sur la machine (`channel: 'chrome'`).

```bash
npm run test:e2e
```

Résultat obtenu : **3 scénarios réussis**.

1. Connexion, tableau de bord, liste, détail, Source Zéro, propagation, fiche,
   génération si nécessaire et téléchargement du PDF, puis déconnexion.
2. Message d’erreur avec un mauvais mot de passe.
3. Création d’une rumeur de test puis suppression avec confirmation.

Les artefacts `test-results/`, `playwright-report/` et `blob-report/` sont
ignorés par Git.

---

## 7. Erreurs fréquentes

### `Impossible de joindre le serveur Django`

Le backend n’est pas lancé ou n’écoute pas sur le port 8000. Vérifier :

```bash
curl http://localhost:8000/api/sante/
```

### Erreur CORS sur le port 4200

Le backend autorise `3000` et `5173`. Utiliser `npm start` (port 5173) ou le
proxy fourni. Ne pas ajouter une origine sauvage en production.

### Boucle de rafraîchissement JWT

L’intercepteur ne traite que les URL privées et utilise `HttpBackend` pour le
refresh. Si le refresh échoue, les jetons sont supprimés et l’utilisateur est
renvoyé vers `/connexion`.

### La création renvoie `200` au lieu de `201`

C’est un doublon détecté. Le frontend lit `cree: false` et affiche le dossier
existant ; il ne doit pas afficher une erreur.

### `401` sur le PDF ou l’image

Les exports sont privés. Ils doivent être demandés avec
`responseType: 'blob'` et le JWT, jamais via un simple `href` public.

### `501` lors de la génération d’un rapport

Le backend dépend de ReportLab/Pillow pour les exports. Vérifier l’installation
des dépendances Python :

```bash
source env/bin/activate
pip install -r backend/requirements.txt
```

### Le rôle choisi à l’inscription est ignoré

C’est volontaire : le backend force `journaliste`. Le formulaire affiche ce rôle
en lecture seule.

### Route « Nouvelle rumeur » inaccessible ou détail incorrect

L’ordre des routes est important : `rumeurs/nouvelle` doit être déclarée avant
`rumeurs/:id`.

### Capture refusée

La capture doit être une vraie image JPG, PNG, WEBP ou GIF de moins de 5 Mo. Le
backend vérifie aussi le contenu réel du fichier avec Pillow.

### Session perdue après rechargement

Le profil est rechargé depuis `authentification/profil/` si un jeton d’accès est
présent. Si le refresh token a expiré, la déconnexion est normale.

---

## 8. Sécurité et limites

- Les jetons sont stockés dans `localStorage` pour le MVP. Une application de
  production devrait envisager des cookies `HttpOnly` et une politique CSP.
- Aucune donnée n’est scrapée : les publications sont saisies manuellement.
- Les scores et alertes sont des aides à l’enquête, pas des preuves.
- Les captures peuvent contenir des données personnelles : appliquer les règles
  éditoriales et légales de la rédaction.
- Le backend reste la source de vérité pour les permissions, les doublons, les
  analyses et les rapports.
