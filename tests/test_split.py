"""Bölme sözleşmesi: kayıt düzeyi, kanal dengesi, metin sızıntısı sıfır.

v1'in kusuru ölçülüydü (`docs/DESIGN.md` madde 6): `validation`ın %5,9'u
`train` ile aynı metni taşıyordu ve gerçek bir held-out yoktu.
"""

from kiraat.split import SplitConfig, assign_sources, source_leakage, text_leakage


def sources(n_per_channel=4, channels=("a", "b", "c")):
    out, sid = [], 1
    for ch in channels:
        for _ in range(n_per_channel):
            out.append({"id": sid, "channel": ch}); sid += 1
    return out


def test_kayit_duzeyinde_boler_ve_kanal_dengeli():
    srcs = sources()
    hours = {s["id"]: 1.0 for s in srcs}
    split_of = assign_sources(srcs, hours, SplitConfig(test_hours=3.0, dev_hours=3.0))
    # kanal başına 1 sa test + 1 sa dev hedefi: her kanaldan birer kayıt
    per_channel = {}
    for s in srcs:
        per_channel.setdefault(s["channel"], []).append(split_of[s["id"]])
    for ch, splits in per_channel.items():
        assert splits.count("test") == 1, (ch, splits)
        assert splits.count("dev") == 1, (ch, splits)
    assert not source_leakage(split_of)


def test_kanal_hedefi_dolduramazsa_acik_kalir_telafi_edilmez():
    """Küçük kanal test hedefini dolduramaz; başka kanaldan tamamlanmaz,
    çünkü telafi tam da bozmak istediğimiz dengesizliği geri getirir."""
    srcs = [{"id": 1, "channel": "kucuk"}] + [{"id": i, "channel": "buyuk"} for i in range(2, 12)]
    hours = {1: 0.1, **{i: 5.0 for i in range(2, 12)}}
    split_of = assign_sources(srcs, hours, SplitConfig(test_hours=4.0, dev_hours=0.0))
    assert split_of[1] == "test"                      # elindeki kadarı alınır
    assert sum(1 for i in range(2, 12) if split_of[i] == "test") == 1


def test_metin_sizintisi_bulunur():
    split_of = {1: "train", 2: "test"}
    clips = [
        {"id": "a", "source_id": 1, "text": "Bir varmış bir yokmuş."},
        {"id": "b", "source_id": 2, "text": "bir varmış, bir yokmuş"},   # aynı metin
        {"id": "c", "source_id": 2, "text": "Başka bir cümle."},
    ]
    leaked = text_leakage(clips, split_of)
    assert leaked["test"] == {"b"}
    assert leaked["dev"] == set()


def test_bos_metin_sizinti_saymaz():
    split_of = {1: "train", 2: "test"}
    clips = [{"id": "a", "source_id": 1, "text": ""}, {"id": "b", "source_id": 2, "text": ""}]
    assert text_leakage(clips, split_of) == {"dev": set(), "test": set()}
