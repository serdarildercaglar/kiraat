"""Klip sınırlarını ASR zaman damgasından sese çekme.

Kör dinlemede görülen kusur: Whisper bir kelimenin bitişini bir sonrakinin
başına yapıştırdığında (boşluk 0,0 s; koşuda kliplerin %10'u) kelime bitişi
erken olduğu için son hece klibin dışında kalıyor — "anımsatıyor|du".
Zaman damgası çevresinde pay bırakmak bunu çözmez, çünkü verilecek boşluk
yok. Oysa gerçek sessizlik (nefes) damganın hemen yakınında duruyor.

Bu modül bölütlemeden sonra çalışır: komşu iki klip arasındaki damga
çevresinde küçük bir pencerede ses enerjisine bakar, sessizlik bulursa
sınırı oraya koyar; bulamazsa penceredeki en düşük enerjili ana koyar.
Metne dokunmaz, klip sırasını ve kelime aralıklarını değiştirmez.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Sequence

import numpy as np

from .segment import Clip, SegmentConfig, Word


@dataclass(frozen=True)
class RefineConfig:
    #: Damgadan ne kadar önce/sonra aranır (s). Öncesi kasıtlı olarak kısa:
    #: Whisper kelime bitişleri erken olduğu için sessizlik hep sonradadır.
    before_sec: float = 0.05
    after_sec: float = 0.60
    frame_ms: float = 20.0
    hop_ms: float = 10.0
    #: Yerel konuşma seviyesinin bu kadar altı sessizlik sayılır (dB).
    silence_drop_db: float = 25.0
    #: Sessizlik sayılması için asgari süre (s).
    min_silence_sec: float = 0.06
    #: Bulunan sessizlik sonraki kelimenin damgasından bu kadar sonra
    #: başlıyorsa kelime çoktan başlamıştır; sınır damgayı geçemez (s).
    silence_after_word_sec: float = 0.10


@dataclass(frozen=True)
class Envelope:
    """Kısa zamanlı enerji, dBFS; `t(i)` ile karenin ortası saniye."""

    db: np.ndarray
    hop: float
    frame: float

    def index(self, t: float) -> int:
        return int(np.clip(round((t - self.frame / 2) / self.hop), 0, len(self.db) - 1))

    def t(self, i: int) -> float:
        return i * self.hop + self.frame / 2


#: Kare bloğu başına ayrılan geçici bellek tavanı (bayt). Zarf, kayıt ne
#: kadar uzun olursa olsun bu tavanın üstüne çıkmaz.
_BLOCK_BYTES = 32 << 20


def _geometry(n_samples: int, sr: int, cfg: RefineConfig) -> tuple[int, int, int]:
    frame = max(int(sr * cfg.frame_ms / 1000), 1)
    hop = max(int(sr * cfg.hop_ms / 1000), 1)
    n = max((n_samples - frame) // hop + 1, 1)
    return frame, hop, n


def _block_db(block: np.ndarray, frame: int, hop: int, rows: int) -> np.ndarray:
    """`rows` kareyi bitişik bir (rows, frame) dizisinde ölçüp dB döndür.

    Kareler bitişik kopyalanır, çünkü `np.mean` toplama sırasını dizinin
    yerleşimine göre seçiyor; görünüm üzerinden ortalama almak son bitlerde
    farklı sonuç verebilirdi ve bu aşamanın çıktısı yayımlanıyor.
    """
    win = np.lib.stride_tricks.sliding_window_view(block, frame)[::hop][:rows]
    rms = np.sqrt(np.mean(np.ascontiguousarray(win) ** 2, axis=1))
    return 20.0 * np.log10(np.maximum(rms, 1e-6))


def envelope(wave: np.ndarray, sr: int, cfg: RefineConfig = RefineConfig()) -> Envelope:
    """Bellekteki sesin kısa zamanlı enerjisi, blok blok.

    Kare dizinini tek seferde maddileştiren eski uygulama örnek başına 24
    bayt harcıyordu (saatte 2,7 GB); korpusta 4 saatten uzun 131, 8 saatten
    uzun 35 kayıt var, yani ölçüm kaydın uzunluğuyla büyüyen bir bellek
    duvarına çarpıyordu. Çıktı aynı, harcanan bellek artık sabit.
    """
    wave = np.asarray(wave, dtype=np.float32).ravel()
    frame, hop, n = _geometry(len(wave), sr, cfg)
    if len(wave) < frame + (n - 1) * hop:
        wave = np.pad(wave, (0, frame + (n - 1) * hop - len(wave)))
    rows = max(int(_BLOCK_BYTES // (frame * 4)), 1)
    out = np.empty(n, dtype=np.float64)
    for i in range(0, n, rows):
        take = min(rows, n - i)
        a = i * hop
        out[i:i + take] = _block_db(wave[a:a + frame + (take - 1) * hop], frame, hop, take)
    return Envelope(db=out, hop=hop / sr, frame=frame / sr)


def envelope_of_file(path: str, cfg: RefineConfig = RefineConfig()) -> tuple[Envelope, int, int]:
    """Zarfı dosyadan akıtarak ölç; ses hiçbir zaman tümüyle belleğe alınmaz.

    `(zarf, örnekleme hızı, örnek sayısı)` döner. Tek kanallı kayıt bekler —
    hattın `prepare` aşaması her kaydı monoya indirir; çok kanallı bir dosya
    verilirse çağıran tarafın kendisi karıştırmalıdır.
    """
    import soundfile as sf

    info = sf.info(str(path))
    if info.channels != 1:
        raise ValueError(f"tek kanal bekleniyordu, {info.channels} kanal: {path}")
    sr, total = info.samplerate, info.frames
    frame, hop, n = _geometry(total, sr, cfg)
    rows = max(int(_BLOCK_BYTES // (frame * 4)), 1)
    out = np.empty(n, dtype=np.float64)
    with sf.SoundFile(str(path)) as fh:
        for i in range(0, n, rows):
            take = min(rows, n - i)
            need = frame + (take - 1) * hop
            fh.seek(i * hop)
            block = fh.read(need, dtype="float32", always_2d=False)
            if len(block) < need:      # yalnızca kaydın sonunda: son kare eksik kalırsa
                block = np.pad(block, (0, need - len(block)))
            out[i:i + take] = _block_db(block, frame, hop, take)
    return Envelope(db=out, hop=hop / sr, frame=frame / sr), sr, total


def _silence_runs(mask: np.ndarray) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    start = None
    for i, m in enumerate(mask):
        if m and start is None:
            start = i
        elif not m and start is not None:
            runs.append((start, i))
            start = None
    if start is not None:
        runs.append((start, len(mask)))
    return runs


def find_boundary(
    env: Envelope, t_end: float, t_next: float, seg: SegmentConfig, cfg: RefineConfig = RefineConfig()
) -> tuple[float, float]:
    """(önceki klibin bitişi, sonraki klibin başlangıcı); bkz. `find_boundary_ex`."""
    prev_end, next_start, _ = find_boundary_ex(env, t_end, t_next, seg, cfg)
    return prev_end, next_start


def find_boundary_ex(
    env: Envelope, t_end: float, t_next: float, seg: SegmentConfig, cfg: RefineConfig = RefineConfig()
) -> tuple[float, float, float | None]:
    """(önceki klibin bitişi, sonraki klibin başlangıcı).

    `t_end` önceki klibin son kelimesinin, `t_next` sonrakinin ilk kelimesinin
    ASR damgası. Pencere içinde en uzun sessizlik bulunursa önceki klip o
    sessizliğe `trail_pad_sec` kadar uzar, sonraki klip sessizliğin sonundan
    `lead_pad_sec` önce başlar; ikisi çakışmaz. Sessizlik yoksa ikisi de
    penceredeki en sessiz ana konur. Üçüncü değer bulunan sessizliğin
    başlangıcıdır (yoksa None); çağıran, sessizliğin sonraki kelime
    başladıktan sonra mı geldiğine bununla karar verir.
    """
    # Pencere `t_next`e göre kısılmaz: boşluk sıfırken sonraki kelimenin
    # damgası da yanlış yerdedir ve gerçek sessizlik ikisinin de ötesindedir.
    # Sonraki kelimeye taşma, çağıranın kelime bitişine göre kırpmasıyla önlenir.
    lo = env.index(t_end - cfg.before_sec)
    hi = env.index(max(t_next, t_end) + cfg.after_sec)
    if hi <= lo:
        t = env.t(lo)
        return t, t
    ctx_lo, ctx_hi = env.index(t_end - 1.0), env.index(t_next + 1.0) + 1
    level = float(np.percentile(env.db[ctx_lo:ctx_hi], 90))
    window = env.db[lo:hi + 1]
    quiet = window < (level - cfg.silence_drop_db)
    min_frames = max(int(round(cfg.min_silence_sec / env.hop)), 1)
    runs = [(a, b) for a, b in _silence_runs(quiet) if b - a >= min_frames]
    if runs:
        a, b = max(runs, key=lambda r: r[1] - r[0])
        s0, s1 = env.t(lo + a) - env.frame / 2, env.t(lo + b - 1) + env.frame / 2
        prev_end = min(s0 + seg.trail_pad_sec, s1)
        next_start = max(s1 - seg.lead_pad_sec, prev_end)
        return round(prev_end, 3), round(next_start, 3), round(s0, 3)
    t = env.t(lo + int(np.argmin(window)))
    return round(t, 3), round(t, 3), None


def refine_boundaries(
    clips: Sequence[Clip],
    words: Sequence[Word],
    env: Envelope,
    seg: SegmentConfig,
    cfg: RefineConfig = RefineConfig(),
) -> list[Clip]:
    """Komşu klip çiftlerinin ortak sınırını sese göre yeniden koy.

    Yalnızca damgalar arası boşluğun iki payı da barındıramadığı çiftler
    değiştirilir; geniş boşluklu çiftlerde bölütleyicinin payı zaten
    sessizliğin içindedir. İlk klibin başı ve son klibin sonu dokunulmaz.
    """
    if not clips:
        return []
    out = list(clips)
    room = seg.lead_pad_sec + seg.trail_pad_sec
    for i in range(len(out) - 1):
        prev, nxt = out[i], out[i + 1]
        t_end = words[prev.word_span[1] - 1].end
        t_next = words[nxt.word_span[0]].start
        if t_next - t_end >= room:
            continue
        prev_end, next_start, silence_at = find_boundary_ex(env, t_end, t_next, seg, cfg)
        # Sınır önceki klibin son kelimesinin başına taşamaz ve iki klip
        # çakışmaz.
        prev_end = max(prev_end, words[prev.word_span[1] - 1].start + 0.05)
        next_start = max(next_start, prev_end)
        # Sonraki kelimenin damgasının ötesine yalnızca güçlü kanıtla geçilir:
        # damgada ya da hemen ardında başlayan bir sessizlik, kelimenin henüz
        # başlamadığını gösterir (Whisper'ın yapıştırdığı kelimeler). Sessizlik
        # yoksa ("en sessiz an" pencerenin uzak kenarına düşer) ya da sessizlik
        # kelime başladıktan sonra geliyorsa sınır kelime başını geçemez —
        # sample-15'te kliplerin %2,5'i ilk hecesi kesik başlıyordu.
        if silence_at is None or silence_at > t_next + cfg.silence_after_word_sec:
            next_start = min(next_start, t_next)
            prev_end = min(prev_end, next_start)
        # Hizalayıcı damgaları çakışıyorsa (sonraki kelime öncekinin bitişinden
        # önce "başlıyor") hangi kelimenin kesileceği belirsizdir; sınır çakışma
        # aralığının ortasına konur ki kayıp iki tarafa da en az olsun.
        if t_next < t_end and next_start < t_end:
            mid = round((t_end + t_next) / 2, 3)
            next_start = max(next_start, mid)
            prev_end = min(max(prev_end, mid), next_start)
        # Sonraki klip tek kelimelik ve damgası yanlışsa bulunan sessizlik onun
        # bitişinin ötesinde kalabilir; klip sıfır ya da eksi süreli olmasın diye
        # sınır geri çekilir, gerekirse önceki klip de kısalır.
        floor = nxt.end - 0.05
        if next_start > floor:
            next_start = max(floor, words[nxt.word_span[0]].start)
            prev_end = min(prev_end, next_start)
        out[i] = replace(prev, end=prev_end, flags=tuple(sorted(set(prev.flags) | {"snapped_end"})))
        out[i + 1] = replace(nxt, start=next_start, flags=tuple(sorted(set(nxt.flags) | {"snapped_start"})))
    return out
