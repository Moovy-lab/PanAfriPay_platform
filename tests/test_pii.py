import pytest
from pyspark.sql import SparkSession

from pii import hash_column, hash_msisdn, hash_value


@pytest.fixture(scope="module")
def spark() -> SparkSession:
    return SparkSession.builder.master("local[1]").appName("test").getOrCreate()


@pytest.fixture(autouse=True)
def salt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PII_HASH_SALT", "test-salt")


def test_trois_formats_donnent_le_meme_hash(spark: SparkSession) -> None:
    df = spark.createDataFrame(
        [
            ("+221771234567",),
            ("00221771234567",),
            ("+221 77 123 45 67",),
            ("221771234567",),
        ],
        ["msisdn"],
    )
    hashes = [r[0] for r in df.select(hash_msisdn("msisdn")).collect()]
    assert len(set(hashes)) == 1


def test_null_et_vide_donnent_null(spark: SparkSession) -> None:
    df = spark.createDataFrame([(None,), ("",), ("   ",)], "msisdn string")
    assert all(r[0] is None for r in df.select(hash_msisdn("msisdn")).collect())


def test_parite_spark_python(spark: SparkSession) -> None:
    df = spark.createDataFrame([("00221771234567",)], ["msisdn"])
    spark_hash = df.select(hash_msisdn("msisdn")).first()[0]
    assert spark_hash == hash_value("+221771234567")


def test_sel_absent_leve_une_erreur(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PII_HASH_SALT")
    with pytest.raises(ValueError):
        hash_value("+221771234567")


def test_hash_value_none_donne_none() -> None:
    assert hash_value(None) is None


def test_hash_column_hache_et_garde_null(spark: SparkSession) -> None:
    df = spark.createDataFrame([("ABC-123",), (None,)], "imei string")
    rows = df.select(hash_column("imei").alias("h")).collect()
    assert rows[0]["h"] == hash_value("ABC-123")
    assert rows[1]["h"] is None
