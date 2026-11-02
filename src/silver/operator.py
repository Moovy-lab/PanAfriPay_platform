from __future__ import annotations

import argparse
import time

from delta_utils import log_event, read_source, write_delta_merge
from spark_session import get_spark


def run(csv_source: bool = False) -> None:
    started = time.monotonic()
    spark = get_spark("silver-operators")
    source = read_source(spark, "operators", csv_source)
    rows_in = source.count()
    silver = source.cache()
    rows_out = silver.count()
    write_delta_merge(spark, silver, "operators", "operator_code")
    log_event(
        job="operators",
        table="operators",
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
