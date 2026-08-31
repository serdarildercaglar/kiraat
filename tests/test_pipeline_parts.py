from pathlib import Path

import numpy as np

from kiraat.stages.asr import whisper_name
from kiraat.stages.clip_qc import level_metrics, speech_metrics
from kiraat.store import Store


def test_whisper_adi():
    assert whisper_name("openai/whisper-large-v3") == "large-v3"
    assert whisper_name("large-v3-turbo") == "large-v3-turbo"


def test_seviye_ve_konusma_olcumleri():
    wave = np.zeros(24000, dtype=np.float32)
    wave[1000:2000] = 1.0
    m = level_metrics(wave)
    assert abs(m["clip_ratio"] - 1000 / 24000) < 1e-4 and m["peak_dbfs"] == 0.0
    s = speech_metrics([{"start": 0.2, "end": 1.0}, {"start": 2.5, "end": 3.0}], 3.5)
    assert abs(s["speech_ratio"] - 1.3 / 3.5) < 1e-3
    assert s["internal_silence_sec"] == 1.5 and s["leading_silence_sec"] == 0.2 and s["trailing_silence_sec"] == 0.5


def test_ses_yuksekligi_lufs():
    from kiraat.stages.clip_qc import loudness_lufs

    sr = 24000
    rng = np.random.default_rng(0)
    wave = (rng.standard_normal(2 * sr) * 0.1).astype("float32")
    val = loudness_lufs(wave, sr)
    assert val is not None and -30.0 < val < -10.0
    # 20 dB kazanç farkı ≈ 20 LU (BS.1770 doğrusal kazançta LU kaydırır).
    quiet = loudness_lufs((wave * 0.1).astype("float32"), sr)
    assert quiet is not None and abs((val - quiet) - 20.0) < 1.0
    # Tanımsız durumlar: sessizlik (−inf) ve 0,4 s bloğundan kısa klip.
    assert loudness_lufs(np.zeros(2 * sr, dtype="float32"), sr) is None
    assert loudness_lufs(wave[: int(0.3 * sr)], sr) is None


def test_store_gidis_donus(tmp_path):
    st = Store(tmp_path / "db.sqlite")
    assert st.add_sources([{"path": "/a.m4a", "channel": "k", "ext": ".m4a", "bytes": 1}]) == 1
    assert st.add_sources([{"path": "/a.m4a", "channel": "k"}]) == 0
    sid = st.sources()[0]["id"]
    st.update_source(sid, duration=12.5, meta={"words": "/w.jsonl"})
    assert st.sources([sid])[0]["meta"]["words"] == "/w.jsonl"
    st.replace_clips(sid, [{"id": "c1", "idx": 0, "channel": "k", "start": 0.0, "end": 2.0, "duration": 2.0,
                            "text": "Merhaba.", "flags": ["short"], "metrics": {"n_words": 1}}])
    assert not st.is_done("clip", "c1", "clip_qc", "1")
    assert [c["id"] for c in st.pending_clips("clip_qc", "1")] == ["c1"]
    st.merge_clip_results([{"id": "c1", "metrics": {"speech_ratio": 0.9}, "flags": ["x"]}])
    st.mark_done("clip", "c1", "clip_qc", "1")
    c = st.clips(sid)[0]
    assert c["metrics"] == {"n_words": 1, "speech_ratio": 0.9} and c["flags"] == ["short", "x"]
    assert st.pending_clips("clip_qc", "1") == []
    assert st.pending_clips("clip_qc", "2") != []   # sürüm değişince yeniden yapılır
    # Kaynak yeniden bölütlenince aynı kimlikli yeni klipler yeniden ölçülmeli.
    st.replace_clips(sid, [{"id": "c1", "idx": 0, "channel": "k", "start": 0.0, "end": 3.0, "duration": 3.0,
                            "text": "Merhaba dünya.", "flags": [], "metrics": {}}])
    assert [c["id"] for c in st.pending_clips("clip_qc", "1")] == ["c1"]


