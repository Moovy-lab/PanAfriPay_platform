# Dictionnaire de données — Data Warehouse Mobile Money

## 1. Dictionnaire de données de la table de faits `Fact_Transaction`

La table `Fact_Transaction` constitue la table centrale du Data Warehouse. Elle stocke les mesures quantitatives relatives aux transactions Mobile Money ainsi que les clés étrangères permettant de relier chaque transaction aux dimensions descriptives.

**Granularité :** une ligne par transaction source. Le volume initial attendu est d’environ 109 325 lignes, avant les éventuelles opérations de filtrage, de contrôle de qualité et de dédoublonnage.

| Colonne | Type de données proposé | Rôle / Description |
|---|---|---|
| `transaction_key` | BIGINT | Clé primaire technique générée dans le Data Warehouse. |
| `transaction_id` | VARCHAR(50) | Identifiant unique de la transaction dans le système source. |
| `transaction_ref` | VARCHAR(100) | Référence métier permettant d’identifier la transaction. |
| `initiated_time_key` | INT | Clé étrangère vers `Dim_Temps`, correspondant à la date d’initiation. |
| `completed_time_key` | INT, nullable | Clé étrangère vers `Dim_Temps`, correspondant à la date de finalisation, si disponible. |
| `sender_customer_key` | INT, nullable | Clé étrangère vers `Dim_Client`, identifiant le client émetteur lorsqu’il est connu. |
| `receiver_customer_key` | INT, nullable | Clé étrangère vers `Dim_Client`, identifiant le client destinataire lorsqu’il est connu. |
| `agent_key` | INT, nullable | Clé étrangère vers `Dim_Agent`, identifiant l’agent associé à la transaction, si applicable. |
| `operator_key` | INT | Clé étrangère vers `Dim_Operateur`, identifiant l’opérateur concerné. |
| `transaction_type_key` | INT | Clé étrangère vers `Dim_Transaction`, regroupant les informations descriptives sur le type, le canal et le statut de la transaction. |
| `geography_key` | INT | Clé étrangère vers `Dim_Geographie`, permettant de situer géographiquement la transaction. |
| `currency_key` | INT | Clé étrangère vers `Dim_Devise`, identifiant la devise du montant enregistré. |
| `amount` | DECIMAL(18,2) | Montant de la transaction dans la devise d’origine. |
| `fees` | DECIMAL(18,2) | Frais associés à la transaction. |
| `duration_seconds` | INT, nullable | Durée écoulée entre l’initiation et la finalisation, exprimée en secondes, si calculable. |
| `transaction_count` | INT | Compteur de transactions, initialisé à 1 pour chaque transaction source conservée. |

### Remarques de modélisation

- `transaction_key` est une clé technique du Data Warehouse, distincte de `transaction_id`, qui provient du système source.
- `sender_customer_key` et `receiver_customer_key` référencent tous deux `Dim_Client`, mais représentent deux rôles différents : l’émetteur et le destinataire.
- `initiated_time_key` et `completed_time_key` référencent tous deux `Dim_Temps`, respectivement pour l’initiation et la finalisation.
- Les attributs `transaction_status`, `channel` et `error_code` peuvent être intégrés dans `Dim_Transaction` afin de faciliter l’analyse des transactions réussies, échouées ou en attente.

## 2. Dictionnaire de données des dimensions

### 2.1. Dimension `Dim_Temps`

Cette dimension centralise les informations calendaires utilisées pour analyser l’évolution temporelle des transactions, des inscriptions et des taux de change.

| Colonne | Type proposé | Description |
|---|---|---|
| `time_key` | INT | Clé primaire de la dimension, au format `AAAAMMJJ` lorsque la date est représentable sous cette forme. |
| `full_date` | DATE | Date calendaire complète. |
| `day` | INT | Jour du mois. |
| `month` | INT | Numéro du mois. |
| `month_name` | VARCHAR(20) | Nom du mois. |
| `quarter` | INT | Trimestre de l’année. |
| `year` | INT | Année calendaire. |
| `day_of_week` | VARCHAR(15) | Jour de la semaine. |
| `is_weekend` | BOOLEAN | Indique si la date correspond à un samedi ou à un dimanche. |

