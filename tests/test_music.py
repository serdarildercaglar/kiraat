import math

import pytest

from kiraat.stages.music import (INAUDIBLE_DB, has_background_music,
                                 music_to_speech_db, rms)


def tone(amp: float, n: int = 1000) -> list[float]:
    return [amp * math.sin(2 * math.pi * i / 32) for i in range(n)]


def test_rms_bos_dizi():
    assert rms([]) == 0.0


def test_muziksiz_klip_taban_deger_dondurur():
    assert music_to_speech_db(tone(0.5), [0.0] * 1000) == -80.0


def test_muzik_konusmanin_altindaysa_negatif():
    db = music_to_speech_db(tone(0.5), tone(0.05))
    assert db == pytest.approx(-20.0, abs=0.5)


def test_muzik_baskinsa_pozitif():
    assert music_to_speech_db(tone(0.05), tone(0.5)) > 0


def test_konusma_sessizse_muzik_baskin_sayilir():
    assert music_to_speech_db([0.0] * 1000, tone(0.5)) == 0.0


def test_taban_asilmaz():
    assert music_to_speech_db(tone(0.9), tone(1e-9)) == -80.0


def test_ikili_yanit_esikten_turetilir():
    # Yalnızca dB kuralı (audioset_min=None): eşik üstü var, altı yok.
    assert not has_background_music(-40.0, audioset_min=None)
    assert has_background_music(-10.0, audioset_min=None)
    assert not has_background_music(None, audioset_min=None)
    # Kullanici kendi esigini kesebilir.
    assert has_background_music(-40.0, threshold_db=-50.0, audioset_min=None)
    # Varsayılan: AudioSet kanıtı olmadan dB tek başına işaret üretmez.
    assert not has_background_music(-10.0)


def test_koddaki_varsayilanlar_konfigle_ayni():
    """Kodun varsayılanı konfigden sapmamalı. −30 dB kör dinlemeyle çürütülüp
    konfig −40'a çekilmişti ama modül varsayılanı −30'da kalmıştı: konfigde
    anahtar unutulsaydı hat çürütülmüş eşiği sessizce kullanacaktı."""
    from pathlib import Path

    from kiraat.config import Config
    from kiraat.stages.music import AUDIOSET_MIN, AUDIOSET_MUSIC_LABELS, SEPARATOR_SCREEN

    music = Config.load(Path(__file__).resolve().parents[1] / "configs/default.yaml").section("music")
    assert INAUDIBLE_DB == music["inaudible_db"]
    assert AUDIOSET_MIN == music["audioset_min"]
    assert SEPARATOR_SCREEN == music["separator_screen"]
    assert list(AUDIOSET_MUSIC_LABELS) == list(music["audioset_labels"])


def test_isaret_db_ve_audioset_birlikte_ister():
    # dB tek başına yetmez: AudioSet kanıtı yoksa (oda tınısı) işaret yok
    assert not has_background_music(-10.0, audioset=0.10, audioset_min=0.3)
    assert has_background_music(-10.0, audioset=0.55, audioset_min=0.3)
    # AudioSet yüksek ama dB eşiğin altında: duyulmuyor, işaret yok
    assert not has_background_music(-45.0, audioset=0.9, audioset_min=0.3)
    # audioset_min=None yalnızca dB kuralı
    assert has_background_music(-10.0, audioset=0.0, audioset_min=None)


def test_okunamayan_klip_kosuyu_durdurmaz(tmp_path):
    """Okunamayan seste `music` koşuyu HATA ile düşürüyordu (31 Ağu incelemesi,
    ertelenen b maddesi): clip_qc işaretler, dnsmos boş bırakır, music
    durdururdu. Sözleşme artık dnsmos ile aynı — ölçümler boş kalır, işaret
    verilmez (`unreadable_audio` sahibi clip_qc), koşu sürer."""
    import math as _math
    from concurrent.futures import ThreadPoolExecutor
    from pathlib import Path

    import numpy as np
    import soundfile as sf

    from kiraat.config import Config
    from kiraat.stages.music import MusicStage

    good = tmp_path / "good.flac"
    sf.write(good, np.array([0.1 * _math.sin(i / 5.0) for i in range(2400)],
                            dtype="float32"), 24000)
    bad = tmp_path / "bad.flac"
    bad.write_bytes(b"bu bir flac degil")

    class FakeMeasurer:
        def prepare(self, wave, sr):
            return {"wave": wave, "sr": sr}

        def measure_prepared(self, prepared):
            return {"music_score_audioset": 0.0, "music_to_speech_db": -80.0,
                    "music_db_separated": False}

    cfg = Config.load(Path(__file__).resolve().parents[1] / "configs/default.yaml")
    stage = MusicStage(cfg)
    stage.measurer = FakeMeasurer()
    stage.prefetch = ThreadPoolExecutor(2)
    try:
        rows = stage.process_clips([
            {"id": "c1", "audio": str(bad)},
            {"id": "c2", "audio": str(good)},
        ])
    finally:
        stage.prefetch.shutdown(wait=True)

    by_id = {row["id"]: row for row in rows}
    assert by_id["c1"]["metrics"] == {}
    assert by_id["c1"]["flags"] == []
    assert by_id["c2"]["metrics"]["music_to_speech_db"] == -80.0


def test_pencereler_klibin_kuyrugunu_da_olcer():
    """5 Eyl 2026 gerilemesi: `range(0, n - window + 1, hop)` klibin sonunu
    dışarıda bırakıyordu. 15 s'lik klipte tek pencere çıkıyor (76.161 <
    80.000) ve son 4,76 s hiç ölçülmüyordu; skor pencereler üzerinden azami
    alındığı için yalnızca kuyrukta duyulan müzik görünmez oluyordu."""
    from kiraat.stages.music import MusicMeasurer

    m = MusicMeasurer()
    window = int(m.window_sec * 16000)
    for saniye in (10.5, 12.0, 15.0, 17.3, 30.0, 121.0):
        n = int(saniye * 16000)
        starts = m.window_starts(n)
        assert starts[0] == 0
        assert all(0 <= s <= n - window for s in starts)
        assert starts == sorted(set(starts))
        # Kuyruk dışarıda kalmaz: son pencere sesin sonuna dayanır.
        assert starts[-1] + window == n, f"{saniye} s: kuyruk ölçülmüyor"


def test_pencereden_kisa_klipte_dizi_degismedi():
    """Kliplerin %93,4'ü penceresinden kısa; onlarda eski ve yeni dilimleme
    örnek örnek özdeş olmalı, yoksa v4 kayıtlarının sürüm göçü geçersizdir."""
    from kiraat.stages.music import MusicMeasurer

    m = MusicMeasurer()
    window, hop = int(m.window_sec * 16000), int(m.hop_sec * 16000)
    for saniye in (0.5, 1.5, 5.0, 7.0, 10.24):
        n = int(saniye * 16000)
        eski = list(range(0, max(n - window, 0) + 1, hop))
        assert m.window_starts(n) == eski == [0]
