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
    assert INAUDIBLE_DB == -30.0


def test_isaret_db_ve_audioset_birlikte_ister():
    # dB tek başına yetmez: AudioSet kanıtı yoksa (oda tınısı) işaret yok
    assert not has_background_music(-10.0, audioset=0.10, audioset_min=0.3)
    assert has_background_music(-10.0, audioset=0.55, audioset_min=0.3)
    # AudioSet yüksek ama dB eşiğin altında: duyulmuyor, işaret yok
    assert not has_background_music(-45.0, audioset=0.9, audioset_min=0.3)
    # audioset_min=None yalnızca dB kuralı
    assert has_background_music(-10.0, audioset=0.0, audioset_min=None)
