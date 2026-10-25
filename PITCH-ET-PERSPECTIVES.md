# FactCheck Mada — Argumentaire et perspectives

> **La phrase à retenir** : un outil de triage OSINT souverain, juridiquement
> propre et pensé pour le français et le malagasy, qui aide les rédactions à
> documenter une rumeur au lieu de prétendre savoir si elle est vraie.

---

## 1. Pourquoi ce projet existe

Les rédactions malgaches font déjà du fact-checking. Ce qui leur manque, ce n'est
pas la compétence : c'est **un dossier de preuve structuré**, produit assez vite
pour être utile avant que la rumeur ne se répande.

Aujourd'hui, ce dossier tient souvent dans une conversation WhatsApp, quelques
captures d'écran et un tableur. Résultat : la chronologie est approximative, la
première occurrence est inconnue, les preuves disparaissent avec les publications,
et chaque nouveau dossier recommence de zéro.

FactCheck Mada transforme ce travail en un objet unique, horodaté, exportable et
défendable.

## 2. Ce qui rend le projet crédible

### 2.1 Il ne promet pas ce qu'il ne peut pas tenir

La plupart des projets de « détection de fake news » promettent un score de
vérité. Ce score n'existe pas : aucun modèle ne peut certifier la véracité d'une
affirmation politique ou sanitaire. FactCheck Mada revendique l'inverse — des
indices, des alertes, une chronologie, une décision humaine. C'est moins
spectaculaire, et beaucoup plus solide face à un rédacteur en chef, un avocat ou
un bailleur.

### 2.2 Il est juridiquement propre

- Aucun scraping de profils.
- Aucune collecte de données privées WhatsApp ou Messenger.
- Aucune reproduction massive de contenus protégés.
- Seules les traces publiques, saisies par un journaliste, sont conservées.

C'est un avantage décisif : les outils qui aspires des réseaux sociaux sont
fragiles juridiquement, et leur accès peut être coupé du jour au lendemain.

### 2.3 Il est traçable

Chaque alerte est expliquée, chaque score est calculé par une formule visible,
chaque publication est horodatée. Un dossier peut être rouvert, audité, corrigé.
La fiche PDF porte la mention « Analyse automatique — vérification humaine
requise ».

### 2.4 Il est pensé pour Madagascar

- Interface entièrement en français.
- Lexiques de détection en français **et** en malagasy.
- Plateformes réellement utilisées localement : WhatsApp, Facebook, Messenger,
  TikTok, YouTube.
- Fuseau `Indian/Antananarivo`, dates et nombres au format français.
- Fonctionne sans budget cloud : SQLite, Python pur, aucune dépendance à un
  service payant.

### 2.5 Il est déjà fonctionnel

Ce n'est pas une maquette. Le backend compte 41 tests automatisés, l'interface 15
tests unitaires et 3 parcours de bout en bout ; le build de production passe. Le
parcours complet — inscription, rumeur, publications, alertes, propagation,
rapport, téléchargement — est opérationnel.

## 3. Ce qui le distingue des alternatives

| Alternative | Limite | Apport de FactCheck Mada |
|---|---|---|
| Vérifier à la main dans un tableur | Lent, non traçable, preuves dispersées | Dossier unique, chronologie, exports |
| Détecteur automatique de « fake news » | Verdict non fiable, non défendable | Indices explicables, décision humaine |
| Outils de monitoring social payants | Coûteux, couverture faible à Madagascar, données non maîtrisées | Coût quasi nul, données locales, bilingue |
| API officielles des plateformes | Inaccessibles à un média indépendant | Aucune dépendance, saisie maîtrisée |
| IA générative seule | Hallucinations, non-reproductibilité | L'IA reste une aide, jamais une autorité |

## 4. Trois cas d'usage concrets

### Cas 1 — Rumeur sanitaire sur WhatsApp

