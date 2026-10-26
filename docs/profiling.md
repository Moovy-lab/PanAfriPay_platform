# Profiling des données PanAfriPay

Ce document résume l'analyse exploratoire (EDA) des cinq fichiers CSV du projet. Le détail des calculs est dans le notebook [`notebooks/panafripay_eda.ipynb`](../notebooks/panafripay_eda.ipynb).

L'analyse est en **lecture seule** : aucune ligne n'est supprimée ni corrigée à ce stade. Le nettoyage est réalisé dans la couche silver du pipeline (voir section 5).

## 1. Données analysées

| Fichier | Lignes | Colonnes | Contenu |
|---|---:|---:|---|
| `transactions.csv` | 109 325 | 18 | Transactions Mobile Money |
| `customers.csv` | 50 050 | 11 | Clients |
| `agents.csv` | 5 005 | 12 | Agents et points de service |
| `operators.csv` | 5 | 7 | Opérateurs et limites de transaction |
| `fx_rates.csv` | 270 | 5 | Taux de change quotidiens |

- **Période des transactions** : du 1er janvier au 31 mars 2026 (UTC).
- **Devises des transactions** : XOF (76 306) et GNF (33 019).
- **Nature des données** : jeu de données synthétique fourni avec le sujet. Aucune donnée réelle n'est utilisée.

## 2. Résultats : attendu et mesuré

| Anomalie | Fichier | Attendu | Mesuré |
|---|---|---|---|
| Doublons `transaction_id` | transactions | ~5 % | 5 000 copies (4,57 %) |
| Montants invalides | transactions | ~3 % | 3 000 (2,74 %) : 1 508 négatifs + 1 492 au-dessus de la limite journalière |
| MSISDN non conformes | transactions, customers | ~2,5 % | émetteurs 2,36 % ; récepteurs 2,27 % ; clients 2,40 % |
| `agent_id` inexistant | transactions | ~1 % | 1 000 (0,91 %) |
| Transactions miroir | transactions | ~150 paires | 150 |
| Vélocité anormale | transactions | 1 cas | 1 client : 25 transactions en 8 min 48 s |
| Dates de naissance erronées | customers | ~0,5 % | 245 (0,49 %) |
| Agents sans coordonnées | agents | quelques | 160 (3,2 %) |
| Doublons clients / agents | customers, agents | 50 / 5 | 50 / 5 |

**Lecture des écarts.** Toutes les mesures sont proches des valeurs annoncées. Les nombres bruts sont ronds (5 000, 3 000, 1 000, 150) : les pourcentages du sujet semblent calculés sur une base de 100 000 transactions avant ajout des copies. Cela explique un taux un peu plus bas sur le fichier complet (4,57 % au lieu de 5 %).

## 3. Méthode de mesure

| Anomalie | Règle appliquée |
|---|---|
| Doublons | Copies en trop : lignes qui répètent un identifiant déjà vu. Les doublons exacts (toutes colonnes identiques) sont distingués des doublons conflictuels (même identifiant, valeurs différentes). |
| Montants négatifs | `amount < 0`. |
| Montants au-dessus du plafond | `amount > transaction_limit_daily` de l'opérateur (jointure sur `operator_code`). `operators.csv` ne fournit pas de plafond par transaction ; la limite journalière est utilisée comme plafond (hypothèse de travail). |
| MSISDN non conformes | Valeur non vide ne respectant pas le format `+` suivi de 8 à 15 chiffres, mesurée sur les valeurs brutes. Normalisation testée : espaces supprimés, `00` remplacé par `+`, `+` ajouté devant un numéro composé de chiffres. |
| `agent_id` inexistant | `agent_id` renseigné et absent de `agents.csv`. Un `agent_id` vide n'est pas une anomalie : il dépend du type de transaction. |
| Transactions miroir | Transaction A vers B et transaction B vers A, même montant exact, moins de 60 secondes d'écart, sur des numéros normalisés. Les copies de `transaction_id` sont retirées avant le calcul. |
| Vélocité | Au moins 25 transactions dans une fenêtre glissante de 10 minutes pour un même émetteur (numéro normalisé). |
| Dates de naissance | Quatre valeurs sentinelles du sujet (`1900-01-01`, `9999-12-31`, `0000-00-00`, `1850-05-12`), dates illisibles, et âge négatif ou supérieur à 110 ans. |
| Coordonnées | Latitude ou longitude vide ; latitude hors de -90 à 90 ; longitude hors de -180 à 180. |

## 4. Constats détaillés

### Doublons
5 000 copies de `transaction_id` (9 860 lignes concernées dans 4 860 groupes : certains identifiants apparaissent plus de deux fois), 50 copies de `customer_id` et 5 de `agent_id`.

### Montants
1 508 montants négatifs (1,38 %) et 1 492 montants supérieurs à la limite journalière (1,36 %), soit exactement 3 000. Ce chiffre rond soutient l'hypothèse « plafond = limite journalière » sans la démontrer : l'unité des limites reste à confirmer, car les transactions sont en XOF et en GNF.

### MSISDN
| Colonne | Avec espaces | Préfixe `00` | Sans `+` ni `00` | Total non conforme |
|---|---:|---:|---:|---:|
| `sender_msisdn` | 1 017 | 1 061 | 497 | 2 575 |
| `receiver_msisdn` | 293 | 293 | 160 | 746 |
| `customers.msisdn` | 491 | 470 | 241 | 1 202 |

