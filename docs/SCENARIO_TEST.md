# Scénario de test complet

Ce scénario valide le parcours d'une démonstration de hackathon, de l'inscription
à l'export du rapport. Il nécessite `curl` et `jq`.

> Le code du backend se trouve dans `backend/` : les commandes `manage.py`
> s'exécutent depuis ce dossier.

```bash
BASE=http://localhost:8000/api
```

## 0. Vérifier que l'API répond

```bash
curl -s $BASE/sante/
# {"statut":"ok","service":"API FactCheck Mada"}
```

## 1. Inscription d'un journaliste

```bash
NOM="demo_$(date +%s)"
INSCRIPTION=$(curl -s -X POST $BASE/authentification/inscription/ \
  -H "Content-Type: application/json" \
  -d "{
    \"nom_utilisateur\": \"$NOM\",
    \"email\": \"$NOM@factcheck.mg\",
    \"mot_de_passe\": \"MotDePasse123!\",
    \"confirmation_mot_de_passe\": \"MotDePasse123!\",
    \"redaction\": \"Rédaction de démonstration\"
  }")

echo "$INSCRIPTION" | jq '{message, journaliste: .journaliste.nom_utilisateur}'
TOKEN=$(echo "$INSCRIPTION" | jq -r .jeton_acces)
RAFRAICHISSEMENT=$(echo "$INSCRIPTION" | jq -r .jeton_rafraichissement)
```

Attendu : `201`, message « Compte créé avec succès. », deux jetons.

## 2. Connexion et rafraîchissement

```bash
curl -s -X POST $BASE/authentification/connexion/ \
  -H "Content-Type: application/json" \
  -d "{\"nom_utilisateur\":\"$NOM\",\"mot_de_passe\":\"MotDePasse123!\"}" \
  | jq '{message, journaliste: .journaliste.nom_utilisateur}'

curl -s -X POST $BASE/authentification/rafraichir-token/ \
  -H "Content-Type: application/json" \
  -d "{\"jeton_rafraichissement\":\"$RAFRAICHISSEMENT\"}" \
  | jq '{message, jeton: (.jeton_acces | length > 0)}'
```

## 3. Créer une rumeur

```bash
RUMEUR=$(curl -s -X POST $BASE/rumeurs/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "titre": "Alerte prétendue sur une pénurie de carburant",
    "contenu": "URGENCE : une grave pénurie de carburant toucherait Antananarivo. Les stations seraient fermées. Partagez ce message à tous avant qu ils suppriment l information. Une aide de 500 000 ariary est offerte.",
    "langue": "fr"
  }')

echo "$RUMEUR" | jq '{cree, message, id: .rumeur.id}'
RID=$(echo "$RUMEUR" | jq -r .rumeur.id)
```

Attendu : `cree: true`, `id` renseigné.

Relancer exactement le même appel : `200`, `cree: false`, message
« Une rumeur similaire a déjà été enregistrée. » et le même `id`.

## 4. Ajouter trois publications datées

### Publication 1 — la plus récente

```bash
P1=$(curl -s -X POST $BASE/rumeurs/$RID/publications/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "plateforme": "facebook",
    "url_publication": "https://facebook.com/posts/demo-1",
    "nom_auteur": "Alerte Info Scénario",
    "url_profil_auteur": "https://facebook.com/alerte.scenario",
    "date_creation_compte": "2026-10-15",
    "nombre_abonnes": 80,
    "date_publication": "2026-10-24T08:30:00Z",
    "texte_brut": "URGENCE : une grave pénurie de carburant toucherait Antananarivo. Les stations seraient fermées. Partagez ce message à tous avant qu ils suppriment l information. Une aide de 500 000 ariary est offerte."
  }')
echo "$P1" | jq '{premiere: .publication.est_premiere_detection, alertes: (.alertes_compte | length)}'
P1ID=$(echo "$P1" | jq -r .publication.id)
```

### Publication 2 — intermédiaire (doit créer un lien)

```bash
P2=$(curl -s -X POST $BASE/rumeurs/$RID/publications/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "plateforme": "whatsapp",
    "nom_auteur": "Groupe Scénario",
    "url_profil_auteur": "",
    "date_creation_compte": null,
    "nombre_abonnes": null,
    "date_publication": "2026-10-23T08:30:00Z",
    "texte_brut": "URGENCE : une grave pénurie de carburant toucherait Antananarivo. Les stations seraient fermées. Partagez ce message à tous avant qu ils suppriment l information. Une aide de 500 000 ariary est offerte. Selon nos informations."
  }')
echo "$P2" | jq '{liens: .liens_crees, alertes: (.alertes_compte | length)}'
P2ID=$(echo "$P2" | jq -r .publication.id)
```

### Publication 3 — la plus ancienne (devient Source Zéro)

