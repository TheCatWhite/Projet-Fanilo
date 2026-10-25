# API FactCheck Mada

Base URL locale : `http://localhost:8000/api`

## Documentation interactive

Le schéma OpenAPI 3 est généré automatiquement depuis le code :

| Route | Description |
|---|---|
| `GET /api/schema/` | Schéma OpenAPI (YAML par défaut, JSON avec `Accept: application/json`) |
| `GET /api/docs/` | Swagger UI |
| `GET /api/redoc/` | Redoc |

Ouvrir `http://localhost:8000/api/docs/`, cliquer sur **Authorize**, puis coller
le jeton d'accès obtenu via `POST /api/authentification/connexion/`. Le bouton
autorise les appels aux routes protégées avec le schéma `Bearer`.

La documentation peut être désactivée en production :

```env
DOCUMENTATION_ACTIVE=False
```

Toutes les réponses sont en JSON. Sauf mention contraire, les routes protégées
attendent l'en-tête :

```http
Authorization: Bearer <jeton_acces>
```

Les erreurs utilisent le format standard DRF, avec des messages en français :

```json
{"detail": "Rumeur introuvable ou accès non autorisé."}
```

```json
{"titre": ["Ce champ est obligatoire."]}
```

---

## 1. Santé

### `GET /sante/`

Publique, sans authentification.

```json
{
  "statut": "ok",
  "service": "API FactCheck Mada"
}
```

---

## 2. Authentification

### `POST /authentification/inscription/`

Publique. Le rôle est toujours forcé à `journaliste`.

```json
{
  "nom_utilisateur": "demo2",
  "email": "demo2@factcheck.mg",
  "mot_de_passe": "MotDePasse123!",
  "confirmation_mot_de_passe": "MotDePasse123!",
  "redaction": "La Gazette"
}
```

Réponse `201` :

```json
{
  "message": "Compte créé avec succès.",
  "journaliste": {
    "id": 1,
    "nom_utilisateur": "demo2",
    "email": "demo2@factcheck.mg",
    "redaction": "La Gazette",
    "role": "journaliste",
    "date_inscription": "2026-10-25T18:51:49.123456+03:00",
    "est_administrateur": false
  },
  "jeton_acces": "...",
  "jeton_rafraichissement": "..."
}
```

