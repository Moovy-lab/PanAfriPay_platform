# ADR-001 : Choix du format de table transactionnel (Delta Lake)



- **Statut** : Accepté

- **Date** : 20/10/2026

- **Auteur** : ZONGO Mitibmanegda Ismaila

## Contexte

Le projet construit un pipeline batch de traitement de données Mobile Money pour une plateforme panafricaine de transactions monétaires. L'architecture Lakehouse locale comporte trois zones : bronze (données brutes), silver (données nettoyées) et gold (données prêtes pour l'analyse).

Les zones silver et gold nécessitent un format de table transactionnel offrant :

- le time travel (relire une version passée d'une table) ;

- le rollback (revenir à une version antérieure) ;

- des écritures idempotentes, sans doublons en cas de réexécution ;

- un partitionnement explicite.

Ces exigences figurent dans le sujet du projet. Le pipeline s'exécute entièrement en local, avec Apache Spark comme seul moteur de calcul.

## Options étudiées

1. **Delta Lake 3.x**

2. **Apache Iceberg**

Les deux formats répondent aux exigences fonctionnelles ci-dessus.

## Décision

Nous retenons **Delta Lake 3.x** pour les zones silver et gold.

## Justifications

1. **Intégration native avec PySpark** : la configuration est simple et réduit le risque technique dans un projet de courte durée.

2. **Fonctionnalités exigées couvertes nativement** : `MERGE INTO` (écritures idempotentes), `DESCRIBE HISTORY` et lecture par version (time travel), `RESTORE` (rollback).

3. **Documentation et tutoriels abondants** : la prise en main et le dépannage sont plus rapides.

4. **Un seul moteur de calcul** : le projet n'utilise que Spark en local. L'interopérabilité multi-moteurs d'Iceberg (Trino, Flink, etc.) n'apporterait aucun bénéfice ici.

## Conséquences

**Avantages**

- Mise en œuvre rapide et stable.

- Moins de configuration, donc une stack Docker plus simple.

**Inconvénients acceptés**

- Moins d'ouverture à d'autres moteurs de calcul qu'Iceberg.

- Dépendance à l'écosystème Delta Lake.

- Une évolution du projet vers une architecture multi-moteurs nécessiterait de réévaluer ce choix (ou de les tables).