def test_kaynak_kesfi_kanal_donusumlu(tmp_path):
    from kiraat.config import Config
    from kiraat.pipeline import discover_sources

    for ch, files in {"b_kanal": ["x.m4a", "y.m4a"], "A_kanal": ["p.mp3"], "c": ["q.wav", "r.txt"]}.items():
        (tmp_path / ch).mkdir()
        for f in files:
            (tmp_path / ch / f).write_bytes(b"0")
    cfg = Config({"paths": {"raw_root": str(tmp_path)},
                  "sources": {"extensions": [".m4a", ".mp3", ".wav"], "exclude_patterns": []},
                  "runtime": {"max_sources": 3}})
    picked = discover_sources(cfg)
    # Kanallar büyük/küçük harfe bakılmadan sıralı ve her kanal sırayla bir kayıt verir.
    assert [s["channel"] for s in picked] == ["A_kanal", "b_kanal", "c"]
    cfg0 = Config({**cfg.data, "runtime": {"max_sources": 0}})
    assert len(discover_sources(cfg0)) == 4


def test_kanal_siniri(tmp_path):
    from kiraat.config import Config
    from kiraat.pipeline import discover_sources

    for ch in ("a", "b", "c"):
        (tmp_path / ch).mkdir()
        for i in range(3):
            (tmp_path / ch / f"{i}.wav").write_bytes(b"0")
    cfg = Config({"paths": {"raw_root": str(tmp_path)}, "sources": {"extensions": [".wav"]},
                  "runtime": {"max_sources": 4, "max_channels": 2}})
    picked = discover_sources(cfg)
    assert [s["channel"] for s in picked] == ["a", "b", "a", "b"]


def test_kesik_kaynak_isareti(tmp_path):
    import numpy as np
    import soundfile as sf
    from kiraat.config import Config
    from kiraat.stages.prepare import PrepareStage

    src = tmp_path / "k" / "x.wav"
    src.parent.mkdir()
    sf.write(str(src), np.zeros(24000 * 2, dtype="float32"), 24000)
    cfg = Config({"paths": {"work_root": str(tmp_path / "work")}, "prepare": {"target_sr": 24000}})
    row = PrepareStage(cfg).process_source({"id": 1, "path": str(src)})[0]
    assert abs(row["duration"] - 2.0) < 0.05 and "source_flags" not in row


def test_tohumlu_rastgele_orneklem(tmp_path):
    from kiraat.config import Config
    from kiraat.pipeline import discover_sources

    for ch in "abcdef":
        (tmp_path / ch).mkdir()
        for i in range(4):
            (tmp_path / ch / f"{i}.wav").write_bytes(b"0")
    base = {"paths": {"raw_root": str(tmp_path)}, "sources": {"extensions": [".wav"]}}
    a = discover_sources(Config({**base, "runtime": {"max_sources": 6, "max_channels": 2, "sample_seed": 7}}))
    b = discover_sources(Config({**base, "runtime": {"max_sources": 6, "max_channels": 2, "sample_seed": 7}}))
    c = discover_sources(Config({**base, "runtime": {"max_sources": 6, "max_channels": 2, "sample_seed": 8}}))
    assert a == b                                   # aynı tohum, aynı örneklem
    assert len(a) == 6 and len({s["channel"] for s in a}) == 2   # 2 kanal × 3 kayıt
    assert a != c or [s["channel"] for s in a] != [s["channel"] for s in c]


def test_hizalama_parcalama():
    from kiraat.stages.align import make_chunks

    # 0,5 s'lik kelimeler, her 10 kelimede 0,4 s boşluk; 100 kelime ≈ 54 s
    words, t = [], 0.0
    for i in range(100):
        words.append({"text": f"k{i}", "start": round(t, 2), "end": round(t + 0.5, 2)})
        t += 0.5 + (0.4 if i % 10 == 9 else 0.0)
    chunks = make_chunks(words, target_sec=20.0, max_sec=40.0, min_gap_sec=0.3, pad_sec=0.5)
    assert [c.a for c in chunks][0] == 0 and chunks[-1].b == 100
    for a, b in zip(chunks, chunks[1:]):
        assert a.b == b.a                                   # boşluksuz, örtüşmesiz kelime kapsamı
        assert words[a.b]["start"] - words[a.b - 1]["end"] >= 0.3   # kesim boşlukta
    assert all(20.0 <= (words[c.b - 1]["end"] - words[c.a]["start"]) <= 40.0 for c in chunks[:-1])
    assert chunks[0].start == 0.0 and chunks[0].end == words[chunks[0].b - 1]["end"] + 0.5


