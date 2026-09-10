"""Yayın şeması: sütunlar kiraat şemasından türer, ikisi ayrışamaz."""

import json

from kiraat import schema
from kiraat.hf import SPLITS, features, published_columns, storage_features, to_row


def test_sutunlar_semadan_turer_ve_source_path_yayimlanmaz():
    adlar = [c.name for c in published_columns()]
    assert "source_path" not in adlar, "ham dosya yolu yayımlanmaz"
    assert set(adlar) | {"source_path"} == {c.name for c in schema.COLUMNS}
    f = features()
    assert set(f) == set(adlar) | {"split"}


def test_her_sema_tipinin_karsiligi_var():
    """Şemaya yeni tipte bir sütun eklenirse burada patlasın, yayında değil."""
    for col in published_columns():
        assert col.dtype in {"audio", "string", "int", "float", "bool",
                             "list[string]", "dict[string,float]"}, col


def test_satir_donusumu():
    clip = {"id": "src00007-00042", "audio": "work/x/00042.flac", "source_id": 7,
            "channel": "kanal", "duration": 5.5, "text": "Bir cümle.",
            "flags": ["short"], "recommended": False,
            "music_stem_db": {"drums": -40.0, "bass": -50.0}}
    row = to_row(clip, "train")
    assert row["split"] == "train"
    assert row["audio"] == {"bytes": None, "path": "work/x/00042.flac"}
    assert row["source_id"] == "src00007"        # kayıt kimliği dize
    assert json.loads(row["music_stem_db"])["drums"] == -40.0
    assert row["dnsmos_ovrl"] is None            # eksik ölçüm boş kalır
    assert row["flags"] == ["short"]


def test_source_id_yayimda_dize():
    """Şemada int (veritabanı sayacı), yayımda kayıt kimliği dizesi."""
    from datasets import Value
    assert features()["source_id"] == Value("string")


def test_depolama_semasinda_ses_bayt():
    st = storage_features()
    assert set(st["audio"]) == {"bytes", "path"}
    assert SPLITS == ("train", "dev", "test", "rest"), \
        "rest bölmesi olmadan korpusun bir kısmı yayımlanmaz"


def test_kart_yayimlanan_her_sutunu_belgeler():
    """Kart, yayımlanan sütunların tam listesini taşır — biri eklenip kartta
    unutulursa burada patlar. Kartı ilk yazarken `audio`, `source_id` ve
    `split` tabloda yoktu; verinin kendisi belgesiz kalmıştı."""
    import re
    from pathlib import Path

    kart = Path(__file__).resolve().parents[1] / "docs" / "DATASET_CARD.md"
    govde = kart.read_text(encoding="utf-8").split("## Columns", 1)[1]
    govde = govde.split("## Known limitations")[0]
    belgeli = set(re.findall(r"^\| `([a-z_]+)`", govde, re.M))
    assert belgeli == {c.name for c in published_columns()} | {"split"}


def test_kart_yayimlanan_her_bolmeyi_anar():
    """`rest` bölmesi kartta yoksa okur 316.733 klibi kayıp sayar."""
    from pathlib import Path

    kart = (Path(__file__).resolve().parents[1] / "docs" / "DATASET_CARD.md")
    metin = kart.read_text(encoding="utf-8")
    for bolme in SPLITS:
        assert f"`{bolme}`" in metin, f"{bolme} bölmesi kartta anılmıyor"
        assert f"path: data/{bolme}-*" in metin, f"{bolme} configs bloğunda yok"