Une rumeur annonce la fermeture d'un hôpital. Le journaliste saisit le message
reçu, la capture et le numéro de l'émetteur. L'outil détecte un appel au partage,
une urgence artificielle et l'absence de source. La fiche indique « contacter
l'établissement » et « exiger un document officiel ». Le fact-check est publié en
quelques heures, avec une chronologie vérifiable.

### Cas 2 — Fausse annonce officielle sur Facebook

Une page se présente comme le ministère de la Santé. L'alerte « nom
potentiellement trompeur » et « compte récent » oriente la vérification. Le
journaliste contacte le ministère, obtient un démenti, et publie une fiche qui
cite la Source Zéro et l'heure exacte de première détection.

### Cas 3 — Propagation d'une vidéo TikTok

La même vidéo est reprise par cinq comptes. L'outil relie les publications
similaires, calcule une diffusion en moins de 24 heures et signale une
propagation rapide. La rédaction sait qu'il faut publier vite, et sur quels
comptes appuyer la démonstration.

## 5. Indicateurs d'impact à suivre

Le projet doit être évalué sur des indicateurs mesurables, pas sur des
impressions.

| Indicateur | Ce qu'il mesure |
|---|---|
| Temps de constitution d'un dossier | De la première saisie à la fiche exportée |
| Part de dossiers avec Source Zéro identifiée | Utilité réelle de la chronologie |
| Nombre de fact-checks publiés à partir de l'outil | Adoption éditoriale |
| Délai entre détection et publication | Valeur du triage |
| Taux de dossiers rouverts / corrigés | Qualité de la traçabilité |
| Retours des journalistes | Ergonomie et confiance |

Ces chiffres doivent être collectés sur 2 à 3 rédactions pilotes, sur au moins
trois mois. Ils n'existent pas encore : c'est précisément l'objet de la phase
pilote.

## 6. Feuille de route

### Horizon 1 — Consolider (1 mois)

Objectif : rendre l'outil agréable à utiliser au quotidien.

1. **Champs de volume et d'échantillon** : `nombre_partages_estime`,
   `methode_collecte`, `url_archive`. Le rapport distingue explicitement
   « volume observé » et « échantillon analysé ».
2. **Import CSV** : saisir 50 publications en un envoi, avec dédoublonnage par
   URL et rapport d'erreurs ligne par ligne.
3. **OCR des captures** : Tesseract en local, gratuit, pour pré-remplir le texte
   brut à partir d'une capture d'écran.
4. **Regroupement en grappes** : afficher « 12 partages entre 14 h et 16 h »
   plutôt que 12 nœuds illisibles.

### Horizon 2 — Automatiser sans se tromper (3 mois)

Objectif : réduire la saisie et la recherche, jamais le jugement.

1. **Assistance IA encadrée** :
   - « Cette rumeur a-t-elle déjà été démentie ? » via une recherche web sourcée
     (type Perplexity Sonar), restreinte aux médias de fact-checking ;
   - chaque résultat doit porter une URL, sinon il est rejeté ;
   - aucun champ « verdict » dans le schéma de sortie ;
   - requête, modèle et réponse archivés pour l'audit ;
   - mention « Assistance IA — sources non vérifiées » dans l'interface et le PDF.
2. **Parser d'export WhatsApp** : à partir du fichier `.txt` exporté par
   l'application, reconstituer des publications datées. C'est le levier le plus
   rentable à Madagascar.
3. **Graphe multi-parents** : une publication peut être republiée par plusieurs
   comptes. Le modèle actuel impose un seul parent ; il faut passer à un graphe
   orienté pour rester fidèle à la diffusion réelle.
4. **Archivage systématique** : enregistrer une copie (archive.today ou Wayback)
   de chaque publication, car l'original peut disparaître. C'est un impératif de
   chaîne de preuve.

### Horizon 3 — Passer à l'échelle (12 mois)

1. **PostgreSQL + file de tâches** (Celery/Redis) pour les analyses longues et les
   imports massifs.
2. **PWA mobile** pour la saisie terrain, avec mode hors ligne.
3. **Multi-rédactions** : espaces séparés, rôles, journal d'audit.
4. **Enrichissement malgache** : lexiques, variantes dialectales, translittération.
5. **API publique** pour les rédactions partenaires et les écoles de journalisme.
6. **Tableau de bord d'impact** : temps gagné, dossiers traités, fact-checks
   publiés.