def test_asama_surumu_konfigle_degisir():
    from kiraat.config import Config
    from kiraat.pipeline import stage_version
    from kiraat.stages.segmentation import SegmentStage

    base = {"segment": {"min_sec": 2.5, "target_sec": 7.0, "max_sec": 15.0}, "align": {"enabled": True}, "text": {}}
    a = stage_version(Config(base), SegmentStage(Config(base)))
    b = stage_version(Config({**base, "segment": {**base["segment"], "min_sec": 1.5}}), SegmentStage(Config(base)))
    c = stage_version(Config({**base, "music": {"x": 1}}), SegmentStage(Config(base)))
    assert a != b and a == c and a.startswith(SegmentStage.version + "+")



def test_prepare_sinirlayici_istege_bagli_ve_varsayilan_kapali():
    """Sınırlayıcı açıkken `clip_ratio` kaynağın kırpılmasını değil hattın
    kendi tavanını ölçüyordu; varsayılan kapalı, açılırsa `level=false`."""
    from kiraat.stages.prepare import ffmpeg_filters

    kapali = ffmpeg_filters({"highpass_hz": 40.0, "peak_ceiling_db": None})
    assert kapali == ["highpass=f=40.0"]
    assert ffmpeg_filters({"highpass_hz": 40.0}) == ["highpass=f=40.0"]

    filters = ffmpeg_filters({"highpass_hz": 40.0, "peak_ceiling_db": -1.0})
    lim = [f for f in filters if f.startswith("alimiter")][0]
    assert "level=false" in lim and "limit=0.8913" in lim
    assert filters[0] == "highpass=f=40.0"


def test_varsayilan_konfigde_tepe_sinirlayici_yok():
    """Politikadaki `clip_ratio` kuralının ölü olmaması buna bağlı."""
    from kiraat.config import Config
    from kiraat.stages.prepare import ffmpeg_filters

    opts = Config.load(Path(__file__).resolve().parents[1] / "configs/default.yaml").section("prepare")
    assert opts["peak_ceiling_db"] is None
    assert not any(f.startswith("alimiter") for f in ffmpeg_filters(opts))


def test_saat_butcesi_alt_sinir(tmp_path):
    from kiraat.config import Config
    from kiraat.pipeline import discover_sources

    for ch, files in {"a": ["1.m4a", "2.m4a"], "b": ["3.m4a", "4.m4a"]}.items():
        (tmp_path / ch).mkdir()
        for f in files:
            (tmp_path / ch / f).write_bytes(b"0")
    cfg = Config({"paths": {"raw_root": str(tmp_path)},
                  "sources": {"extensions": [".m4a"], "exclude_patterns": []},
                  "runtime": {"max_sources": 0, "max_hours": 1.0}})
    # her kayıt 40 dk: 1 saat bütçesi ikinci kayıtla aşılır ve orada durur (alt sınır)
    picked = discover_sources(cfg, duration_of=lambda p: 2400.0)
    assert [s["path"].rsplit("/", 1)[-1] for s in picked] == ["1.m4a", "3.m4a"]
    # bütçe sıfırsa sınırsız
    cfg0 = Config({**cfg.data, "runtime": {"max_sources": 0, "max_hours": 0}})
    assert len(discover_sources(cfg0, duration_of=lambda p: 2400.0)) == 4