Erreurs : `400` (champ manquant, mot de passe trop faible, doublon d'e-mail ou de
nom d'utilisateur).

> Le validateur Django refuse un mot de passe trop proche du nom d'utilisateur.

### `POST /authentification/connexion/`

```json
{"nom_utilisateur": "demo", "mot_de_passe": "Demo1234!"}
```

Réponse `200` : mêmes champs que l'inscription, avec
`"message": "Connexion réussie."`. Erreur `401` si les identifiants sont faux.

### `POST /authentification/rafraichir-token/`

```json
{"jeton_rafraichissement": "..."}
```

L'alias standard `refresh` est également accepté. Réponse `200` :

```json
{"jeton_acces": "...", "message": "Jeton d'accès renouvelé."}
```

Erreur `400` si le jeton est invalide ou expiré.

### `GET /authentification/profil/`

Réponse `200` : profil du journaliste connecté.

---

## 3. Rumeurs

### `POST /rumeurs/`

Protégée.

```json
{
  "titre": "Alerte prétendue sur une pénurie de carburant",
  "contenu": "Texte complet de la rumeur...",
  "langue": "fr"
}
```

Création `201` :

```json
{
  "cree": true,
  "message": "Rumeur enregistrée.",
  "rumeur": {"id": 1, "titre": "...", "empreinte_contenu": "..."},
  "similaires": [
    {"id": 4, "titre": "Rumeur proche", "score_similarite": 0.72}
  ]
}
```

Doublon (score ≥ 0,90 ou empreinte identique) — réponse `200` :

```json
{
  "cree": false,
  "message": "Une rumeur similaire a déjà été enregistrée.",
  "rumeur": {"id": 1, "...": "..."},
  "similaires": [{"id": 1, "score_similarite": 1.0}]
}
```

La comparaison porte sur le contenu normalisé. Les rumeurs proches sous le seuil
de 0,90 sont signalées dans `similaires` sans bloquer la création.

### `GET /rumeurs/`

Paramètres :

| Paramètre | Exemple | Description |
|---|---|---|
| `statut` | `en_analyse` | `en_analyse`, `analyse_terminee`, `archivee` |
| `titre` | `carburant` | Recherche partielle sur le titre |
| `recherche` | `penurie` | Recherche dans le titre et le contenu |
| `date_debut` | `2026-10-01` | Création à partir de cette date |
| `date_fin` | `2026-10-31` | Création jusqu'à cette date |
| `tri` | `-cree_le` | `cree_le`, `titre`, `statut` (préfixe `-` accepté) |
| `page` | `1` | Page courante |
| `taille_page` | `20` | Taille maximale 100 |

Réponse paginée :

```json
{
  "total": 12,
  "suivant": "http://localhost:8000/api/rumeurs/?page=2",
  "precedent": null,
  "resultats": [
    {
      "id": 1,
      "titre": "...",
      "extrait_contenu": "...",
      "statut": "en_analyse",
      "statut_libelle": "En analyse",
      "nombre_publications": 3,
      "score_credibilite": 42,
      "niveau_risque": "eleve",
      "niveau_risque_libelle": "Élevé",
      "cree_le": "..."
    }
  ]
}
```

### `GET /rumeurs/{id}/`

Détail complet : contenu, publications (avec alertes de compte), alertes de texte,
liens de propagation et rapport.

### `PATCH /rumeurs/{id}/`

Champs modifiables : `titre`, `contenu`, `statut`. Le contenu est renormalisé et
rehaché. Si le nouveau texte crée un doublon, réponse `400` :

```json
{
  "detail": "Une rumeur similaire existe déjà. La modification n'a pas été enregistrée.",
  "similaires": [{"id": 2, "score_similarite": 0.95}]
}
```

### `DELETE /rumeurs/{id}/`

Réponse `204`. Les publications, alertes, liens et rapport liés sont supprimés en
cascade, ainsi que les fichiers médias du rapport.

---

## 4. Publications et propagation

### `POST /rumeurs/{id}/publications/`

Accepte `application/json` ou `multipart/form-data` (capture d'écran).

```json
{
  "plateforme": "facebook",
  "url_publication": "https://facebook.com/posts/123",
  "nom_auteur": "Alerte Info Madagascar",
  "url_profil_auteur": "https://facebook.com/alerte.info",
  "date_creation_compte": "2026-10-15",
  "nombre_abonnes": 120,
  "date_publication": "2026-10-23T08:30:00Z",
  "texte_brut": "Texte de la publication..."
}
```

Champs optionnels : `url_publication`, `url_profil_auteur`,
`date_creation_compte`, `nombre_abonnes`, `texte_brut`, `capture_ecran`.
`date_publication` est obligatoire.

Traitement automatique :

1. création de la publication ;
2. recalcul de la première détection (date la plus ancienne) ;
3. création des liens de propagation (similarité ≥ 0,80, sens chronologique) ;
4. analyse du compte ;
5. analyse du texte de la rumeur.

Réponse `201` :

```json
{
  "message": "Publication enregistrée et analysée.",
  "publication": {
    "id": 2,
    "plateforme": "facebook",
    "plateforme_libelle": "Facebook",
    "est_premiere_detection": false,
    "alertes_compte": [
      {
        "type_alerte": "compte_recent",
        "gravite": "elevee",
        "description": "..."
      }
    ]
  },
  "liens_crees": [
    {
      "publication_parent_id": 1,
      "publication_enfant_id": 2,
      "score_similarite": 0.94
    }
  ],
  "alertes_compte": [],
  "analyse_texte": {
    "score_risque_texte": 74,
    "nombre_alertes": 7,
    "alertes": []
  },
  "premiere_publication_detectee": {"id": 1, "...": "..."}
}
```

Capture d'écran en multipart :

```bash
curl -X POST "$BASE/rumeurs/1/publications/" \
  -H "Authorization: Bearer $TOKEN" \
  -F "plateforme=facebook" \
  -F "nom_auteur=Alerte Info" \
  -F "date_publication=2026-10-23T08:30:00Z" \
  -F "texte_brut=Texte de la publication" \
  -F "capture_ecran=@capture.png"
```

Limites : image de 5 Mo maximum, formats JPG, PNG, WEBP ou GIF.

### `GET /rumeurs/{id}/publications/`

Liste chronologique (date croissante), avec les alertes de compte imbriquées.

### `GET /rumeurs/{id}/arbre-propagation/`

```json
{
  "rumeur_id": 1,
  "premiere_publication_detectee": {
    "id": 1,
    "plateforme": "facebook",
    "nom_auteur": "Alerte Info Madagascar",
    "date_publication": "...",
    "est_premiere_detection": true,
    "indicateurs_risque": ["Compte récent (gravité élevée)"]
  },
  "noeuds": [
    {
      "id": 1,
      "plateforme": "facebook",
      "plateforme_libelle": "Facebook",
      "nom_auteur": "Alerte Info Madagascar",
      "url_publication": "https://...",
      "date_publication": "...",
      "est_premiere_detection": true,
      "indicateurs_risque": ["Compte récent (gravité élevée)"],
      "nombre_alertes": 2
    }
  ],
  "liens": [
    {
      "publication_parent_id": 1,
      "publication_enfant_id": 2,
      "score_similarite": 0.94
    }
  ],
  "statistiques_propagation": {
    "nombre_publications": 5,
    "plateformes": ["facebook", "whatsapp"],
    "premiere_publication": "...",
    "derniere_publication": "...",
    "vitesse_estimee": "5 publications en 6 heures",
    "duree_heures": 6.0,
    "repartition_plateformes": {"facebook": 3, "whatsapp": 2}
  }
}
```

### `POST /publications/{id}/analyser-compte/`

Relance les règles d'analyse du compte. Les alertes automatiques sont remplacées,
pas dupliquées.

```json
{
  "publication_id": 2,
  "nombre_alertes": 2,
  "alertes": [
    {
      "type_alerte": "compte_recent",
      "gravite": "elevee",
      "description": "Le compte a été créé il y a 12 jour(s)..."
    }
  ],
  "message": "Analyse du compte terminée."
}
```

### `POST /rumeurs/{id}/analyser-texte/`

```json
{
  "rumeur_id": 1,
  "score_risque_texte": 74,
  "nombre_alertes": 7,
  "alertes": [
    {
      "type_alerte": "langage_alarmiste",
      "gravite": "elevee",
      "expression_detectee": "urgence",
      "explication": "..."
    }
  ]
}
```

---

## 5. Rapports

### `POST /rumeurs/{id}/generer-rapport/`

Relance les analyses texte et comptes, calcule le score et crée ou met à jour le
rapport (opération idempotente).

```json
{
  "message": "Rapport généré.",
  "rapport": {
    "id": 1,
    "score_credibilite": 42,
    "niveau_risque": "eleve",
    "niveau_risque_libelle": "Élevé",
    "resume": "La rumeur ... Ces éléments sont des indices ...",
    "recommandations": [
      "Contacter la source originale.",
      "Vérifier auprès de l'institution mentionnée.",
      "Rechercher des publications antérieures similaires.",
      "Ne pas publier sans confirmation officielle."
    ],
    "genere_le": "...",
    "fichier_pdf": null,
    "fichier_image": null
  }
}
```

### `GET /rumeurs/{id}/rapport/`

`200` avec le rapport, ou `404` :

```json
{"detail": "Aucun rapport n'a encore été généré pour cette rumeur."}
```

### `GET /rumeurs/{id}/rapport/pdf/`

Génère puis renvoie le PDF (`application/pdf`). L'URL du fichier est enregistrée
dans `fichier_pdf`. En cas de dépendance manquante : `501`.

### `GET /rumeurs/{id}/rapport/image/`

Génère puis renvoie une carte PNG 1080 × 1080 (`image/png`), avec la mention
« Analyse automatique — vérification humaine requise ».

---

## 6. Tableau de bord

### `GET /tableau-de-bord/statistiques/`

Périmètre : rumeurs du journaliste connecté (toutes pour un administrateur).

```json
{
  "total_rumeurs": 12,
  "rumeurs_analysees": 8,
  "rumeurs_haut_risque": 3,
  "total_publications": 45,
  "plateforme_plus_active": "facebook",
  "repartition_plateformes": {"facebook": 25, "whatsapp": 15, "tiktok": 5},
  "rumeurs_recentes": [
    {
      "id": 12,
      "titre": "...",
      "score_credibilite": 35,
      "niveau_risque": "tres_eleve",
      "nombre_publications": 6,
      "cree_le": "..."
    }
  ]
}
```

`rumeurs_analysees` correspond au nombre de rapports générés.
`rumeurs_haut_risque` compte les rapports `eleve` et `tres_eleve`.

---

## 7. Codes HTTP et erreurs fréquentes

| Code | Signification |
|---|---|
| `200` | Succès (dont doublon de rumeur) |
| `201` | Création |
| `204` | Suppression |
| `400` | Validation, doublon en modification, jeton de rafraîchissement invalide |
| `401` | Authentification absente ou identifiants incorrects |
| `403` | Permission refusée |
| `404` | Ressource absente ou hors périmètre |
| `415` | Format de requête non supporté (multipart attendu) |
| `501` | Export indisponible (dépendance manquante) |

Messages utiles :

- `Identifiants d'authentification non fournis.`
- `Jeton invalide ou expiré.`
- `Rumeur introuvable ou accès non autorisé.`
- `Une rumeur similaire a déjà été enregistrée.`
- `La date de création du compte ne peut pas être dans le futur.`
- `La capture d'écran ne doit pas dépasser 5 Mo.`

---

## 8. Limites assumées

- La similarité est un indice, pas une preuve de filiation.
- Les alertes reposent sur des règles explicables ; elles peuvent produire des
  faux positifs (par exemple un nom contenant « info »).
- Aucune collecte automatique de réseaux sociaux n'est effectuée.
- Les exports PDF/image ne constituent pas un verdict de vérité.
