# kiraat

Türkçe okuma-konuşma (read-speech) korpusu üretim hattı; `turkish-tts-audiobooks`
(v1) hattının yerine geçer. v1'in ölçülmüş kusurları ve her birinin yol açtığı
tasarım kararı [`docs/DESIGN.md`](docs/DESIGN.md) başındaki on iki maddelik
tabloda; yeni bir şey yazmadan önce o tabloya bakılır.

## Bozulmaması gereken iki değişmez

**Kesim cümle sınırındadır.** Bölütleme, VAD'ın bulduğu sessizliklerde değil,
ASR + zorlamalı hizalamadan gelen kelime zaman damgaları üzerinde cümle
sınırlarında yapılır. v1'de sessizlikte kesmek yayımlanan havuzun %9,4'ünü
cümle ortasından başlattı. `tests/test_segment.py` bu sözleşmeyi sınar:
üretilen hiçbir klip küçük harfle başlamaz.

**Hiçbir eşik klip elemez.** Klip aşamaları yalnızca ölçüm üretir; karar,
konfigdeki sürümlü `recommended_subset` politikasının işidir ve her dışlamanın
gerekçesi kayda yazılır. `ClipStage.validate_output`, bir aşamanın çıktısına
`recommended`/`decision` yazmasını hata olarak reddeder. v1'de doğrulanmamış
bir sınıflandırıcıyı kapı yapmak 981 saati ve korpusun kanal çeşitliliğini
sildi. Yeni bir sinyal kapı olmadan önce kör dinleme denetiminden geçer.

## Çalışma yöntemi

**Tam korpus tek seferde işlenmez.** Her aşama önce birkaç kayıtlık bir
örnekte koşturulur, çıktısı somut olarak gösterilir — ölçülen sayılar, örnek
transcript'ler, dinlenebilir klipler — ve ancak doğrulandıktan sonra ölçek
büyütülür. Tam koşu, hattın tamamı doğrulanmadan ve açık onay alınmadan
başlatılmaz. `runtime.max_sources` varsayılan olarak 5'tir ve bilinçli olarak
küçüktür; büyütmek bir karardır, varsayılan değil.

Bunun sebebi v1: kusurların hepsi korpus yayımlandıktan sonra görüldü, oysa
hepsi birkaç yüz kliplik bir örnekte görünürdü. Her aşamanın yanında
çıktısını gözle denetlenebilir kılan küçük bir betik bulunur;
[`scripts/probe_music.py`](scripts/probe_music.py) bunun örüntüsüdür.

## Çalıştırma

Testler ve model işleri base conda ortamında koşmaz:

```bash
/home/serdar/miniconda3/envs/main/bin/python -m pytest
```

O ortamda torch/torchaudio/transformers ve bir RTX 3090 var. Kaynak
ayrıştırması için ayrı `demucs` paketi yok; torchaudio'nun
`HDEMUCS_HIGH_MUSDB_PLUS` paketi kullanılır.

## Sınırlar

Eşikler koda gömülmez, hepsi [`configs/default.yaml`](configs/default.yaml)
içindedir; `Config.load` bilinmeyen bölüm veya anahtarı sessizce yutmaz, hata
verir. v1'in verisi taban ölçümü için okunur ama bu depoya kopyalanmaz;
yayımlanmış v1 veri kümesi, kartı ve makalesi ayrı bir projede (`voxcpm`)
yürür ve oraya yeni hat özelliği eklenmez.

Türkçe metinde `str.lower()`/`str.upper()` kullanılmaz — `kiraat.text.turkish`
içindeki `lower`/`upper` kullanılır, çünkü I/ı ve i/İ eşlemesi farklıdır.
