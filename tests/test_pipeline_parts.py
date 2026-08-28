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

