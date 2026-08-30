"""Sınır iyileştirme: ASR damgası erken bitse de kesim sessizliğe düşer."""

from __future__ import annotations

import numpy as np

from kiraat.boundaries import RefineConfig, envelope, find_boundary, refine_boundaries
from kiraat.segment import SegmentConfig, Word, segment

SR = 24000


def synth(words_true: list[tuple[float, float]], total: float, seed: int = 0) -> np.ndarray:
    """Her kelime için gürültü patlaması, arası sessizlik (çok düşük gürültü)."""
    rng = np.random.default_rng(seed)
    wave = rng.normal(0, 0.001, int(total * SR)).astype(np.float32)
    for a, b in words_true:
        i, j = int(a * SR), int(b * SR)
        wave[i:j] = rng.normal(0, 0.3, j - i)
    return wave


def test_sifir_bosluklu_damgada_kesim_sessizlige_duser():
    # Gerçek ses: kelime 1 0,50–1,20 s, sessizlik 1,20–1,55, kelime 2 1,55–2,20.
    wave = synth([(0.5, 1.2), (1.55, 2.2)], 3.0)
    env = envelope(wave, SR)
    seg = SegmentConfig(lead_pad_sec=0.15, trail_pad_sec=0.25)
    # Whisper'ın damgası: kelime 1'in bitişi 80 ms erken, sonraki hemen ona yapışık.
    prev_end, next_start = find_boundary(env, t_end=1.12, t_next=1.12, seg=seg)
    assert 1.20 <= prev_end <= 1.55, prev_end        # son hece klipte, kesim sessizlikte
    assert 1.20 <= next_start <= 1.55, next_start
    assert next_start >= prev_end


def test_sessizlik_yoksa_en_sessiz_an_secilir():
    wave = synth([(0.5, 2.5)], 3.0)   # kesintisiz konuşma
    env = envelope(wave, SR)
    prev_end, next_start = find_boundary(env, 1.4, 1.4, SegmentConfig())
    assert prev_end == next_start
    assert 1.3 <= prev_end <= 2.1


def test_refine_klip_listesinde_yalnizca_dar_bosluklari_degistirir():
    wave = synth([(0.5, 1.2), (1.55, 2.2), (4.0, 4.6)], 5.0)
    words = [Word("Bir.", 0.5, 1.12), Word("İki.", 1.12, 2.2), Word("Üç.", 4.0, 4.6)]
    seg = SegmentConfig(min_sec=0.1, target_sec=0.5, max_sec=5.0)
    clips = segment(words, seg)
    assert len(clips) == 3
    refined = refine_boundaries(clips, words, envelope(wave, SR), seg)
    assert "snapped_end" in refined[0].flags and refined[0].end >= 1.2
    assert "snapped_start" in refined[1].flags
    # İkinci ile üçüncü arasında 1,8 s boşluk var; dokunulmaz.
    assert "snapped_end" not in refined[1].flags and refined[2].start == clips[2].start
    for a, b in zip(refined, refined[1:]):
        assert a.end <= b.start


def test_tek_kelimelik_klip_eksi_sureli_olmaz():
    # "En" kelimesinin damgası 2120,10–2120,32; gerçek sessizlik ondan sonra. Sınır
    # sessizliğe çekilince klip başı kendi bitişini geçmemeli.
    wave = synth([(0.5, 2.0), (2.1, 2.3), (2.9, 4.0)], 5.0)   # ikinci kelime çok kısa
    words = [Word("Birinci cümle.", 0.5, 1.9), Word("En", 1.9, 2.05), Word("Sonraki.", 2.9, 4.0)]
    seg = SegmentConfig(min_sec=0.1, target_sec=0.5, max_sec=5.0)
    clips = segment(words, seg)
    refined = refine_boundaries(clips, words, envelope(wave, SR), seg)
    for c in refined:
        assert c.end > c.start, c
    for a, b in zip(refined, refined[1:]):
        assert a.end <= b.start



def test_sinir_sonraki_klibin_ilk_kelimesini_gecmez():
    """Sessizlik bulunamayınca 'en sessiz an' pencerenin uzak kenarına düşüp
    sonraki klibin ilk hecesini kesiyordu; sınır kelime başlangıcını geçemez."""
    import numpy as np
    from kiraat.boundaries import envelope, refine_boundaries
    from kiraat.segment import Clip, SegmentConfig, Word

    sr = 16000
    # 3 s boyunca kesintisiz gürültü: hiçbir yerde sessizlik yok
    rng = np.random.default_rng(0)
    wave = (rng.standard_normal(3 * sr) * 0.3).astype("float32")
    words = [Word("Bir.", 0.5, 1.0), Word("İki.", 1.02, 1.6)]
    clips = [Clip(0.4, 1.01, "Bir.", (0, 1)), Clip(1.01, 1.7, "İki.", (1, 2))]
    out = refine_boundaries(clips, words, envelope(wave, sr), SegmentConfig())
    assert out[1].start <= words[1].start
    assert out[0].end <= out[1].start