```bash
P3=$(curl -s -X POST $BASE/rumeurs/$RID/publications/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "plateforme": "tiktok",
    "url_publication": "https://tiktok.com/@scenario/video/1",
    "nom_auteur": "scenario_tiktok",
    "url_profil_auteur": "https://tiktok.com/@scenario",
    "date_creation_compte": "2026-09-01",
    "nombre_abonnes": 2500,
    "date_publication": "2026-10-22T06:00:00Z",
    "texte_brut": "URGENCE : une grave pénurie de carburant toucherait Antananarivo. Les stations seraient fermées. Partagez ce message à tous avant qu ils suppriment l information. Une aide de 500 000 ariary est offerte."
  }')
echo "$P3" | jq '{premiere: .publication.est_premiere_detection}'
P3ID=$(echo "$P3" | jq -r .publication.id)
```

## 5. Lister les publications

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  $BASE/rumeurs/$RID/publications/ \
  | jq '[.[] | {id, plateforme, date_publication, est_premiere_detection}]'
```

Attendu : ordre chronologique, `tiktok` marquée `est_premiere_detection: true`.

## 6. Analyse du texte

```bash
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  $BASE/rumeurs/$RID/analyser-texte/ \
  | jq '{score_risque_texte, nombre_alertes, types: [.alertes[].type_alerte]}'
```

Attendu : score > 0, alertes `langage_alarmiste`, `appel_au_partage`,
`absence_de_source` et `promesse_financiere`.

## 7. Analyse des comptes

```bash
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  $BASE/publications/$P1ID/analyser-compte/ \
  | jq '{nombre_alertes, alertes: [.alertes[].type_alerte]}'
```

Attendu : `compte_recent`, `faible_activite` et `nom_imposteur` pour un compte
créé récemment, peu suivi et nommé « Alerte Info… ».

## 8. Arbre de propagation

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  $BASE/rumeurs/$RID/arbre-propagation/ \
  | jq '{
      premiere: .premiere_publication_detectee.id,
      noeuds: (.noeuds | length),
      liens: .liens,
      vitesse: .statistiques_propagation.vitesse_estimee
    }'
```

Attendu : 3 nœuds, au moins 2 liens, `premiere` = identifiant TikTok, vitesse
exprimée en heures ou jours.

## 9. Générer le rapport

```bash
RAPPORT=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  $BASE/rumeurs/$RID/generer-rapport/)

echo "$RAPPORT" | jq '{
  score: .rapport.score_credibilite,
  niveau: .rapport.niveau_risque,
  recommandations: .rapport.recommandations
}'
```

Attendu : score entre 0 et 100, niveau cohérent avec le score, les quatre
recommandations de base présentes. Relancer l'appel ne crée pas de second rapport.

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  $BASE/rumeurs/$RID/rapport/ | jq '{score: .score_credibilite, niveau: .niveau_risque}'
```

## 10. Exports (optionnels)

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  -o rapport.pdf $BASE/rumeurs/$RID/rapport/pdf/
file rapport.pdf
# PDF document

curl -s -H "Authorization: Bearer $TOKEN" \
  -o rapport.png $BASE/rumeurs/$RID/rapport/image/
file rapport.png
# PNG image data, 1080 x 1080
```

## 11. Tableau de bord

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  $BASE/tableau-de-bord/statistiques/ \
  | jq '{
      total_rumeurs,
      rumeurs_analysees,
      rumeurs_haut_risque,
      total_publications,
      plateforme_plus_active
    }'
```

Attendu : `total_rumeurs: 1`, `rumeurs_analysees: 1`,
`total_publications: 3`, `plateforme_plus_active` parmi les trois plateformes.

## 12. Contrôles de sécurité

```bash
# Sans jeton : 401
curl -s $BASE/rumeurs/ | jq .

# Jeton invalide : 401
curl -s -H "Authorization: Bearer invalide" $BASE/rumeurs/ | jq .

# Rumeur inaccessible : 404
curl -s -H "Authorization: Bearer $TOKEN" $BASE/rumeurs/999999/ | jq .
```

## 13. Postman

Importer `docs/collection_postman.json`, sélectionner l'environnement
« FactCheck Mada », puis exécuter les dossiers dans l'ordre :

1. Authentification (les jetons sont enregistrés automatiquement).
2. Rumeurs (l'identifiant de rumeur est capturé).
3. Publications (l'identifiant de publication est capturé).
4. Rapport et tableau de bord.

La collection utilise `base_url = http://localhost:8000/api`. Les dates des
publications sont calculées automatiquement à l'exécution.

## 14. Swagger

Ouvrir `http://localhost:8000/api/docs/`, se connecter avec
`POST /api/authentification/connexion/`, puis cliquer sur **Authorize** et coller
le `jeton_acces` retourné. Les routes protégées peuvent ensuite être exécutées
directement depuis Swagger. L'upload de capture utilise `multipart/form-data`.

Le schéma OpenAPI est disponible sur `http://localhost:8000/api/schema/` et peut
être validé avec :

```bash
python manage.py spectacular --file /tmp/factcheck-openapi.yaml --validate
```
