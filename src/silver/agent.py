from __future__ import annotations

import argparse
import time

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from delta_utils import log_event, read_source, write_delta_merge
from silver._common import deduplicate, numeric_columns
from spark_session import get_spark


def transform(df: DataFrame) -> DataFrame:
    """Clean agents, deduplicate IDs and flag available coordinates."""

    df = numeric_columns(
        df,
        {
            "latitude": "double",
            "longitude": "double",
        },
    )
    df = deduplicate(
        df,
        "agent_id",
        order_by="agent_id",
    )
    has_geo = F.col("latitude").isNotNull() & F.col("longitude").isNotNull()

    return df.withColumn("has_geo", has_geo).withColumn(
        "onboarding_date",
        F.to_date("onboarding_date"),
    )


def run(csv_source: bool = False) -> None:
    """Run the silver transformation for customers."""
    started = time.monotonic()
    spark = get_spark("silver-agents")
    source = read_source(spark, "agents", csv_source)
    rows_in = source.count()
    silver = transform(source).cache()
    rows_out = silver.count()
    write_delta_merge(spark, silver, "agents", "agent_id")
    log_event(
        job="agents",
        table="agents",
        event="completed",
        rows_in=rows_in,
        rows_valid=rows_out,
        rows_deduplicated=rows_in - rows_out,
        duration_seconds=time.monotonic() - started,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", action="store_true")
    run(csv_source=parser.parse_args().csv)
