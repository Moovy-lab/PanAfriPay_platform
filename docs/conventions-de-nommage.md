# Conventions de nommage



Ces règles s'appliquent à tout le projet. Elles garantissent un code cohérent et facile à relire.

## 1\. Fichiers et dossiers

| Élément                                                          | Règle                                                            | Exemple                                                          |
| ---------------------------------------------------------------- | ---------------------------------------------------------------- | ---------------------------------------------------------------- |
| Dossiers                                                         | minuscules                                                       | `dags/`, `dbt/`, `src/`, `tests/`, `scripts/`, `docs/`, `infra/` |
| Fichiers Python                                                  | minuscules, tirets bas                                           | `ingest_bronze.py`, `normalize_msisdn.py`                        |
| Fichiers de test                                                 | `test_` \+ nom du module testé                                   | `test_normalize_msisdn.py`                                       |
| DAGs Airflow                                                     | minuscules, tirets bas                                           | `mobile_money_pipeline.py`                                       |
| Documentation                                                    | minuscules, tirets                                               | `architecture.md`, `runbook.md`                                  |

## 2\. Lakehouse (zones et tables Delta)

Chaque table est préfixée par sa zone.

| Zone                         | Règle                        | Exemple                      |
| ---------------------------- | ---------------------------- | ---------------------------- |
| Bronze                       | `bronze_&lt;source&gt;`      | `bronze_transactions`        |
| Silver                       | `silver_&lt;source&gt;`      | `silver_transactions`        |
| Gold                         | `gold_&lt;sujet&gt;`         | `gold_transactions_enriched` |
| Quarantaine                  | `quarantine_&lt;source&gt;`  | `quarantine_transactions`    |

- Colonnes techniques préfixées par un tiret bas : *`ingested`*`at`, *`source`*`file`, *`batch`*`id`.

- Colonnes métier en `snake_case` : `transaction_id`, `agent_id`, `initiated_at`.

- Colonnes sensibles hachées suffixées par *`hash` : `msisdn`*`hash`, `imei_hash`.

- Partitionnement : `ingestion_date` en bronze, `transaction_date` en silver et gold.

## 3\. dbt et PostgreSQL

| Couche                                                 | Préfixe                                                | Exemple                                                |
| ------------------------------------------------------ | ------------------------------------------------------ | ------------------------------------------------------ |
| Staging                                                | `stg_`                                                 | `stg_transactions`                                     |
| Intermédiaire                                          | `int_`                                                 | `int_transactions_enriched`                            |
| Dimensions                                             | `dim_`                                                 | `dim_agent`, `dim_client`, `dim_operateur`, `dim_date` |
| Faits                                                  | `fact_`                                                | `fact_transaction`, `fact_anomaly`                     |

- Noms de tables et colonnes en minuscules (PostgreSQL les met en minuscules de toute façon). Les majuscules (`FACT_TRANSACTION`) sont réservées à la documentation.

- Clés primaires : `&lt;table&gt;_id`. Clés de substitution : `&lt;dimension&gt;_key`.

- Colonnes SCD2 : `valid_from`, `valid_to`, `is_current`.

- Tests dbt : fichiers dans `dbt/tests/`, nommés `assert_&lt;règle&gt;.sql`.

## 4\. Code Python

| Élément                  | Règle                    | Exemple                  |
| ------------------------ | ------------------------ | ------------------------ |
| Fonctions, variables     | `snake_case`             | `normalize_msisdn()`     |
| Classes                  | `PascalCase`             | `TransactionRecord`      |
| Constantes               | `MAJUSCULES_TIRETS_BAS`  | `MAX_TRANSACTION_AMOUNT` |
| Modules privés           | préfixe `_`              | `_helpers.py`            |

- Annotations de type obligatoires sur toutes les fonctions.

- Code formaté par `black` et vérifié par `ruff` et `isort` (hooks pre-commit).

## 5\. Airflow

| Élément                                                              | Règle                                                                | Exemple                                                              |
| -------------------------------------------------------------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------- |
| `dag_id`                                                             | `snake_case`                                                         | `mobile_money_pipeline`                                              |
| `task_id`                                                            | `verbe_objet`                                                        | `ingest_bronze`, `run_quality_checks`, `run_dbt`, `detect_anomalies` |

## 6\. Git

- Branches : `feature/&lt;nom-court&gt;`, `fix/&lt;nom-court&gt;`, `docs/&lt;nom-court&gt;`. Exemple : `feature/bronze-ingestion`.

- Commits au format conventional commits : `type: description`.

| Type                                       | Usage                                      |
| ------------------------------------------ | ------------------------------------------ |
| `feat`                                     | nouvelle fonctionnalité                    |
| `fix`                                      | correction de bug                          |
| `docs`                                     | documentation                              |
| `test`                                     | ajout ou modification de tests             |
| `refactor`                                 | réécriture sans changement de comportement |
| `chore`                                    | outillage, configuration                   |

Exemple : `feat: ajout de l'ingestion bronze idempotente`.

- Tags de version : `v1.0.0`.

## 7\. Configuration

- Variables d'environnement : `MAJUSCULES_TIRETS_BAS` (`POSTGRES_PASSWORD`, `HASH_SALT`).

- Toutes les variables sont déclarées dans `.env.example`, sans valeur secrète.