## 7. Ce que le projet refuse de faire

Ces refus sont des choix stratégiques, pas des oublis.

- **Pas de scraping de profils** : illégal ou contraire aux conditions
  d'utilisation, et vulnérable à une coupure d'accès.
- **Pas de verdict automatique** : impossible à justifier, dangereux
  juridiquement, destructeur de confiance.
- **Pas d'agent autonome qui publie** : un fact-check engage une rédaction. Un
  système qui décide seul n'est pas auditable.
- **Pas de revente de données** : les dossiers appartiennent aux rédactions.

## 8. Modèle de soutien et de financement

Trois pistes réalistes, non exclusives :

1. **Pilotes avec des rédactions** : déploiement accompagné, formation, retour
   d'expérience. C'est la première étape, et elle peut être gratuite ou à coût
   symbolique.
2. **Subventions aux médias et à l'éducation aux médias** : fonds francophones,
   programmes de lutte contre la désinformation, appels d'offres universitaires.
3. **Prestations** : formation d'étudiants en journalisme, adaptation de l'outil
   à une autre langue ou à un autre pays, hébergement géré.

Le coût d'exploitation est volontairement bas : un serveur modeste, SQLite ou
PostgreSQL, aucune API payante obligatoire. L'IA reste optionnelle et plafonnée.

## 9. Risques et parades

| Risque | Parade |
|---|---|
| Adoption faible par les journalistes | Co-conception avec 2-3 rédactions, formation, saisie en moins de 3 minutes |
| Saisie manuelle trop lente à 50 sources | Import CSV, OCR, grappes, parser WhatsApp |
| Seuils mal calibrés | Corpus de test malgache, ajustement documenté, seuils configurables |
| Dérive vers un « détecteur de vérité » | Principe inscrit dans le code, les textes, les rapports et les tests |
| Hallucinations d'un LLM | Schéma strict, URL obligatoire, archivage, validation humaine |
| Données personnelles | Minimisation, pas de collecte privée, stockage privé en production |
| Dépendance à un financeur | Coût d'exploitation faible, code et données maîtrisés |
| Preuves qui disparaissent | Archivage systématique et captures horodatées |

## 10. Ce qu'il reste à prouver

L'honnêteté fait partie de l'argumentaire. Trois choses ne sont pas encore
démontrées :

1. **La qualité de détection sur un corpus malgache réel.** Les tests valident le
   logiciel, pas la performance prédictive. Il faut un corpus annoté par des
   journalistes.
2. **Le gain de temps mesuré.** Il doit être chiffré sur des dossiers réels, pas
   estimé.
3. **L'usage en rédaction sous contrainte.** Un outil peut être bon et ne pas être
   adopté. Seule une phase pilote le dira.

Dire cela n'affaiblit pas le projet : cela montre qu'il est pilotable, donc
finançable.

## 11. La demande

Pour passer du MVP au produit utile :

- **2 à 3 rédactions pilotes** à Antananarivo et en région, pour trois mois ;
- **un référent juridique** sur les données personnelles et le droit de la presse ;
- **un corpus de 200 à 500 publications** annotées vrai/faux/indéterminé, pour
  calibrer les seuils — sans jamais exposer ces annotations comme un verdict
  public ;
- **un budget d'exploitation modeste** (hébergement + API IA optionnelle,
  de l'ordre de quelques dizaines d'euros par mois) ;
- **des partenaires académiques** pour l'évaluation indépendante.

## 12. Conclusion

FactCheck Mada ne vend pas une machine à dire la vérité. Il vend du temps, de la
mémoire et de la crédibilité à des rédactions qui n'ont souvent ni l'un ni
l'autre.

C'est un outil modeste dans ses promesses et ambitieux dans son usage : rendre le
fact-checking malgache plus rapide, plus traçable et plus difficile à contester.
