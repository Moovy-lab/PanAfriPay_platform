from __future__ import annotations

import argparse
import time

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from delta_utils import log_event, read_source, write_delta_merge
from pii import hash_msisdn
from silver._common import deduplicate, numeric_columns
from spark_session import get_spark

MAX_AGE_YEARS = 110


def transform(df: DataFrame) -> DataFrame:
    """Deduplicate, hash the MSISDN, parse dates and flag invalid birth dates."""
    df = numeric_columns(df, {"account_balance": "decimal(14,2)"})
    df = deduplicate(df, "customer_id", order_by="customer_id")

    raw = F.col("birth_date")
    parsed = F.when(
        raw.rlike(r"^\d{4}-\d{2}-\d{2}$") & (raw != "0000-00-00"), F.to_date(raw)
    )
    age = F.floor(F.months_between(F.current_date(), parsed) / 12)
    is_valid = parsed.isNotNull() & (age >= 0) & (age <= MAX_AGE_YEARS)

    return (
        df.withColumn("birth_date_valid", is_valid)
        .withColumn("birth_date", F.when(is_valid, parsed))
        .withColumn("registration_date", F.to_date("registration_date"))
        .withColumn("msisdn", hash_msisdn("msisdn"))
    )


def run(csv_source: bool = False) -> None:
    """Run the silver transformation for customers."""
    started = time.monotonic()
    spark = get_spark("silver-customers")
    source = read_source(spark, "customers", csv_source)
    rows_in = source.count()
    silver = transform(source).cache()
    rows_out = silver.count()
    write_delta_merge(spark, silver, "customers", "customer_id")
    log_event(
        job="customers",
        table="customers",
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