**Utilisation :** analyse des volumes quotidiens et mensuels, identification des périodes de forte activité et étude des tendances temporelles.

### 2.2. Dimension `Dim_Client`

Cette dimension est construite à partir du fichier `customers.csv`. Elle contient les caractéristiques descriptives des clients Mobile Money.

| Colonne | Type proposé | Description |
|---|---|---|
| `customer_key` | INT, clé primaire | Clé technique de substitution générée par le Data Warehouse. |
| `customer_id` | VARCHAR(50) | Identifiant métier provenant du système source. |
| `msisdn` | VARCHAR(20) | Numéro de téléphone du client, normalisé selon les règles retenues. |
| `first_name` | VARCHAR(100) | Prénom du client. |
| `last_name` | VARCHAR(100) | Nom du client. |
| `birth_date` | DATE | Date de naissance nettoyée et validée. |
| `kyc_level` | VARCHAR(30) | Niveau de vérification d’identité du client. |
| `registration_date` | DATE | Date d’inscription du client. |
| `country_code` | VARCHAR(10) | Code du pays d’enregistrement du client. |
| `region` | VARCHAR(100) | Région associée au client. |
| `customer_status` | VARCHAR(30) | Statut du compte client. |

**Points de contrôle :**

- Les 50 doublons signalés dans le fichier source doivent être examinés avant le chargement.
- `customer_key` et `customer_id` doivent rester distincts.
- Une dimension à évolution lente, de type SCD Type 2, peut être envisagée pour historiser les changements de niveau KYC ou de statut.

### 2.3. Dimension `Dim_Agent`

Cette dimension est construite à partir du fichier `agents.csv`. Elle permet d’analyser l’activité du réseau d’agents selon leurs caractéristiques et leur implantation géographique.

| Colonne | Type proposé | Description |
|---|---|---|
| `agent_key` | INT, clé primaire | Clé technique du Data Warehouse. |
| `agent_id` | VARCHAR(50) | Identifiant métier de l’agent dans le système source. |
| `agent_name` | VARCHAR(150) | Nom commercial ou nom de l’agent. |
| `agent_type` | VARCHAR(50) | Catégorie ou type d’agent. |
| `operator_code` | VARCHAR(20) | Code de l’opérateur auquel l’agent est rattaché. |
| `country_code` | VARCHAR(10) | Code du pays d’implantation. |
| `region` | VARCHAR(100) | Région d’implantation. |
| `city` | VARCHAR(100) | Ville d’implantation. |
| `latitude` | DECIMAL(10,7) | Latitude géographique de l’agent. |
| `longitude` | DECIMAL(10,7) | Longitude géographique de l’agent. |
| `onboarding_date` | DATE | Date d’intégration ou d’activation de l’agent. |
| `agent_status` | VARCHAR(30) | Statut opérationnel de l’agent. |
| `commission_tier` | VARCHAR(30) | Palier ou catégorie de commission. |

**Utilisation :** analyse des dépôts et retraits par agent, ville, région, opérateur et statut opérationnel.

### 2.4. Dimension `Dim_Operateur`

Cette dimension est construite à partir du fichier `operators.csv`. Elle regroupe les informations descriptives et réglementaires relatives aux opérateurs Mobile Money.

| Colonne | Type proposé | Description |
|---|---|---|
| `operator_key` | INT, clé primaire | Clé technique du Data Warehouse. |
| `operator_code` | VARCHAR(20) | Code source identifiant l’opérateur. |
| `operator_name` | VARCHAR(100) | Nom commercial de l’opérateur. |
| `country_code` | VARCHAR(10) | Code du pays principal de l’opérateur. |
| `license_number` | VARCHAR(100) | Numéro ou référence de licence. |
| `transaction_limit_daily` | DECIMAL(18,2) | Plafond journalier de transaction, si fourni par la source. |
| `transaction_limit_monthly` | DECIMAL(18,2) | Plafond mensuel de transaction, si fourni par la source. |
| `service_start_date` | DATE | Date de lancement du service. |

**Utilisation :** comparaison des volumes, montants, frais et taux d’échec par opérateur.

