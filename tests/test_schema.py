"""Şema ile export'un birbirinden kopmaması.

`Pipeline.export`'un sabit anahtarları şemada olmalı; aşamaların ürettiği
her ölçüm şemada açıklanmış olmalı. Ölçüm anahtarları aşama kodundan değil,
aşamaların gerçekten yazdığı örnek çıktılardan alınır.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from kiraat import schema
from kiraat.stages.clip_qc import level_metrics

EXPORT_FIXED_KEYS = {
    "id", "audio", "channel", "source_id", "source_path", "source_sample_rate", "source_flags",
    "start", "end", "duration", "text_raw", "text", "text_spoken", "flags", "duplicate_of",
    "recommended", "exclusion_reasons", "policy_version",
}


def test_export_sabit_anahtarlari_semada():
    assert EXPORT_FIXED_KEYS <= set(schema.BY_NAME)


def test_sema_adlari_tekil_ve_sirali():
    names = schema.column_names()
    assert len(names) == len(set(names))
    assert names[0] == "id" and names[-1] == "policy_version"


def test_clip_qc_olcumleri_semada():
    assert set(level_metrics([0.0, 0.5, -0.5])) <= set(schema.BY_NAME)


def test_markdown_tablo_yerel_sutunlari_gizler():
    table = schema.markdown_table()
    assert "`source_path`" not in table and "`recommended`" in table
    assert "`source_path`" in schema.markdown_table(published_only=False)


def test_check_manifest_eksik_ve_fazlayi_bulur():
    row = {c.name: None for c in schema.COLUMNS if not c.optional}
    assert schema.check_manifest([row]) == (set(), set())
    del row["text"]
    row["surpriz"] = 1
    assert schema.check_manifest([row]) == ({"text"}, {"surpriz"})


SAMPLE = Path("work/sample-5c/manifests/clips.jsonl")


@pytest.mark.skipif(not SAMPLE.exists(), reason="örnek koşu manifestosu yok")
def test_ornek_kosu_manifestosu_semayla_uyusur():
    missing, unknown = schema.check_manifest_file(SAMPLE)
    assert not missing, f"şemada olup manifestoda olmayan: {sorted(missing)}"
    assert not unknown, f"manifestoda olup şemada olmayan: {sorted(unknown)}"
