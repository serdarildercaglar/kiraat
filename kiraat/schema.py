"""Yayımlanan klip şeması: her sütunun türü, birimi, üreten aşaması ve anlamı.

Tek kaynak burasıdır. `Pipeline.export` manifestoyu yazar, bu modül onu
belgeler ve `check_manifest` ikisinin birbirinden kopmadığını sınar
(`tests/test_schema.py`). Makaledeki sütun tablosu ve veri kartı
`python -m kiraat schema` çıktısından üretilir, elle yazılmaz.

Üç ilke şemayı biçimlendirir (docs/DESIGN.md):
  * Hiçbir eşik klip elemez: ölçümlerin hepsi sütun olarak yayımlanır,
    karar `recommended` + `exclusion_reasons` + `policy_version` üçlüsüdür.
  * Metin üç alandır ve üçü de farklıdır: `text_raw`, `text`, `text_spoken`.
  * Yineleme ve kalıp metin silinmez, işaretlenir (`duplicate_of`, `flags`).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


@dataclass(frozen=True)
class Column:
    name: str
    dtype: str            # string | int | float | bool | list[string] | audio
    stage: str            # üreten aşama ya da 'export'
    description: str
    unit: str = ""
    #: Her satırda bulunmayabilir (isteğe bağlı model, eksik ölçüm).
    optional: bool = False
    #: Yerel çalışma dizinine özgü; yayımlanan sürümde dönüştürülür ya da düşer.
    local: bool = False


COLUMNS: tuple[Column, ...] = (
    # ------------------------------------------------------------ kimlik
    Column("id", "string", "segment",
           "Klip kimliği: `srcNNNNN-KKKKK`; kaynak kaydın numarası ve klibin kayıt içindeki sırası."),
    Column("audio", "audio", "segment",
           "Klip sesi: 24 kHz, tek kanal, FLAC (PCM 16 bit). Yerel sürümde dosya yolu, yayımda gömülü ses.",
           local=True),
    Column("channel", "string", "prepare",
           "Kaynak kaydın geldiği YouTube kanalı (klasör adı). Konuşmacı kimliği değildir; bir kanalda birden çok okuyucu olabilir."),
    Column("source_id", "int", "prepare",
           "Kaynak kaydın hat içindeki numarası; aynı kayıttan kesilen kliplerde aynıdır.", local=True),
    Column("source_path", "string", "prepare",
           "Kaynak kaydın yerel dosya yolu. Yayımlanan sürümde herkese açık kaynak kimliğiyle (video kimliği) değiştirilir.",
           local=True),
    Column("source_sample_rate", "int", "prepare",
           "Kaynak kaydın kapsayıcıdaki gerçek örnekleme hızı. Klipler 24 kHz'e yeniden örneklenir; 24 kHz'in altındaki kaynaklar üst-örneklenmiş demektir, bu sütun onu ayırt eder.",
           unit="Hz"),
    Column("source_flags", "list[string]", "prepare",
           "Kaynak kayıt düzeyindeki işaretler. `truncated_source`: çözülen ses, kapsayıcının bildirdiği sürenin %95'inden kısa (bozuk/yarım indirme).",),
    Column("start", "float", "segment",
           "Klibin kaynak kayıt içindeki başlangıç zamanı; cümle sınırındaki kelime damgasından, sınır iyileştirmesi ve baş payı uygulanmış.",
           unit="s"),
    Column("end", "float", "segment", "Klibin kaynak kayıt içindeki bitiş zamanı; `start` gibi.", unit="s"),
    Column("duration", "float", "segment", "Klip süresi, `end - start`.", unit="s"),
    # ------------------------------------------------------------ metin
    Column("text_raw", "string", "asr",
           "ASR (Whisper large-v3) çıktısı, dokunulmamış; klibin kelime aralığından birleştirilmiş."),
    Column("text", "string", "segment",
           "Hafif temizlenmiş metin: boşluk, tırnak ve tekrar eden noktalama düzeltilmiş; sayı ve kısaltmalar olduğu gibi. Okunabilir/arşiv sürümü."),
    Column("text_spoken", "string", "segment",
           "Okunuşa çevrilmiş metin: sayılar, sıra sayıları, saat/tarih/para birimi ve yaygın kısaltmalar Türkçe okunuşuyla yazılmış. TTS eğitiminde kullanılması amaçlanan alan."),
    Column("n_words", "int", "segment",
           "Klipteki kelime sayısı (ASR kelimeleri, klitikler — de/da, mi, ki — bir önceki kelimeye bağlanmış)."),
    # ------------------------------------------------------------ transcript ve zaman damgası güveni
    Column("word_confidence", "float", "segment",
           "Klipteki kelimelerin en düşük olasılığı, `confidence_source`'a göre Whisper kelime olasılığı ya da hizalayıcı skoru. Tek bir nadir kelime (özel isim, ünlem) değeri düşürür; bir kapı değil, sıralama sinyalidir."),
    Column("word_confidence_mean", "float", "segment", "Aynı kaynaktan kelime olasılıklarının klip ortalaması."),
    Column("confidence_source", "string", "segment",
           "`word_confidence` sütunlarının kaynağı: `asr` (Whisper kelime olasılığı) ya da `align` (zorlamalı hizalama skoru)."),
    Column("align_score_min", "float", "align",
           "Zorlamalı hizalayıcının (MMS_FA, CTC) kelime başına ortalama kare olasılığının klipteki en düşüğü. Ses ile metnin uyuşmasını Whisper'dan bağımsız ölçer; 0 = hizalanamadı.",
           optional=True),
    Column("align_score_mean", "float", "align", "Hizalayıcı kelime skorlarının klip ortalaması.", optional=True),
    # ------------------------------------------------------------ kesim kalitesi
    Column("lead_gap_sec", "float", "segment",
           "Klibin ilk kelimesiyle kayıttaki bir önceki kelime arasındaki boşluk. Kaydın ilk kelimesiyse boş. Küçük değer, önceki cümlenin klibe bulaşma riskidir.",
           unit="s", optional=True),
    Column("trail_gap_sec", "float", "segment",
           "Klibin son kelimesiyle kayıttaki bir sonraki kelime arasındaki boşluk; kaydın son kelimesiyse boş.",
           unit="s", optional=True),
    Column("leading_silence_sec", "float", "clip_qc",
           "Klip başından VAD'ın (Silero) bulduğu ilk konuşmaya kadar geçen süre; "
           "paysız, kısa sessizlik eşikli ayrı VAD geçişinden.", unit="s"),
    Column("trailing_silence_sec", "float", "clip_qc",
           "VAD'ın son konuşmasından klip sonuna kadar geçen süre; aynı paysız geçişten.", unit="s"),
    Column("internal_silence_sec", "float", "clip_qc",
           "Klip içindeki en uzun konuşmasız aralık (VAD bölgeleri arasındaki en büyük boşluk).", unit="s"),
    Column("speech_ratio", "float", "clip_qc", "VAD'ın konuşma saydığı sürenin klip süresine oranı (0–1)."),
    # ------------------------------------------------------------ sinyal seviyesi
    Column("peak_dbfs", "float", "clip_qc", "Mutlak tepe örnek seviyesi.", unit="dBFS"),
    Column("rms_dbfs", "float", "clip_qc", "Klibin RMS seviyesi (kazanç uygulanmamış, kaynağın kendi seviyesi).", unit="dBFS"),
    Column("clip_ratio", "float", "clip_qc",
           "Tam ölçeğe dayanan örneklerin (|x| ≥ 0,99) oranı; dijital kırpılma ölçüsü."),
    Column("loudness_lufs", "float", "clip_qc",
           "BS.1770 tümleşik ses yüksekliği (pyloudnorm). Sese kazanç uygulanmaz; seviye normalizasyonu kullanıcıya bırakılır, bu sütun onun girdisidir. 0,4 s'lik ölçüm bloğundan kısa ya da tümüyle sessiz kliplerde boş.",
           unit="LUFS", optional=True),
    # ------------------------------------------------------------ arka plan müziği
    Column("music_score_audioset", "float", "music",
           "AudioSet AST sınıflandırıcısının müzik etiketleri (Music, Background music, Soundtrack…) üzerindeki azami skoru, klip pencereleri üzerinden en büyük değer. Ucuz eleme sinyali; konuşmayla birlikte var olabilir. Okunamayan klipte (`unreadable_audio`) boş.",
           optional=True),
    Column("music_to_speech_db", "float", "music",
           "Kaynak ayrıştırmasından (HDemucs) gelen fiziksel ölçü: eşlik (davul+bas+diğer) enerjisinin vokal enerjisine oranı. Ayrıştırıcı koşmadıysa taban değer −80. `background_music` işareti bu sütundan konfigdeki eşikle türetilir. Okunamayan klipte boş.",
           unit="dB", optional=True),
    Column("music_db_separated", "bool", "music",
           "Ayrıştırıcı bu klipte gerçekten koştu mu. Hayırsa `music_to_speech_db` ölçüm değil taban değerdir (AudioSet skoru eleme eşiğinin altındaydı). Okunamayan klipte boş.",
           optional=True),
    Column("music_stem_db", "dict[string,float]", "music",
           "Ayrıştırıcının dört bileşeninin (drums, bass, other, vocals) ayrı ayrı enerji seviyeleri; yalnızca ayrıştırıcının koştuğu kliplerde yazılır. `music_to_speech_db` bunlardan türetilir.",
           unit="dB", optional=True),
    # ------------------------------------------------------------ algısal kalite (DNSMOS P.835)
    Column("dnsmos_sig", "float", "dnsmos",
           "DNSMOS P.835 konuşma kalitesi kestirimi (SIG, 1–5): konuşmanın kendi bozulması. Referans uygulamayla birebir: 9,01 s pencereler, polinom eşleme, pencere ortalaması. Okunamayan klipte (`unreadable_audio`) boş.",
           optional=True),
    Column("dnsmos_bak", "float", "dnsmos",
           "DNSMOS P.835 arka plan kestirimi (BAK, 1–5): arka plan gürültüsünün rahatsızlığı; yüksek değer temiz demektir. Okunamayan klipte boş.",
           optional=True),
    Column("dnsmos_ovrl", "float", "dnsmos",
           "DNSMOS P.835 genel kalite kestirimi (OVRL, 1–5). Bir kapı değildir: politika kuralı ancak kör dinleme denetiminden sonra konabilir (politika v4 kaydı). Okunamayan klipte boş.",
           optional=True),
    # ------------------------------------------------------------ işaretler, yineleme, karar
    Column("flags", "list[string]", "export",
           "Klip işaretleri; hiçbiri klibi silmez. `forced_split`: tek başına süre tavanını aşan cümle iç noktalamasından bölündü; "
           "`gap_split`: aynı cümle uzun sessizlikte bölündü; `oversize`: bölünecek iç noktalama yok, cümle tavanı aşarak bütün bırakıldı; "
           "`short`: süre `segment.min_sec` altında; `background_music`: `music_to_speech_db` eşiğin üstünde; "
           "`duplicate`: aynı kayıt/kanal içinde aynı metnin tekrarı (bkz. `duplicate_of`); `boilerplate`: kanalın kayıtlarında tekrar eden künye/anons kalıbı; "
           "`unreadable_audio`: klip dosyası okunamadı, ölçümleri yok."),
    Column("duplicate_of", "string", "export",
           "Klip bir yinelemeyse korunan kopyanın kimliği; değilse boş. Yineleme, metnin aynı VE sesin aynı olmasıdır: ses kimliği `dedupe.identity_fields` (süre, LUFS, RMS, tepe) birebir tutuyorsa klip aynı kaydın kopyasıdır. Aynı metnin ayrı bir okuması yineleme DEĞİLDİR, prozodi çeşitliliği olarak tutulur; kanal anahtara girmez.",
           optional=True),
    # ------------------------------------------------------------ konuşmacı
    Column("speaker_id", "string", "export",
           "Kaydın konuşmacı kümesi (`spkNNNN`). Kümeleme korpusun tamamı üzerinde yapılır: birleştirme eşiği ölçülen iki dağılımın eşit hata noktasından alınır (kayıt içi klip benzerliği ve farklı kanalların kayıt benzerliği), küme sayısı verilmez. Kimlik kayıt düzeyindedir; kaydın bütün klipleri aynı değeri taşır. Kapı değildir, politikada kuralı yoktur.",
           optional=True),
    Column("speaker_consistency", "float", "speaker",
           "Kaydın gömülen kliplerinin birbirine kosinüs benzerliğinin ortalaması (0–1). Düşük değer kayıtta birden çok ses olduğunu gösterir (röportaj, çok sesli okuma) ve o kaydın tek konuşmacı gibi ele alınamayacağını söyler.",
           optional=True),
    Column("speaker_margin", "float", "export",
           "Kaydın kendi küme merkezine benzerliği eksi en yakın diğer kümeye benzerliği. Küçük değer kümeler arası sınıra yakın bir kaydı işaret eder; negatif değer yanlış kümede olabileceğini söyler.",
           optional=True),
    Column("recommended", "bool", "export",
           "Sürümlü politikanın (`recommended_subset`) bu klibi varsayılan eğitim alt kümesine önerip önermediği. Veri elemez; kullanıcı ölçüm sütunlarından kendi kuralını koyabilir."),
    Column("exclusion_reasons", "list[string]", "export",
           "`recommended=false` ise sağlanmayan kuralların listesi: `metrik<eşik`, `metrik>eşik`, `isaret:ad[,ad]`, `eksik_olcum:metrik`. Önerilen kliplerde boş."),
    Column("policy_version", "string", "export",
           "`recommended` ve `exclusion_reasons`'ı üreten politika sürümü; kurallar konfigde sürümlüdür ve değişince yalnızca bu üç sütun yeniden hesaplanır."),
)

BY_NAME = {c.name: c for c in COLUMNS}


def column_names(*, published_only: bool = False) -> list[str]:
    return [c.name for c in COLUMNS if not (published_only and c.local)]


def check_manifest(rows: Iterable[dict], *, columns: Sequence[Column] = COLUMNS) -> tuple[set[str], set[str]]:
    """(şemada olup manifestoda hiç görünmeyen zorunlu sütunlar, manifestoda olup şemada olmayan anahtarlar)."""
    seen: set[str] = set()
    for r in rows:
        seen |= set(r)
    required = {c.name for c in columns if not c.optional}
    known = {c.name for c in columns}
    return required - seen, seen - known


def check_manifest_file(path: Path) -> tuple[set[str], set[str]]:
    with Path(path).open(encoding="utf-8") as fh:
        return check_manifest(json.loads(line) for line in fh if line.strip())


def markdown_table(*, published_only: bool = True) -> str:
    lines = ["| sütun | tür | birim | aşama | açıklama |", "|---|---|---|---|---|"]
    for c in COLUMNS:
        if published_only and c.local:
            continue
        name = f"`{c.name}`" + (" (isteğe bağlı)" if c.optional else "")
        desc = c.description.replace("|", "\\|")
        lines.append(f"| {name} | {c.dtype} | {c.unit} | {c.stage} | {desc} |")
    return "\n".join(lines)