def test_kanal_basina_kayit_ve_dakika_tavani(tmp_path):
    from kiraat.config import Config
    from kiraat.pipeline import discover_sources

    for ch in ("a", "b", "c"):
        (tmp_path / ch).mkdir()
        for i in range(5):
            (tmp_path / ch / f"{i}.m4a").write_bytes(b"0")
    base = {"paths": {"raw_root": str(tmp_path)}, "sources": {"extensions": [".m4a"]}}
    # kanal başına 2 kayıt: 3 kanal × 2 = 6, dönüşümlü sırayla
    picked = discover_sources(Config({**base, "runtime": {"max_sources": 0, "max_sources_per_channel": 2}}))
    assert [s["channel"] for s in picked] == ["a", "b", "c", "a", "b", "c"]
    # saat bütçesi kesilmiş süreyle sayılır: her kayıt 2 saat ama tavan 20 dk →
    # 1 saat bütçesi 3. kayıtta dolar (alt sınır), tavansız olsaydı 1. kayıtta dolardı
    cfg = Config({**base, "runtime": {"max_sources": 0, "max_hours": 1.0}, "prepare": {"max_minutes": 20}})
    assert len(discover_sources(cfg, duration_of=lambda p: 7200.0)) == 3
    cfg0 = Config({**base, "runtime": {"max_sources": 0, "max_hours": 1.0}})
    assert len(discover_sources(cfg0, duration_of=lambda p: 7200.0)) == 1


def test_prepare_dakika_tavani(tmp_path):
    import numpy as np
    import soundfile as sf
    from kiraat.config import Config
    from kiraat.stages.prepare import PrepareStage

    src = tmp_path / "k" / "x.wav"
    src.parent.mkdir()
    sf.write(str(src), np.zeros(24000 * 6, dtype="float32"), 24000)   # 6 s
    cfg = Config({"paths": {"work_root": str(tmp_path / "work")}, "prepare": {"target_sr": 24000, "max_minutes": 4 / 60}})
    row = PrepareStage(cfg).process_source({"id": 1, "path": str(src)})[0]
    # 4 s'de kesildi; kapsayıcı süresi korunur, kesik-indirme işareti verilmez
    assert abs(row["duration"] - 4.0) < 0.05 and abs(row["container_duration"] - 6.0) < 0.05
    assert row["cap_sec"] == 4.0 and "source_flags" not in row


def test_asama_yeniden_kosunca_sahipli_anahtarlar_silinir(tmp_path):
    from kiraat.store import Store

    st = Store(tmp_path / "s.sqlite")
    sid = st.add_sources([{"path": "/x/a.m4a", "channel": "k", "ext": ".m4a", "bytes": 1}]) and 1
    st.replace_clips(sid, [{"id": "c1", "idx": 0, "channel": "k", "start": 0.0, "end": 2.0, "duration": 2.0,
                            "text": "Merhaba.", "flags": [], "metrics": {}}])
    st.merge_clip_results([{"id": "c1", "metrics": {"music_to_speech_db": -10.0, "music_prob_external": 0.9, "speech_ratio": 0.8},
                            "flags": ["background_music", "short"]}])
    # müzik aşaması yeniden koşuyor: dış model kapalı, işaret yok
    st.merge_clip_results([{"id": "c1", "metrics": {"music_to_speech_db": -50.0}, "flags": []}],
                          owned_metrics=("music_to_speech_db", "music_prob_external"), owned_flags=("background_music",))
    c = st.clips()[0]
    assert c["metrics"] == {"speech_ratio": 0.8, "music_to_speech_db": -50.0}   # hayalet anahtar yok, başka aşamanınki duruyor
    assert c["flags"] == ["short"]                                             # sahipli işaret düştü, başkası kaldı


# --------------------------------------------------------------- sürüm zinciri
def _cfg_ile(**bolumler):
    from kiraat.config import Config
    cfg = Config.load(Path(__file__).resolve().parents[1] / "configs/default.yaml")
    data = {k: (dict(v) if isinstance(v, dict) else v) for k, v in cfg.data.items()}
    for ad, degisiklik in bolumler.items():
        data[ad] = {**data[ad], **degisiklik}
    return Config(data)


