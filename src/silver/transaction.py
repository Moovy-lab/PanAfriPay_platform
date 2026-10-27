from __future__ import annotations

import argparse
import time

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from delta_utils import log_event, read_source, write_delta_merge
from pii import hash_msisdn
from silver._common import deduplicate, numeric_columns, timestamp_columns
from spark_session import get_spark


def transform(df: DataFrame) -> DataFrame:
    """Type, deduplicate, pseudonymise phone numbers and add the partition column."""
    df = timestamp_columns(df, "initiated_at", "completed_at")
    df = numeric_columns(df, {"amount": "decimal(14,2)", "fees": "decimal(10,2)"})
    df = deduplicate(df, "transaction_id")
    return (
        df.withColumn("sender_msisdn", hash_msisdn("sender_msisdn"))
        .withColumn("receiver_msisdn", hash_msisdn("receiver_msisdn"))
        .withColumn("transaction_date", F.to_date("initiated_at"))
    )


def run(csv_source: bool = False) -> None:
    """Run the silver transformation for transactions."""
    started = time.monotonic()
    spark = get_spark("silver-transactions")
    source = read_source(spark, "transactions", csv_source)
    rows_in = source.count()
    silver = transform(source).cache()
    rows_out = silver.count()
    write_delta_merge(
        spark, silver, "transactions", "transaction_id", partition_by="transaction_date"
    )
    log_event(
        job="transactions",
        table="transactions",
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
