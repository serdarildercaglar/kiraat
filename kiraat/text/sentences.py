"""Türkçe cümle sınırı bulma.

v1'in en pahalı kusuru, kesimin sessizlikte yapılmasıydı: seslendiren virgülde
nefes alıyor, iki cümle arasında almıyor, dolayısıyla yayımlanan temiz havuzun
%9,4'ü cümle ortasından başlıyordu. v2 kesimi transcript üzerinde yapar ve bu
modül o kesimin nereye düşeceğine karar verir.

Girdi, ASR'nin kelime zaman damgalarıyla verdiği belirteç (token) dizisidir.
Çıktı, cümle oluşturan belirteç aralıklarıdır; zaman eşlemesi çağıranın işidir.
"""

from __future__ import annotations

from .turkish import CLOSERS, SENTENCE_END, lower, upper

#: Sonundaki nokta cümleyi bitirmeyen kısaltmalar. Nokta içerenler ('M.Ö.')
#: olduğu gibi, tek harfli baş harfler ('A.') ayrı kuralla ele alınır.
ABBREVIATIONS = frozenset(
    {
        "dr", "doç", "prof", "yrd", "av", "sn", "sayın", "alb", "gen", "yzb",
        "hz", "st", "mah", "cad", "sok", "apt", "no", "tel", "faks",
        "bkz", "örn", "yak", "çev", "haz", "ed", "der", "yay", "bas",
        "vb", "vs", "vd", "age", "agy", "yy", "as", "ms", "mö",
        "sf", "s", "c", "bl", "böl", "şb", "tic", "ltd", "şti", "a.ş",
        "mim", "müh", "uzm", "öğr", "gör", "arş", "ing", "alm", "fr", "osm",
    }
)

#: Sıra sayısı olduğu için noktası cümle bitirmeyen sayılardan sonra gelmesi
#: beklenen sözcükler ('3. bölüm', '1. kitap'). Küçük harfle başlayan her
#: sözcük zaten sınır saymaz; bu küme yalnızca büyük harfle başlayanlar için.
ORDINAL_FOLLOWERS = frozenset(
    {"bölüm", "kitap", "cilt", "kısım", "perde", "sayı", "baskı", "dünya"}
)


def _strip_closers(token: str) -> str:
    out = token.rstrip()
    while out and out[-1] in CLOSERS:
        out = out[:-1].rstrip()
    return out


def _core(token: str) -> str:
    """Belirtecin noktalamadan arınmış gövdesi, küçük harfe çevrilmiş."""
    return lower(_strip_closers(token).rstrip("".join(SENTENCE_END))).strip(",;:—-–")


def _starts_new_sentence(token: str) -> bool:
    """Bir sonraki belirteç yeni bir cümle başlatıyor gibi mi duruyor."""
    for ch in token:
        if ch.isalpha():
            return ch == upper(ch) and ch != lower(ch)
        if ch.isdigit():
            return True
        if ch in CLOSERS or ch in "«(-—":
            continue
        return False
    return False


def is_boundary(tokens: list[str], i: int) -> bool:
    """`tokens[i]` bir cümleyi bitiriyor mu."""
    token = _strip_closers(tokens[i])
    if not token or token[-1] not in SENTENCE_END:
        return False

    # '!' ve '?' kısaltma olamaz; nokta belirsiz olan tek işaret.
    if token[-1] == ".":
        core = _core(token)
        if core in ABBREVIATIONS:
            return False
        # Tek harfli baş harf: 'A. Hamdi Tanpınar'.
        if len(core) == 1 and core.isalpha():
            return False
        # 'M.Ö.' gibi içinde nokta olan kısaltmalar.
        if "." in core and core.replace(".", "") in ABBREVIATIONS:
            return False
        if core.isdigit():
            # 1-3 basamaklı sayı + nokta neredeyse her zaman sıra sayısıdır
            # ("1. Naip", "3. Selim", "100. Yıl") — ardından özel isim geldiği
            # için büyük harf kuralı onu yakalayamıyor ve tek belirteçlik
            # 0,1 s'lik "1." klipleri doğuyordu (defter, açık madde 9).
            # Cümlenin çıplak küçük bir sayıyla bitmesi okuma konuşmasında
            # nadirdir; yıllar ("... bitti 1918. Yeni dönem...") 4 basamaklıdır
            # ve sınır olarak kalır.
            if len(core) <= 3:
                return False
            nxt = tokens[i + 1] if i + 1 < len(tokens) else ""
            if not nxt or not _starts_new_sentence(nxt):
                return False
            if _core(nxt) in ORDINAL_FOLLOWERS:
                return False

    if i + 1 >= len(tokens):
        return True
    return _starts_new_sentence(tokens[i + 1])


def sentence_spans(tokens: list[str]) -> list[tuple[int, int]]:
    """Belirteç dizisini cümlelere böl; (başlangıç, bitiş) yarı açık aralıklar."""
    spans: list[tuple[int, int]] = []
    start = 0
    for i in range(len(tokens)):
        if is_boundary(tokens, i):
            spans.append((start, i + 1))
            start = i + 1
    if start < len(tokens):
        spans.append((start, len(tokens)))
    return spans
