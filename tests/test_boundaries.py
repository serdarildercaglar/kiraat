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