def _surumler(cfg):
    from kiraat import base
    from kiraat.pipeline import stage_version
    from kiraat.stages import align, asr, clip_qc, music, prepare, segmentation  # noqa: F401
    return {n: stage_version(cfg, base.get_stage(n))
            for n in ("prepare", "asr", "align", "boilerplate", "segment", "clip_qc", "music")}


def test_ust_akis_kod_surumu_alt_akisi_eskitir(monkeypatch):
    """align kod sürümü değişince align_score'u klibe yazan segment de eskimeli.

    29 Ağu 2026: `AlignStage.version` 1→2 yapıldı (skorları yarıya bölen hata)
    ama `segment`in sürümü değişmediği için artımlı yeniden koşuda düzeltme
    manifestoya hiç ulaşmıyordu.
    """
    from kiraat.stages.align import AlignStage

    cfg = _cfg_ile()
    once = _surumler(cfg)
    monkeypatch.setattr(AlignStage, "version", AlignStage.version + "x")
    sonra = _surumler(cfg)
    assert [n for n in once if once[n] != sonra[n]] == ["align", "segment", "clip_qc", "music"]


def test_vad_bolumu_asr_ve_clip_qc_surumune_giriyor():
    """İkisi de cfg.section('vad') okuyor; eşik değişince yeniden koşmalılar."""
    once = _surumler(_cfg_ile())
    sonra = _surumler(_cfg_ile(vad={"threshold": 0.40}))
    degisen = {n for n in once if once[n] != sonra[n]}
    assert {"asr", "clip_qc"} <= degisen
    assert "prepare" not in degisen


def test_yalnizca_basarim_ayari_surumu_degistirmez():
    once = _surumler(_cfg_ile())
    sonra = _surumler(_cfg_ile(prepare={"ffmpeg_threads": 8}))
    assert once == sonra


def test_hizalayici_guven_kaynagi_yeniden_hizalama_gerektirmez():
    """`confidence_source`u yalnızca segment okur; align sürümü sabit kalmalı,
    yoksa tercih değişince 3.400 saat boşuna yeniden hizalanır."""
    once = _surumler(_cfg_ile())
    sonra = _surumler(_cfg_ile(align={"confidence_source": "align"}))
    assert once["align"] == sonra["align"]
    assert once["segment"] != sonra["segment"]


def test_sayi_bicimi_surumu_degistirmez():
    """CLI --max-minutes 20 float, YAML 20 int verir; aynı anlam aynı özet."""
    assert _surumler(_cfg_ile(prepare={"max_minutes": 20}))["prepare"] == \
           _surumler(_cfg_ile(prepare={"max_minutes": 20.0}))["prepare"]


def test_boilerplate_sozde_asamasi_zincirde():
    """`segment` künyeye bağlı; künye de ASR'ye. Sürümü kanalın 'bitti'
    kaydına yazılan dizgedir, elle yazılmış '1' değil."""
    from kiraat import base
    from kiraat.pipeline import stage_version

    once = _surumler(_cfg_ile())
    assert once["boilerplate"].startswith("1+")
    sonra = _surumler(_cfg_ile(boilerplate={"min_ratio": 0.9}))
    assert once["boilerplate"] != sonra["boilerplate"]
    assert once["segment"] != sonra["segment"]
    assert stage_version(_cfg_ile(), base.get_stage("boilerplate")) == once["boilerplate"]


def test_runtime_bolumu_surume_giremez():
    """İşçi konfigi runtime'ı değiştiriyor; sürüm süreçler arası kararsız olurdu."""
    import pytest
    from kiraat.base import SourceStage, _REGISTRY, register
    from kiraat.pipeline import stage_version

    saved = dict(_REGISTRY)
    try:
        @register
        class _Kotu(SourceStage):
            name = "_kotu"
            config_sections = ("runtime",)

            def process_source(self, source):
                return []

        with pytest.raises(ValueError, match="surume giremez"):
            stage_version(_cfg_ile(), _Kotu)
    finally:
        _REGISTRY.clear()
        _REGISTRY.update(saved)