> **Remarque :** les plafonds doivent correspondre aux attributs réellement disponibles dans `operators.csv`. Si le fichier ne fournit qu’un plafond général ou des limites par transaction, il ne faut pas inventer des limites journalières ou mensuelles.

### 2.5. Dimension `Dim_Transaction`

Cette dimension regroupe les attributs descriptifs issus de `transactions.csv`, après nettoyage et standardisation des valeurs.

| Colonne | Type proposé | Description |
|---|---|---|
| `transaction_type_key` | INT, clé primaire | Clé technique de la dimension. |
| `transaction_type` | VARCHAR(50) | Type de transaction : dépôt, retrait, transfert, etc. |
| `channel` | VARCHAR(50) | Canal utilisé : USSD, application mobile, agent ou API partenaire. |
| `transaction_status` | VARCHAR(30) | Statut de la transaction : réussie, échouée, en attente, etc. |
| `error_code` | VARCHAR(50), nullable | Code d’erreur normalisé, lorsqu’il existe. |

**Utilisation :** analyse des transactions par type, canal et statut, ainsi qu’identification des principales causes d’échec.

Pour un premier Data Warehouse, le regroupement de ces attributs dans une seule dimension simplifie le modèle. Il faudra toutefois maîtriser les combinaisons de valeurs pour éviter la création de lignes descriptives incohérentes.

### 2.6. Dimension `Dim_Geographie`

Cette dimension centralise les informations géographiques nécessaires aux analyses territoriales.

| Colonne | Type proposé | Description |
|---|---|---|
| `geography_key` | INT, clé primaire | Clé technique de la dimension. |
| `country_code` | VARCHAR(10) | Code du pays. |
| `region` | VARCHAR(100) | Région géographique. |
| `city` | VARCHAR(100) | Ville ou localité. |

Les données proviennent principalement de `agents.csv` et `customers.csv`. Le code pays de `transactions.csv` peut également être utilisé pour rattacher une transaction à sa zone géographique.

**Point de vigilance :** le pays du client, le pays de rattachement de l’agent et le pays d’exécution de la transaction peuvent différer. Ces informations ne doivent donc pas être fusionnées sans règle de correspondance explicite.

### 2.7. Dimension `Dim_Devise`

Cette dimension permet de gérer les devises utilisées dans les transactions et d’éviter la comparaison directe de montants exprimés dans des unités monétaires différentes.

| Colonne | Type proposé | Description |
|---|---|---|
| `currency_key` | INT, clé primaire | Clé technique de la dimension. |
| `currency_code` | VARCHAR(10) | Code de la devise, par exemple XOF, GNF ou USD. |
| `currency_name` | VARCHAR(50) | Nom de la devise. |
| `minor_unit` | INT, nullable | Nombre de décimales habituellement utilisées pour exprimer la plus petite unité monétaire, si nécessaire. |

Cette dimension permet de conserver la devise d’origine de chaque transaction. Une conversion monétaire éventuelle devra s’appuyer sur les taux de change disponibles et sur une règle de conversion définie.

## 3. Table de faits `Fact_FX_Rate`

Le fichier `fx_rates.csv` possède une granularité différente de celle des transactions. Il contient les taux de change par date et par paire de devises. Il est donc préférable de le modéliser dans une table de faits distincte.

| Colonne | Type proposé | Description |
|---|---|---|
| `fx_key` | BIGINT, clé primaire | Clé technique de la ligne de taux de change. |
| `time_key` | INT | Clé étrangère vers `Dim_Temps`, correspondant à la date du taux. |
| `source_currency_key` | INT | Clé étrangère vers `Dim_Devise`, représentant la devise de départ. |
| `target_currency_key` | INT | Clé étrangère vers `Dim_Devise`, représentant la devise de destination. |
| `source` | VARCHAR(100) | Source ou fournisseur du taux de change. |
| `exchange_rate` | DECIMAL(18,8) | Taux de change entre les deux devises, selon la convention de cotation retenue. |

**Granularité :** une ligne par date, paire de devises et source de taux lorsque plusieurs sources sont présentes.

Cette table permet de suivre l’évolution des taux de change et de fournir les informations nécessaires à la conversion des montants. Avant toute conversion, il faut définir explicitement le sens du taux, par exemple le nombre d’unités de la devise cible pour une unité de la devise source.
