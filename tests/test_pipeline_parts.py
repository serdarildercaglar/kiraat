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