def test_surum_dongusu_hata_verir():
    import pytest
    from kiraat.base import SourceStage, _REGISTRY, register
    from kiraat.pipeline import stage_version

    saved = dict(_REGISTRY)
    try:
        @register
        class _A(SourceStage):
            name = "_a"
            depends_on = ("_b",)

            def process_source(self, source):
                return []

        @register
        class _B(SourceStage):
            name = "_b"
            depends_on = ("_a",)

            def process_source(self, source):
                return []

        with pytest.raises(ValueError, match="dongu"):
            stage_version(_cfg_ile(), _A)
    finally:
        _REGISTRY.clear()
        _REGISTRY.update(saved)


# ------------------------------------------------------------------ köken
def test_kosu_kaydi_kodu_konfigi_ve_agirliklari_kimliklendiriyor():
    """Yayımlanan manifest kendisini üreten şeye bağlanabilmeli.

    Aksi hâlde 'ölçüm karardan ayrı, politika sürümlü ve yeniden koşulabilir'
    iddiası gösterilemez: manifest hangi commit, hangi eşikler ve hangi model
    ağırlıklarıyla üretildiğini taşımaz ve koşudan sonra bu yeniden kurulamaz.
    """
    from kiraat.config import Config
    from kiraat.provenance import run_record

    cfg = Config.load(Path(__file__).resolve().parents[1] / "configs/default.yaml")
    rec = run_record(cfg, {"prepare": "6+abc"}, {"clips": 3})
    assert set(rec) >= {"created", "git", "stage_versions", "policy_version",
                        "models", "packages", "counts", "config"}
    # Konfigin tamamı kayıtta: eşikler koda gömülü olmadığı için koşu ancak
    # bununla yeniden kurulabilir.
    assert rec["config"] == cfg.data
    assert rec["policy_version"] == str(cfg.get("recommended_subset.version"))
    # Hattın çıktısını belirleyen her paket çözülmüş olmalı.
    assert all(v for v in rec["packages"].values()), rec["packages"]
    # Her ağırlık ya kendi revizyonuyla ya da bir paket sürümüyle sabit.
    for ad, m in rec["models"].items():
        assert m.get("revision") or m.get("pinned_by"), ad
    assert rec["models"]["asr"]["revision"] == cfg.get("asr.revision")
    assert rec["models"]["audioset"]["revision"] == cfg.get("music.audioset_revision")


def test_konfigde_hf_agirliklari_sabitlenmis():
    """HF'den çekilen iki ağırlık commit'e sabitli olmalı; olmazsa depo
    güncellendiğinde bütün sayılar sessizce değişir."""
    from kiraat.config import Config

    cfg = Config.load(Path(__file__).resolve().parents[1] / "configs/default.yaml")
    for anahtar in ("asr.revision", "music.audioset_revision"):
        v = cfg.get(anahtar)
        assert isinstance(v, str) and len(v) == 40 and all(c in "0123456789abcdef" for c in v), (anahtar, v)


def test_hizalama_penceresi_tam_dosyayi_yeniden_orneklemekle_ayni(tmp_path):
    """`WindowReader` parçayı diskten okuyup yeniden örnekliyor; sonuç, kaydın
    tamamını yeniden örnekleyip dilimlemekle aynı örnekleri vermeli. Aynı
    olmasaydı hizalama damgaları kayıt uzunluğuna göre değişirdi."""
    import numpy as np
    import soundfile as sf
    import torch
    import torchaudio

    from kiraat.stages.align import WindowReader

    sr, hedef = 24000, 16000
    wave = (np.random.default_rng(5).standard_normal(sr * 90) * 0.2).astype(np.float32)
    path = tmp_path / "kayit.flac"
    sf.write(str(path), wave, sr, format="FLAC", subtype="PCM_16")
    okunan, _ = sf.read(str(path), dtype="float32")
    tam = torchaudio.functional.resample(torch.from_numpy(okunan), sr, hedef).numpy()

    rd = WindowReader(str(path), hedef)
    for a0, a1 in [(0, 5 * hedef), (7 * hedef, 37 * hedef), (61 * hedef + 13, 89 * hedef),
                   (88 * hedef, 95 * hedef)]:
        pencere = rd.window(a0, a1)
        beklenen = tam[a0:a1]
        assert len(pencere) == len(beklenen), (a0, a1, len(pencere), len(beklenen))
        assert np.array_equal(pencere, beklenen), (a0, a1, float(np.abs(pencere - beklenen).max()))