def test_kelime_basladiktan_sonraki_sessizlik_siniri_ileri_itmez():
    """Whisper/hizalayıcı damgası doğru, kelime kısa ve ardından sessizlik
    varsa bulunan sessizlik kelimenin SONRASIDIR; sınır oraya taşınırsa klip
    kendi kelimesini kaybeder (sample-15'te 0,1 s'lik '1.' klipleri)."""
    from kiraat.boundaries import envelope, refine_boundaries
    from kiraat.segment import Clip, SegmentConfig, Word

    # konuşma 0,5–1,15 (önceki), 1,17–1,50 (kısa kelime), sonra sessizlik 1,5–2,2, konuşma 2,2–3,0
    wave = synth([(0.5, 1.15), (1.17, 1.50), (2.2, 3.0)], 3.5)
    words = [Word("Bir.", 0.5, 1.15), Word("İki.", 1.17, 1.50), Word("Üç.", 2.2, 3.0)]
    clips = [Clip(0.4, 1.16, "Bir.", (0, 1)), Clip(1.16, 1.75, "İki.", (1, 2)), Clip(2.05, 3.2, "Üç.", (2, 3))]
    out = refine_boundaries(clips, words, envelope(wave, SR), SegmentConfig())
    assert out[1].start <= words[1].start, out[1]
    assert out[0].end <= out[1].start


def test_cakisan_damgalarda_sinir_ortaya_konur():
    """Hizalayıcı sonraki kelimeyi öncekinin bitişinden önce başlatmışsa iki
    kelimeden biri kesilecek; sınır çakışmanın ortasında olmalı, önceki
    klibin sonu kelimesinin 0,3 s içine çekilmemeli."""
    import numpy as np
    from kiraat.boundaries import envelope, refine_boundaries
    from kiraat.segment import Clip, SegmentConfig, Word

    sr = 16000
    wave = (np.random.default_rng(1).standard_normal(3 * sr) * 0.3).astype("float32")  # sessizlik yok
    words = [Word("Bir.", 0.5, 1.40), Word("İki.", 1.10, 1.9)]   # 0,3 s çakışma
    clips = [Clip(0.4, 1.25, "Bir.", (0, 1)), Clip(1.25, 2.0, "İki.", (1, 2))]
    out = refine_boundaries(clips, words, envelope(wave, sr), SegmentConfig())
    assert abs(out[0].end - 1.25) < 0.02 and abs(out[1].start - 1.25) < 0.02, out



def _zarf_referans(wave: np.ndarray, sr: int, cfg: RefineConfig = RefineConfig()) -> np.ndarray:
    """Zarfın apaçık ama belleği kaydın uzunluğuyla büyüyen hâli.

    Ölçüt burada: bloklu uygulama bununla birebir aynı sayıyı vermeli.
    """
    wave = np.asarray(wave, dtype=np.float32).ravel()
    frame = max(int(sr * cfg.frame_ms / 1000), 1)
    hop = max(int(sr * cfg.hop_ms / 1000), 1)
    n = max((len(wave) - frame) // hop + 1, 1)
    padded = np.pad(wave, (0, max(frame + (n - 1) * hop - len(wave), 0)))
    idx = np.arange(n)[:, None] * hop + np.arange(frame)[None, :]
    rms = np.sqrt(np.mean(padded[idx] ** 2, axis=1))
    return 20.0 * np.log10(np.maximum(rms, 1e-6))


def test_zarf_bloklu_hesapla_ayni_sayiyi_verir():
    rng = np.random.default_rng(0)
    for sr in (16000, 24000):
        for saniye in (0.005, 0.02, 0.5, 3.7, 61.3):
            wave = (rng.standard_normal(max(int(sr * saniye), 1)) * 0.1).astype(np.float32)
            assert np.array_equal(_zarf_referans(wave, sr), envelope(wave, sr).db), (sr, saniye)


def test_zarf_bellegi_kayit_uzunlugundan_bagimsiz():
    """Korpusta 14,9 saatlik kayıtlar var; zarf o kayıtta da sabit bellekle
    ölçülmeli. Kare dizinini tek seferde kuran hâli saat başına 2,7 GB
    harcıyordu — bu testin düşmesi o hâle dönüldüğünün işaretidir."""
    import tracemalloc

    wave = (np.random.default_rng(0).standard_normal(SR * 300) * 0.1).astype(np.float32)
    tracemalloc.start()
    try:
        tracemalloc.reset_peak()
        envelope(wave, SR)
        yeni = tracemalloc.get_traced_memory()[1]
        tracemalloc.reset_peak()
        _zarf_referans(wave, SR)
        eski = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    assert yeni < 64 << 20, f"zarf 5 dakikada {yeni/1e6:.0f} MB harcadı"
    assert eski > 4 * yeni, f"referans {eski/1e6:.0f} MB, bloklu {yeni/1e6:.0f} MB — ölçüt anlamını yitirmiş"


def test_zarf_dosyadan_akitilinca_da_ayni(tmp_path):
    """`envelope_of_file` sesi belleğe almadan aynı zarfı üretmeli."""
    import tracemalloc

    import soundfile as sf

    from kiraat.boundaries import envelope_of_file

    wave = (np.random.default_rng(3).standard_normal(SR * 137) * 0.1).astype(np.float32)
    path = tmp_path / "kayit.flac"
    sf.write(str(path), wave, SR, format="FLAC", subtype="PCM_16")
    okunan, _ = sf.read(str(path), dtype="float32")
    tracemalloc.start()
    try:
        tracemalloc.reset_peak()
        env, sr, n = envelope_of_file(str(path))
        zirve = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    assert (sr, n) == (SR, len(wave))
    assert np.array_equal(env.db, envelope(okunan, SR).db)
    assert zirve < 64 << 20, f"dosyadan zarf {zirve/1e6:.0f} MB harcadı (ses {len(wave)*4/1e6:.0f} MB)"
