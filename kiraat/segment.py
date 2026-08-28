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

from .text.sentences import sentence_spans

#: Uzun bir cümle bölünmek zorunda kalırsa tercih sırasına göre iç noktalama.
INTERNAL_BREAKS = (";", ":", "—", "–", ",")


@dataclass(frozen=True)
class Word:
    text: str
    start: float
    end: float


@dataclass(frozen=True)
class SegmentConfig:
    min_sec: float = 2.5
    target_sec: float = 9.0
    max_sec: float = 20.0
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
    """Klibin iki ucuna, komşuya taşmadan, nefes payı bırak."""
    start = max(clip.start - cfg.lead_pad_sec, prev_end, 0.0)
    end = clip.end + cfg.trail_pad_sec
    if next_start is not None:
        end = min(end, next_start)
    return replace(clip, start=round(start, 3), end=round(end, 3))


def segment(words: list[Word], cfg: SegmentConfig | None = None) -> list[Clip]:
    """Kelime zaman damgalarından cümle hizalı klipler üret."""
    cfg = cfg or SegmentConfig()
    if not words:
        return []

    pieces: list[tuple[int, int, tuple[str, ...]]] = []
    for sent in _sentences(words):
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
        joined = end - words[cur_a].start
        too_long = joined > cfg.max_sec
        long_pause = gap > cfg.max_join_gap_sec
        enough = (words[cur_b - 1].end - words[cur_a].start) >= cfg.target_sec
        if too_long or long_pause or enough:
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
