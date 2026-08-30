"""Dağıtıcı: sıralı koşuyla özdeş çıktı, kanal bariyeri, hata ve yeniden koşu.

Sahte aşamalar `fake_stages` modülünde; gerçek adların yerine geçerler ve
işçi süreçlerine `Pipeline.worker_imports` ile taşınır.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from kiraat import base
from kiraat.config import Config
from kiraat.pipeline import Pipeline


@pytest.fixture(scope="module", autouse=True)
def sahte_asamalar():
    saved = dict(base._REGISTRY)
    import fake_stages  # noqa: F401  (kayıt: gerçek adların yerine)
    yield
    base._REGISTRY.clear()
    base._REGISTRY.update(saved)


def kaynaklar(tmp_path: Path) -> Path:
    raw = tmp_path / "raw"
    for ch, names in {"chA": ["a1", "a2", "a3"], "chB": ["b1", "b2", "bad"]}.items():
        (raw / ch).mkdir(parents=True)
        for n in names:
            (raw / ch / f"{n}.wav").write_bytes(b"0")
    return raw


def konfig(raw: Path, work: Path, **runtime) -> Config:
    return Config({
        "paths": {"raw_root": str(raw), "work_root": str(work), "db": str(work / "db" / "state.sqlite")},
        "sources": {"extensions": [".wav"]},
        "runtime": {"max_sources": 0, "source_workers": 2, "gpu_stage_concurrency": 1,
                    "gpu_batch_size": 3, "cpu_batch_size": 4, "parallel": True, **runtime},
        "boilerplate": {"min_recordings": 2, "min_ratio": 0.4, "min_words": 3, "max_words": 12,
                        "head_words": 80, "tail_words": 80},
        "segment": {"min_sec": 1.5, "target_sec": 7.0, "max_sec": 15.0},
        "align": {"enabled": True}, "text": {}, "dedupe": {"enabled": False},
        "recommended_subset": {"version": "t", "rules": [{"metric": "speech_ratio", "min": 0.5}]},
    })


def kos(cfg: Config, stages=None) -> Path:
    pipe = Pipeline(cfg)
    pipe.worker_imports = ("fake_stages",)
    try:
        return pipe.run(stages)
    finally:
        pipe.store.close()


def manifest(path: Path, root: Path) -> list[str]:
    return [line.replace(str(root), "<work>") for line in path.read_text(encoding="utf-8").splitlines()]


def olaylar(work: Path) -> list[dict]:
    p = work / "events.jsonl"
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines()] if p.exists() else []


def test_paralel_ve_sirali_ayni_manifestoyu_uretir(tmp_path):
    raw = kaynaklar(tmp_path)
    ws, wp = tmp_path / "serial", tmp_path / "par"
    out_s = kos(konfig(raw, ws, parallel=False))
    out_p = kos(konfig(raw, wp))
    ms, mp = manifest(out_s, ws), manifest(out_p, wp)
    assert ms == mp
    rows = [json.loads(l) for l in mp]
    assert len(rows) == 5 * 5                                   # 6 kaynak, biri bozuk → 5 × 5 klip
    assert all(r["text"].endswith("bp=1") for r in rows)        # künye kanalın tamamından madenlendi
    assert {r["channel"] for r in rows} == {"chA", "chB"}
    assert all("speech_ratio" in r and "music_to_speech_db" in r for r in rows)
    assert all(isinstance(r["recommended"], bool) for r in rows)


def test_kanal_bariyeri_ve_ust_uste_binme(tmp_path):
    raw = kaynaklar(tmp_path)
    work = tmp_path / "par"
    kos(konfig(raw, work))
    ev = olaylar(work)
    asr_done = {}
    for e in ev:
        if e["event"] == "asr":
            asr_done.setdefault(e["channel"], []).append(e["t"])
    starts = [e for e in ev if e["event"] == "segment_start"]
    assert len(starts) == 5
    for s in starts:                                            # bölütleme, kanalın bütün ASR'lerinden sonra
        assert s["t"] > max(asr_done[s["channel"]])
    # Bariyer kanal düzeyinde: chA'nın bölütlemesi chB'nin ASR'sini beklemek zorunda değil;
    # işler tek sırada gitmiyor — birden çok işçi süreç çalıştı.
    assert len({e["pid"] for e in ev}) >= 2
    # Bozuk kaynak: prepare hatası kayda yazıldı, ASR'ye gitmedi, bariyeri tıkamadı.
    from kiraat.store import Store
    st = Store(work / "db" / "state.sqlite")
    bad = [s for s in st.sources() if "bad" in s["path"]]
    st.close()
    assert len(bad) == 1 and bad[0]["error"].startswith("prepare:")
    assert not any(e["event"] == "asr" and e["src"] == bad[0]["id"] for e in ev)


def test_yeniden_kosu_is_yapmaz_ve_asama_alt_kumesi(tmp_path):
    raw = kaynaklar(tmp_path)
    work = tmp_path / "par"
    out1 = kos(konfig(raw, work))
    n1 = len(olaylar(work))
    out2 = kos(konfig(raw, work))
    assert len(olaylar(work)) == n1                             # her şey 'bitti', hiçbir aşama koşmadı
    assert manifest(out1, work) == manifest(out2, work)
    # Yalnızca klip aşaması + export: bölütleme bitmiş kaynakların klipleri
    # doğrudan kuyruğa girer; sürüm aynı olduğundan yine iş yok.
    kos(konfig(raw, work), stages=["music", "export"])
    assert len(olaylar(work)) == n1


def test_klip_isi_hatasi_kosuyu_durdurur_kaynak_hatasi_kayda_gecer(tmp_path):
    """Sonuç yazımı yolu: klip işi hatası yükselir (sıralı kodla aynı), kaynak
    işi hatası kayda `error` olarak yazılır ve koşu sürer."""
    from concurrent.futures import Future
    from kiraat.scheduler import Job, Scheduler

    raw = kaynaklar(tmp_path)
    pipe = Pipeline(konfig(raw, tmp_path / "par"))
    from kiraat.pipeline import discover_sources
    pipe.store.add_sources(discover_sources(pipe.cfg))
    sch = Scheduler(pipe, ["prepare", "clip_qc"], [])
    sch._build()
    fut: Future = Future()
    fut.set_exception(RuntimeError("olcum patladi"))
    job = Job("clip_qc", "1-0", "clips", [{"id": "x", "source_id": 1}])
    with pytest.raises(RuntimeError, match="olcum patladi"):
        sch._complete(job, fut)
    assert job.state == "failed"
    fut2: Future = Future()
    fut2.set_exception(RuntimeError("ffmpeg yok"))
    sch._complete(Job("prepare", "1", "source", 1), fut2)
    assert pipe.store.sources([1])[0]["error"] == "prepare: ffmpeg yok"
    pipe.store.close()


def _kaynak_id(work: Path, ad: str) -> int:
    from kiraat.store import Store
    st = Store(work / "db" / "state.sqlite")
    try:
        return [s["id"] for s in st.sources() if Path(s["path"]).stem == ad][0]
    finally:
        st.close()


def _hata_yaz(work: Path, ad: str) -> int:
    from kiraat.store import Store
    sid = _kaynak_id(work, ad)
    st = Store(work / "db" / "state.sqlite")
    try:
        st.update_source(sid, error="align: sonradan bozuldu")
    finally:
        st.close()
    return sid


def test_hatali_kaynagin_eski_klipleri_de_olculur(tmp_path, monkeypatch):
    """Klipleri üretildikten SONRA hata alan kaynak.

    Klipler depoda kalır ve `export` onları yazar, dolayısıyla ölçülmeleri
    gerekir — sıralı yol (`run_clip_stage`, kaynak süzgeci yok) ölçüyor.
    Dağıtıcı klip işlerini yalnız seçilmiş ve hatasız kaynaklardan kuruyordu;
    o klipler ölçüsüz manifestoya girip `eksik_olcum:*` ile önerilen alt
    kümeden sessizce düşüyordu. Mevcut testler bunu kaçırıyordu: tek bozuk
    kaynak `prepare`de düşüyor ve hiç klip üretmiyor.
    """
    import fake_stages

    raw = kaynaklar(tmp_path)
    ws, wp = tmp_path / "serial", tmp_path / "par"
    kos(konfig(raw, ws, parallel=False))
    kos(konfig(raw, wp))
    sid = _hata_yaz(ws, "a1")
    assert _hata_yaz(wp, "a1") == sid
    monkeypatch.setattr(fake_stages.FakeMusic, "version", "t2")
    out_s = kos(konfig(raw, ws, parallel=False))
    out_p = kos(konfig(raw, wp))
    assert manifest(out_s, ws) == manifest(out_p, wp)
    rows = [json.loads(l) for l in manifest(out_p, wp)]
    assert len([r for r in rows if r["source_id"] == sid]) == 5   # klipleri manifestoda duruyor
    # Asıl değişmez: koşu bitince depoda ölçülmemiş klip kalmaz. Manifest
    # değerine bakmak yetmez — sahte aşama belirlenimci olduğu için eski
    # ölçüm yerinde kalır ve iki yol yine aynı görünür.
    from kiraat.store import Store
    from kiraat.pipeline import stage_version
    from kiraat import base
    for w in (ws, wp):
        st = Store(w / "db" / "state.sqlite")
        try:
            for asama in ("clip_qc", "music"):
                v = stage_version(konfig(raw, w), base.get_stage(asama))
                assert not st.pending_clips(asama, v), (w.name, asama)
        finally:
            st.close()


def test_kunye_hatali_ama_asrsi_biten_kaydi_da_sayar(tmp_path, monkeypatch):
    """Künye kanalın tamamından madenlenir.

    `run_boilerplate` kabul ölçütünü kendi uyguluyor (kelime dosyası var mı);
    dağıtıcı ise kanal listesini hata süzgecinden geçiriyordu. chB'de iki
    kayıttan biri hata alınca eşik (`max(min_recordings, ...)`) tutmuyor,
    künye ifadesi madenlenmiyor ve klip metni iki yolda farklı çıkıyordu.
    """
    import fake_stages

    raw = kaynaklar(tmp_path)
    ws, wp = tmp_path / "serial", tmp_path / "par"
    kos(konfig(raw, ws, parallel=False))
    kos(konfig(raw, wp))
    sid = _hata_yaz(ws, "b2")
    assert _hata_yaz(wp, "b2") == sid
    monkeypatch.setattr(fake_stages.FakeSegment, "version", "t2")   # metin yeniden üretilsin
    out_s = kos(konfig(raw, ws, parallel=False))
    out_p = kos(konfig(raw, wp))
    assert manifest(out_s, ws) == manifest(out_p, wp)
    rows = [json.loads(l) for l in manifest(out_p, wp)]
    chb = [r for r in rows if r["channel"] == "chB" and r["source_id"] != sid]
    assert chb and all(r["text"].endswith("bp=1") for r in chb)


def test_dagitici_klip_kumesi_sirali_yolla_ayni(tmp_path, monkeypatch):
    """Dağıtıcının kuyruğa aldığı klip kümesi = sıralı yolun ölçeceği küme.

    Dağıtıcının 'sıralı koşuyla özdeş çıktı' iddiasının doğrudan sınanması.
    """
    import fake_stages
    from kiraat.scheduler import Scheduler

    raw = kaynaklar(tmp_path)
    work = tmp_path / "par"
    kos(konfig(raw, work))
    _hata_yaz(work, "a1")
    monkeypatch.setattr(fake_stages.FakeMusic, "version", "t2")
    pipe = Pipeline(konfig(raw, work))
    try:
        sch = Scheduler(pipe, ["music"], [s["id"] for s in pipe.store.sources()])
        sch._build()
        kuyrukta = {c["id"] for j in sch.jobs.values() if j.kind == "clips" for c in j.payload}
        bekleyen = {c["id"] for c in pipe.store.pending_clips("music", sch.versions["music"])}
        assert kuyrukta == bekleyen and bekleyen
    finally:
        pipe.store.close()
