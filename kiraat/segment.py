"""Cümle hizalı bölütleme.

v1 sessizlikte kesiyordu; bu modül transcript'te keser. Kesim noktaları
cümle sınırlarıdır, dolayısıyla bir klibin cümle ortasından başlaması
yapısal olarak imkânsızdır — tek istisna, tek başına üst süre sınırını aşan
bir cümlenin iç noklamasından bölünmesidir ve o klipler `forced_split`
işaretiyle ayrılabilir.

Girdi ASR'nin kelime zaman damgalarıdır. VAD artık kesim aracı değil;
yalnızca konuşma bölgesi bulucu olarak, ASR'den önce kullanılır.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Sequence

from .text.sentences import sentence_spans
from .text.turkish import has_sentence_end, is_lower_start, lower, upper

#: Uzun bir cümle bölünmek zorunda kalırsa tercih sırasına göre iç noktalama.
INTERNAL_BREAKS = (";", ":", "—", "–", ",")


@dataclass(frozen=True)
class Word:
    text: str
    start: float
    end: float
    #: ASR/hizalayıcının kelime güveni; birleştirmede asgarisi alınır.
    prob: float | None = None


def _is_clitic(token: str) -> bool:
    """Kesme/tire ile başlayan ek ('ın, -ı) ya da yalnız noktalama mı."""
    if not any(ch.isalnum() for ch in token):
        return True  # yalnız noktalama: "." "," "''"
    # "P .O .Y .M." — kısaltma harfleri noktayla başlayan belirteç olarak gelir.
    if token[0] == "." and len(token.rstrip(".")) == 2 and token[1].isalpha() and token[1] == upper(token[1]):
        return True
    body = token.lstrip("'’-–")
    if body == token:
        return False
    return body[0].isalpha() and body[0] == lower(body[0])


def attach_clitics(words: list[Word]) -> list[Word]:
    """Whisper'ın ayrı belirteç verdiği ekleri ("Button", "'ın") öncekine yapıştır.

    Açılış tırnağıyla başlayan gerçek kelimeler ("''Padişahım") dokunulmadan
    kalır; yalnızca kesme/tire sonrası küçük harfle devam eden parçalar ve
    tek başına kalmış noktalama birleştirilir. Zaman aralığı birleşir, güven
    ikisinin asgarisidir.
    """
    out: list[Word] = []
    for w in words:
        if out and _is_clitic(w.text):
            prev = out[-1]
            probs = [x for x in (prev.prob, w.prob) if x is not None]
            out[-1] = Word(prev.text + w.text, prev.start, w.end, min(probs) if probs else None)
        else:
            out.append(w)
    return out


@dataclass(frozen=True)
class SegmentConfig:
    min_sec: float = 2.5
    target_sec: float = 7.0
    max_sec: float = 15.0
    #: İki cümle arasındaki bu süreden uzun sessizlik bölüm geçişi sayılır ve
    #: cümleler aynı klibe yapıştırılmaz.
    max_join_gap_sec: float = 1.2
    lead_pad_sec: float = 0.15
    trail_pad_sec: float = 0.25


@dataclass(frozen=True)
class Clip:
    start: float
    end: float
    text: str
    word_span: tuple[int, int]
    flags: tuple[str, ...] = field(default=())

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass(frozen=True)
class _Sentence:
    a: int
    b: int
    start: float
    end: float

    @property
    def duration(self) -> float:
        return self.end - self.start


def _sentences(words: list[Word]) -> list[_Sentence]:
    spans = sentence_spans([w.text for w in words])
    return [_Sentence(a, b, words[a].start, words[b - 1].end) for a, b in spans]


def _text(words: list[Word], a: int, b: int) -> str:
    return " ".join(w.text for w in words[a:b])


def _split_oversize(
    words: list[Word], sent: _Sentence, cfg: SegmentConfig
) -> list[tuple[int, int, tuple[str, ...]]]:
    """Tek başına `max_sec`i aşan cümleyi iç noktalamasından böl.

    Hiçbir iç noktalama yoksa cümle bölünmez: bütün olarak, `oversize`
    işaretiyle döner. Bölmek yerine işaretlemek bilinçli — v1'in hatası,
    kararsız kaldığı veriyi kullanılamaz hale getirmesiydi.
    """
    if sent.duration <= cfg.max_sec:
        return [(sent.a, sent.b, ())]

    # Önce uzun iç sessizlik: noktalamasız bir "cümle" içinde `max_join_gap_sec`
    # üstü bir boşluk, büyük olasılıkla ASR'nin noktalamadığı bir cümle
    # sınırıdır (başlık → ilk cümle arasındaki 49 s'lik giriş müziği gibi).
    # En büyük boşlukta kesilir; parça metin olarak bütün görünüyorsa
    # (büyük harfle başlıyor, cümle sonuyla bitiyor) işaret almaz, aksi hâlde
    # `gap_split` alır ve önerilen alt kümeden düşer.
    gaps = [(words[i + 1].start - words[i].end, i) for i in range(sent.a, sent.b - 1)]
    big = [(g, i) for g, i in gaps if g > cfg.max_join_gap_sec]
    if big:
        _, pivot = max(big)
        left = _Sentence(sent.a, pivot + 1, sent.start, words[pivot].end)
        right = _Sentence(pivot + 1, sent.b, words[pivot + 1].start, sent.end)
        out: list[tuple[int, int, tuple[str, ...]]] = []
        for part in (left, right):
            for a, b, flags in _split_oversize(words, part, cfg):
                text = _text(words, a, b)
                complete = not is_lower_start(text) and has_sentence_end(text)
                out.append((a, b, flags if complete else tuple(sorted(set(flags) | {"gap_split"}))))
        return out

    for mark in INTERNAL_BREAKS:
        cuts = [
            i
            for i in range(sent.a, sent.b - 1)
            if words[i].text.rstrip().endswith(mark)
        ]
        if not cuts:
            continue
        # Hedef süreye en yakın kesimi seç, iki yanı da ayrı ayrı özyinele.
        pivot = min(cuts, key=lambda i: abs((words[i].end - sent.start) - cfg.target_sec))
        left = _Sentence(sent.a, pivot + 1, sent.start, words[pivot].end)
        right = _Sentence(pivot + 1, sent.b, words[pivot + 1].start, sent.end)
        out: list[tuple[int, int, tuple[str, ...]]] = []
        for part in (left, right):
            for a, b, flags in _split_oversize(words, part, cfg):
                out.append((a, b, tuple(sorted(set(flags) | {"forced_split"}))))
        return out

    return [(sent.a, sent.b, ("oversize",))]


def _pad(
    clip: Clip, words: list[Word], cfg: SegmentConfig, prev_end: float, next_start: float
) -> Clip:
    """Klibin iki ucuna nefes payı bırak; komşuyla arayı en fazla ortadan böl.

    Pay komşu kelimenin bitişine dayanırsa, ASR kelime bitişleri erken
    olduğu için önceki kelimenin kuyruğu klibe sızıyor (kör dinlemede
    duyuldu). Bu yüzden sınır, komşuya olan boşluğun ortasını geçemez.
    """
    start = max(clip.start - cfg.lead_pad_sec, (clip.start + prev_end) / 2.0, 0.0)
    end = clip.end + cfg.trail_pad_sec
    if next_start is not None:
        end = min(end, (clip.end + next_start) / 2.0)
    return replace(clip, start=round(start, 3), end=round(end, 3))


def clamp_to_audio(clips: list[Clip], total_sec: float) -> list[Clip]:
    """Klip sınırlarını kaydın gerçek süresine kelepçele.

    Son klibin nefes payı (`trail_pad_sec`) kaydın sonunu aşabilir; kesim
    bunu sessizce kırpıyordu ama `end`/`duration` sütunları aşan değeri
    taşıyordu (beş kayıtlık örnekte bir klipte 0,19 s). Sütun, dosyadaki
    sesle aynı olmalı.
    """
    out: list[Clip] = []
    for c in clips:
        end = min(c.end, round(total_sec, 3))
        out.append(replace(c, end=end) if end != c.end else c)
    return out


def _cut_at_boilerplate(
    sentences: list[_Sentence], words: list[Word], spans: Sequence[tuple[int, int]]
) -> list[tuple[_Sentence, bool]]:
    """Cümleleri boilerplate aralıklarının sınırlarında böl; (parça, boilerplate mi)."""
    marks = sorted(set(x for span in spans for x in span))
    out: list[tuple[_Sentence, bool]] = []
    for sent in sentences:
        cuts = [sent.a] + [m for m in marks if sent.a < m < sent.b] + [sent.b]
        for a, b in zip(cuts, cuts[1:]):
            is_bp = any(x <= a and b <= y for x, y in spans)
            out.append((_Sentence(a, b, words[a].start, words[b - 1].end), is_bp))
    return out


def segment(
    words: list[Word],
    cfg: SegmentConfig | None = None,
    boilerplate: Sequence[tuple[int, int]] = (),
) -> list[Clip]:
    """Kelime zaman damgalarından cümle hizalı klipler üret.

    `boilerplate`, kanal düzeyinde madenlenmiş künye/anons ifadelerinin
    kelime aralıklarıdır (`kiraat.boilerplate.find_spans`). Bu aralıklar
    kendi başına klip olur, `boilerplate` işareti taşır ve komşularıyla
    birleşmez; böylece künye ilk cümleye yapışmaz.
    """
    cfg = cfg or SegmentConfig()
    if not words:
        return []

    pieces: list[tuple[int, int, tuple[str, ...]]] = []
    for sent, is_bp in _cut_at_boilerplate(_sentences(words), words, boilerplate):
        if is_bp:
            pieces.append((sent.a, sent.b, ("boilerplate",)))
        else:
            pieces.extend(_split_oversize(words, sent, cfg))

    clips: list[Clip] = []
    cur_a = cur_b = None
    cur_flags: set[str] = set()
    for a, b, flags in pieces:
        start, end = words[a].start, words[b - 1].end
        if cur_a is None:
            cur_a, cur_b, cur_flags = a, b, set(flags)
            continue
        gap = start - words[cur_b - 1].end
        current = words[cur_b - 1].end - words[cur_a].start
        joined = end - words[cur_a].start
        too_long = joined > cfg.max_sec
        long_pause = gap > cfg.max_join_gap_sec
        # Hedef aşılmaz: grup zaten `min_sec` üstündeyse ve bir cümle daha
        # eklemek hedefi aşacaksa grup kapanır. "Hedefe ulaşana kadar ekle"
        # kuralı klipleri hedef + bir cümle uzunluğuna taşıyordu (28 dakikalık
        # örnekte medyan 11,5 s, hedef 9 s iken).
        overshoot = current >= cfg.min_sec and joined > cfg.target_sec
        hard = "boilerplate" in flags or "boilerplate" in cur_flags
        if too_long or long_pause or overshoot or hard:
            clips.append(
                Clip(words[cur_a].start, words[cur_b - 1].end,
                     _text(words, cur_a, cur_b), (cur_a, cur_b),
                     tuple(sorted(cur_flags)))
            )
            cur_a, cur_b, cur_flags = a, b, set(flags)
        else:
            cur_b = b
            cur_flags |= set(flags)
    if cur_a is not None:
        clips.append(
            Clip(words[cur_a].start, words[cur_b - 1].end,
                 _text(words, cur_a, cur_b), (cur_a, cur_b), tuple(sorted(cur_flags)))
        )

    # Kısa klipleri, üst sınırı aşmıyorsa bir sonrakiyle birleştir.
    merged: list[Clip] = []
    for clip in clips:
        if (
            merged
            and "boilerplate" not in merged[-1].flags
            and "boilerplate" not in clip.flags
            and merged[-1].duration < cfg.min_sec
            and (clip.end - merged[-1].start) <= cfg.max_sec
            and (clip.start - merged[-1].end) <= cfg.max_join_gap_sec
        ):
            prev = merged.pop()
            merged.append(
                Clip(prev.start, clip.end,
                     _text(words, prev.word_span[0], clip.word_span[1]),
                     (prev.word_span[0], clip.word_span[1]),
                     tuple(sorted(set(prev.flags) | set(clip.flags))))
            )
        else:
            merged.append(clip)
    merged = [
        c if c.duration >= cfg.min_sec else replace(c, flags=tuple(sorted(set(c.flags) | {"short"})))
        for c in merged
    ]

    out: list[Clip] = []
    for i, clip in enumerate(merged):
        prev_end = merged[i - 1].end if i else 0.0
        next_start = merged[i + 1].start if i + 1 < len(merged) else None
        out.append(_pad(clip, words, cfg, prev_end, next_start))
    return out
