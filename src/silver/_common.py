from __future__ import annotations

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F


def timestamp_columns(df: DataFrame, *names: str) -> DataFrame:
    """Cast present timestamp fields using Spark's UTC session timezone."""
    for name in names:
        if name in df.columns:
            df = df.withColumn(name, F.to_timestamp(F.col(name)))
    return df


def numeric_columns(df: DataFrame, mapping: dict[str, str]) -> DataFrame:
    """Cast present numeric fields to their declared Spark types."""
    for name, data_type in mapping.items():
        if name in df.columns:
            df = df.withColumn(name, F.col(name).cast(data_type))
    return df


def deduplicate(df: DataFrame, key: str, order_by: str = "initiated_at") -> DataFrame:
    """Keep the most recent row for each key."""
    window = Window.partitionBy(key).orderBy(F.col(order_by).desc_nulls_last())
    return (
        df.withColumn("_rn", F.row_number().over(window))
        .filter(F.col("_rn") == 1)
        .drop("_rn")
    )