def test_bolutleme_kaydin_tamamini_bellege_almaz(tmp_path):
    """Korpusun %31'i dört saatten uzun tek parça kayıtlarda; bölütleme o
    kayıtta da kaydın boyutundan bağımsız bellekle çalışmalı."""
    import json
    import tracemalloc

    import numpy as np
    import soundfile as sf

    from kiraat.config import Config
    from kiraat.stages.segmentation import SegmentStage

    sr, dakika = 24000, 10
    rng = np.random.default_rng(11)
    wave = (rng.standard_normal(sr * 60 * dakika) * 0.002).astype(np.float32)
    words, t = [], 0.4
    while t < 60 * dakika - 2:
        text = f"kelime{len(words)}" + ("." if len(words) % 12 == 11 else "")
        i, j = int(t * sr), int((t + 0.45) * sr)
        wave[i:j] = rng.standard_normal(j - i) * 0.25
        words.append({"text": text.capitalize() if not words or words[-1]["text"].endswith(".") else text,
                      "start": round(t, 3), "end": round(t + 0.45, 3), "prob": 0.9})
        t += 0.45 + (0.35 if text.endswith(".") else 0.05)

    (tmp_path / "audio").mkdir()
    (tmp_path / "asr").mkdir()
    audio = tmp_path / "audio" / "src00001.flac"
    sf.write(str(audio), wave, sr, format="FLAC", subtype="PCM_16")
    asr = tmp_path / "asr" / "src00001.jsonl"
    asr.write_text("\n".join(json.dumps(w, ensure_ascii=False) for w in words), encoding="utf-8")

    cfg = Config({"paths": {"work_root": str(tmp_path)},
                  "segment": {"min_sec": 1.5, "target_sec": 7.0, "max_sec": 15.0,
                              "max_join_gap_sec": 1.2, "lead_pad_sec": 0.15, "trail_pad_sec": 0.25},
                  "align": {"enabled": False}, "text": {"emit_raw": True, "emit_spoken": True}})
    stage = SegmentStage(cfg)
    kaynak = {"id": 1, "channel": "kanal", "audio": str(audio), "words": str(asr)}
    tracemalloc.start()
    try:
        tracemalloc.reset_peak()
        rows = stage.process_source(kaynak)
        zirve = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    assert rows and all(r["duration"] > 0 for r in rows)
    ses_mb = wave.nbytes / 1e6
    assert zirve < 64 << 20, f"{dakika} dakikalık kayıtta zirve {zirve/1e6:.0f} MB (ses {ses_mb:.0f} MB)"


def test_kuru_kosu_okunamayan_dosyada_dusmez(tmp_path, capsys):
    """Ham kökte sıfır baytlık ya da bozuk indirme olabiliyor (30 Ağu 2026'da
    bir tane vardı) ve uzantı listesi genişledikçe olasılığı artıyor. Kuru
    koşu bunda çökmemeli, dosyayı adıyla bildirmeli."""
    import numpy as np
    import soundfile as sf

    from kiraat.__main__ import dry_run
    from kiraat.config import Config

    (tmp_path / "kanal").mkdir()
    sf.write(str(tmp_path / "kanal" / "saglam.wav"),
             np.zeros(16000, dtype="float32"), 16000)
    (tmp_path / "kanal" / "bozuk.m4a").write_bytes(b"")

    cfg = Config({"paths": {"raw_root": str(tmp_path)},
                  "sources": {"extensions": [".wav", ".m4a"], "exclude_patterns": []},
                  "runtime": {"max_sources": 0}, "prepare": {"max_minutes": 0}})
    assert dry_run(cfg) == 0
    out = capsys.readouterr().out
    assert "bozuk.m4a" in out and "okunamayan 1 dosya" in out
    assert "toplam: 2 kaynak" in out