Dans les trois cas, aucun numéro n'est invalide après normalisation : toutes les anomalies de format sont réparables en silver. Le contrôle est syntaxique et ne garantit pas que le numéro existe.

### Intégrité référentielle
1 000 transactions (0,91 %) pointent vers un `agent_id` absent de `agents.csv`. Toutes sont de type `DEPOSIT`, et leurs identifiants ont une forme différente des identifiants valides (`AGT-99…` contre `AGT-001…`).

Les 57 387 transactions sans `agent_id` sont normales : `AIRTIME_TOPUP`, `BILL_PAYMENT`, `MERCHANT_PAYMENT` et `TRANSFER` n'ont jamais d'agent, `DEPOSIT` et `WITHDRAWAL` en ont toujours un.

### Dates de naissance
245 dates invalides (0,49 %) : 56 illisibles (`0000-00-00`) et 189 d'âge impossible. Les valeurs `1900-01-01`, `1850-05-12` et `9999-12-31` se convertissent en vraies dates ; seule la règle d'âge les détecte. Aucune date invalide hors de ces quatre valeurs, aucun client mineur.

### Agents
160 agents (3,2 %) sans coordonnées, aucune coordonnée hors limites.

### Antifraude
150 paires miroir. Un seul client dépasse 25 transactions en 10 minutes ; le maximum des autres clients est de 4, donc le seuil de 25 est nettement séparé du comportement normal. Ces détections sont des alertes à investiguer, pas des preuves de fraude.

### Anomalies non annoncées par le sujet
- **289 transactions `DEPOSIT` ont un `receiver_msisdn`**, alors que seuls les `TRANSFER` en ont habituellement. Le lien avec les lignes à `agent_id` inexistant n'a pas été vérifié.
- **198 transactions `DEPOSIT` ont un `partner_merchant_id`**, alors que seuls les `BILL_PAYMENT` et `MERCHANT_PAYMENT` en ont habituellement.
- **Les 1 000 agents inexistants suivent un motif reconnaissable** (`AGT-99…`), ce qui permet une règle de détection simple.

### Contrôles de cohérence réussis
- `completed_at` est renseigné uniquement pour les transactions `SUCCESS` (96 327) et vide pour `FAILED` (6 531), `PENDING` (3 248), `REVERSED` (2 171) et `TIMEOUT` (1 048).
- Le nombre de codes d'erreur (12 998) égale celui des transactions non `SUCCESS`.
- Aucun `completed_at` n'est antérieur à `initiated_at`, aucun frais n'est négatif, aucune date de transaction n'est illisible.
- Les taux de change couvrent trois paires (`XOF->GNF`, `XOF->USD`, `GNF->USD`), 90 jours chacune, sans doublon ni taux négatif ou nul. Toutes les devises des transactions sont couvertes et aucun jour de transaction n'est sans taux : une conversion vers le dollar (USD) est possible.

## 5. Traitement prévu dans le pipeline

Les corrections se font en silver. Les lignes rejetées vont en quarantaine avec un motif de rejet, pour garder la traçabilité.

| Anomalie | Traitement prévu | Motif de quarantaine |
|---|---|---|
| Doublons `transaction_id`, `customer_id`, `agent_id` | Dédupliquer en gardant la version la plus récente ; compter les copies avant et après | - |
| MSISDN non conformes | Normaliser (format E.164), puis hacher en SHA-256 avec sel ; ne pas rejeter | - |
| Montants négatifs | Quarantaine | `NEGATIVE_AMOUNT` |
| Montants au-dessus de la limite | Quarantaine | `AMOUNT_ABOVE_LIMIT` |
| `agent_id` inexistant | Quarantaine | `UNKNOWN_AGENT` |
| Dates de naissance invalides | Conserver le client, mettre la date à vide et ajouter un indicateur `birth_date_valid = false` | - |
| Agents sans coordonnées | Conserver l'agent, coordonnées vides, indicateur `has_geo = false` | - |
| Transactions miroir | Conserver en silver ; lever une alerte dans `fact_anomaly` | - |
| Vélocité anormale | Conserver en silver ; lever une alerte dans `fact_anomaly` | - |
| `DEPOSIT` avec `receiver_msisdn` ou `partner_merchant_id` | À investiguer avant de décider ; conserver et signaler en attendant | - |

Les alertes antifraude ne déclenchent aucune action automatique : elles sont destinées à une revue humaine.

## 6. Limites et biais

- **Plafond de transaction** : `operators.csv` ne contient que des limites journalière et mensuelle. L'hypothèse « plafond = limite journalière » est cohérente avec les données (total de 3 000), mais son unité reste à confirmer auprès de la documentation métier.
- **Contrôle des numéros** : purement syntaxique. Un numéro correctement formé peut ne pas exister.
- **Jeu de données synthétique** : les pourcentages du sujet semblent calculés sur une base de 100 000 transactions ; les écarts avec les mesures sur le fichier complet sont attendus.
- **Répartition inégale** : 70 % des transactions sont en XOF et 30 % en GNF. La répartition par pays, par opérateur et par catégorie d'agent n'a pas encore été mesurée ; elle sera documentée pour évaluer une éventuelle sous-représentation.
- **Limites de la détection** : seuils fixes (60 secondes, 25 transactions en 10 minutes, montant exact), calcul de la vélocité sur l'émetteur uniquement, risque de fausses alertes et de cas manqués. Une fraude qui s'écarte de ces règles n'est pas détectée.
- **Décision humaine** : le module de détection ne bloque ni ne sanctionne ; il lève des alertes revues par une personne.
