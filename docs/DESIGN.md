# Tasarım: v1'in kusurları ve v2'nin kararları

Bu belge, `turkish-tts-audiobooks` (v1) hattının ürettiği yayımlanmış korpus
üzerinde yapılan ölçümleri ve her ölçümün kiraat'ta hangi tasarım kararına yol
açtığını kaydeder. Sayılar v1'in yayımlanan manifestolarından ve durum
veritabanından, 27–28 Ağustos 2026'da doğrudan sayıldı.

## Hata kaydı — özet

| # | v1'in kusuru | ölçü | v2'nin kararı |
|---|---|---|---|
| 1 | sessizlikte kesim cümleyi böler | `train`'in %9,4'ü cümle ortasından başlıyor | ASR sonrası, cümle sınırında kesim |
| 2 | doğrulanmamış sınıflandırıcı kapı yapıldı | 981,3 saat tek gerekçeyle elendi, 131 denetim klibinde 0 doğru pozitif | hiçbir aşama karar veremez |
| 3 | normalizasyon yuvası boş | `text_normalized` ≡ `text` | `text_spoken` gerçekten üretilir |
| 4 | yineleme yanlış düzeyde | `train`'de 281 gerçek, 4.027 kanal içi kopya | anahtar (metin, konuşmacı) |
| 5 | anons/künye metinleri sızdı | tek bir künye 32 kez | kanal düzeyinde boilerplate madenciliği |
| 6 | gerçek held-out yok | `validation`'ın %5,9'u `train` ile aynı metin | ayrı, elle doğrulanmış `test` |
| 7 | müzik ölçüsünün fiziksel karşılığı yok | AudioSet 0,444 → hiç müzik yok; 0,050 → −15,7 dB | ayrıştırma tabanlı dB sütunu |
| 8 | konuşmacı kümeleme doygun | iki baskın kanalda 64 tavanı dolu, küme başına ~2.500 klip | tavan yok, kayıt-içi doğrulama |
| 9 | ses seviyesi dağınık | %5–%95 arası 12,5 LU, kanal medyanları arası 18,4 LU | hedefli LUFS + sütun olarak yayım |
| 10 | üç metin alanı tek alan | `text` ≠ `text_raw` yalnızca %2,39 | üç alan gerçekten farklı |
| 11 | 16 kHz tavanı | — | 24 kHz taban |
| 12 | ASR güven ölçüsü yanlış şeyi ölçüyor | iki geçiş CER medyanı 0,000 | zorlamalı hizalama güveni |

Her satırın ayrıntısı ve gerekçesi aşağıda.

## 1. Sessizlikte kesmek cümleyi ortadan böler

Yayımlanan `train` havuzu, 416.315 klip:

| ölçüm | klip | oran |
|---|---|---|
| küçük harfle başlıyor (cümle ortasından giriş) | 39.220 | %9,4 |
| cümle sonu noktalaması yok (cümle ortasında bitiş) | 59.004 | %14,2 |
| iki ucu birden kırık | 12.105 | %2,9 |

Kaynağı 20 saniyelik sert süre sınırı değil: sınıra dayanan klip yalnızca
%0,5 (2.090 klip), süre medyanı 11,03 s. Kusur eşik ayarından değil,
sıralamadan geliyor — hat sessizlikte kesiyor, cümlede değil. Seslendiren
virgülde nefes alır, iki cümle arasında almayabilir; VAD bu ikisini ayırt
edemez.

**Karar.** Sıralama tersine çevrildi: uzun formda ASR + kelime zaman damgası
→ transcript üzerinde cümle bölütleme → cümle sınırında kesim. VAD korunur
ama yalnızca ASR'ye verilecek konuşma bölgelerini bulur. Tek istisna, tek
başına üst sınırı aşan cümlenin iç noktalamasından bölünmesidir; o klipler
`forced_split` işareti taşır ve önerilen alt kümeye girmez.
Uygulama: [`kiraat/segment.py`](../kiraat/segment.py).

## 2. Doğrulanmamış bir sınıflandırıcıyı kapı yapmak

v1, AudioSet AST'nin "Speech synthesizer" başlığını sentetik anlatım kapısı
olarak kullandı. Sonuç:

- `review` havuzundaki 432.306 klibin 358.934'ü bu işareti taşıyor.
- Bunların **289.430'u (981,3 saat) başka hiçbir gerekçe taşımıyor** — tek
  suçları bu sınıflandırıcı.
- Kör dinleme denetimi (240 klip, 24 kanalın her birinden 10'ar): 131
  işaretli klibin **131'i de insan anlatımı**. Sıfır doğru pozitif; üçler
  kuralıyla işaretli kliplerdeki gerçek sentetik oranı %95 güvenle en fazla
  %2,3.

Bedeli yalnızca saat değil, çeşitlilik. Kurtarılabilir 981 saatin dağılımı,
korpusun en büyük dengesizliğinin doğrudan sebebi:

| kanal | temiz (sa) | filtreye takılan (sa) |
|---|---|---|
| dinleyiniz | 26,9 | 215,0 |
| ses-arşiv | 8,5 | 126,6 |
| cantadakitap | 5,0 | 111,8 |
| ZubeyirSener | 28,5 | 99,8 |
| kitapdinle | 0,1 | 73,6 |
| seslikitaplarmavi | 560,6 | 32,1 |
| BirDinle | 480,0 | 8,2 |

İki baskın kanalın temiz saatlerdeki payı %79; bu klipler geri alınsaydı
%47'ye düşecekti.

**Karar.** Hiçbir aşama karar veremez. Klip aşamaları yalnızca ölçüm üretir
ve `ClipStage.validate_output` bir aşamanın `recommended`/`decision` alanı
yazmasını hata olarak reddeder. Önerilen alt küme, konfigdeki sürümlü kural
listesinden hesaplanır. AudioSet skoru yayımlanır ama varsayılan politikada
kural olarak kullanılmaz (`events.gate_synthetic: false`).
Uygulama: [`kiraat/scoring.py`](../kiraat/scoring.py), [`kiraat/base.py`](../kiraat/base.py).

## 3. Boş normalizasyon yuvası

v1'de `text_normalized`, `text` ile bayt bayt aynıydı. Bir TTS korpusunda
sayıların, kısaltmaların, saatlerin ve para birimlerinin okunuşa çevrilmesi
işin yarısıdır; model "1923" dizgesini değil "bin dokuz yüz yirmi üç" sesini
öğrenir.

**Karar.** Üç alan da yayımlanır ve üçü de farklıdır: `text_raw` (ASR
çıktısı), `text` (hafif temizlik), `text_spoken` (okunuşa çevrilmiş, eğitimde
kullanılan). Uygulama: [`kiraat/text/normalize.py`](../kiraat/text/normalize.py).

## 4. Yineleme kuralı yanlış düzeyde

Yayımlanan havuzlarda fazladan kopyalar:

| kapsam | train | review |
|---|---|---|
| aynı kayıt içinde (gerçek yineleme) | 281 | 278 |
| aynı kanal, farklı kayıt | 4.027 | 19.690 |
| farklı kanal (prozodi için değerli) | 863 | 2.495 |

Doğru kural metnin kendisi değil, (metin, konuşmacı) çiftidir: aynı metin
aynı sesle tekrar ediyorsa yinelemedir, farklı sesle okunuyorsa prozodi
çeşitliliğidir ve tutulur.

**Karar.** `dedupe.mark_duplicates` bu çifti anahtar alır, grupta en iyi
klibi korur, diğerlerine `duplicate_of` ve `duplicate` işareti yazar —
silmez. Uygulama: [`kiraat/dedupe.py`](../kiraat/dedupe.py).

## 5. Anons ve künye metinleri eğitime sızıyor

`train` içinde en çok tekrar eden metinler seslendiren künyeleri ve kanal
anonsları: "Son Seslendiren Vasfiye Sarıkaya" 32 kez, "Seslendiren Vasfiye
Sarıkaya" 13 kez, köşe yazarı imzaları 6–8 kez. `review` havuzunda ayrıca
klasik Whisper halüsinasyonları var: "İzlediğiniz için teşekkür ederim."
152 kez, "Altyazı M.K." 48 kez.

**Karar.** Kanal düzeyinde tekrar eden ifadeleri madenleyen bir boilerplate
aşaması, kayıt başı/sonu bölgelerine ağırlık vererek çalışır ve bulduklarını
`boilerplate` işaretiyle damgalar. ASR tarafında `condition_on_previous_text`
kapatılır; halüsinasyon zincirini kıran ayar budur.

## 6. Gerçek bir held-out yok

`review`, `train` ile kayıt düzeyinde örtüşüyor. `validation`'ın 8.502
klibinin 501'i (%5,9) `train` ile birebir aynı normalleştirilmiş metni
paylaşıyor, dağılımı da eşleşmiyor (medyan süre 7,0 s'ye karşı 11,0 s).

**Karar.** Ayrı bir `test` bölümü: kayıtları hiçbir eğitim bölümüyle
paylaşmayan, metin örtüşmesi sıfıra indirilmiş, kanal dengeli ve elle
doğrulanmış. Akademik yayın için savunulabilir tek yapı budur.

## Yayın açısından

v1 deneysiz bir kaynak makalesiydi. v2'nin elinde taban var: aynı 2.942
saatlik ham malzeme, iki farklı bölütleme stratejisi. Ölçülebilir iki katkı
çıkıyor — sessizlik hizalı kesimin cümle bütünlüğüne maliyeti (%9,4 kırık
giriş → 0), ve doğrulanmamış bir sınıflandırıcıyı kapı yapmanın maliyeti
(981 saat ve kanal çeşitliliği). İkisi de v1 verisiyle kanıtlanabilir.

## 7. Arka plan müziği: sütun zaten vardı, sorusu yanlıştı

v1 bu sütunu yayımlıyor — her satırda `quality_music_score`, AudioSet AST'nin
müzik etiketleri (Music, Background music, Soundtrack music, Singing,
Jingle...) üzerinden pencere bazında azami skor. Yayımlanan dağılım:

| havuz | medyan | p90 | p99 | ≥0,2 | ≥0,5 |
|---|---|---|---|---|---|
| train | 0,002 | 0,008 | 0,165 | %0,6 | %0,0 |
| review | 0,001 | 0,418 | 0,669 | %15,4 | %7,3 |

Üst değerler eşiklerin izidir: 0,70 üstü sert eleme (hiç yüklenmedi), 0,25
üstü `sinirda_muzik`. Yani sinyal bilgilendirici ve zaten elde.

Eksik olan, ölçünün **fiziksel bir karşılığının olmaması**. 0,418'lik bir
AudioSet skoru "müzik ne kadar yüksek" sorusunu yanıtlamaz; eşik seçimi de
bu yüzden keyfî kalır.

**Karar.** Üç sütun birden yayımlanır. `music_score_audioset` ucuz ve çok
etiketli sinyaldir (konuşmayla birlikte var olabilir). `music_to_speech_db`
kaynak ayrıştırmasından gelen fiziksel ölçüdür — eşlik enerjisinin konuşma
enerjisine oranı; −30 dB duyulmaz, −10 dB belirgin müzik. `music_prob_external`
isteğe bağlı bir dış sınıflandırıcının olasılığıdır. İkili `background_music`
yanıtı yayımlanan `music_to_speech_db` sütunundan konfigdeki eşikle türetilir,
yani kullanıcı veriyi yeniden üretmeden kendi eşiğini kesebilir.

**Ölçüldü.** 70 klip, v1'in AudioSet skorunun beş bandından katmanlı
örneklemeyle çekildi ve her biri hem AudioSet skoruyla hem ayrıştırma tabanlı
dB ölçüsüyle ölçüldü. Sıra korelasyonları:

| sinyal | müzik/konuşma dB ile rho |
|---|---|
| AudioSet müzik skoru (çok etiketli) | **+0,799** |
| `AIGenLab/speech-music-classifier-v3` (ikili) | +0,311 |

AudioSet skoru güçlü bir yordayıcı ama tek başına yeterli değil: örneklemde
AudioSet 0,444 olan bir klipte hiç müzik yok (−80 dB), AudioSet 0,673 olan
bir klipte müzik konuşmanın 33 dB altında, yani duyulmuyor. v1'in 0,25'lik
`sinirda_muzik` eşiği bu yüzden hem yanlış işaretliyor hem kaçırıyordu;
0,050 skorlu bir klipte müzik −15,7 dB, yani açıkça duyulur.

İkili modeller üzerine not: `AIGenLab/AST-speech-music-classifier` ve
`AIGenLab/speech-music-classifier-v3`, `id2label = {0: music, 1: speech}`
olan **birbirini dışlayan** sınıflandırıcılardır (AST tabanlı 86,2M; whisper-
small tabanlı 88,4M, ikisinin de yayımlanmış başarımı yok, AST olanın model
kartı hiç yok). Yanıtladıkları soru "bu klip konuşma mı müzik mi", sorulan
soru "konuşmanın altında müzik var mı". Ölçüm bunu doğruladı: müziği hiç
olmayan kliplere 0,999 ve 0,915, müziği −22 dB'de açıkça duyulan kliplere
0,006 ve 0,009 verdiler. Bu yüzden varsayılan konfigde kapalılar; istenirse
`music.external_model` ile üçüncü bir skor sütunu olarak yayımlanırlar ama
politikada kural olamazlar.

Uygulama: [`kiraat/stages/music.py`](../kiraat/stages/music.py), ölçüm betiği
[`scripts/probe_music.py`](../scripts/probe_music.py).

## 8. Konuşmacı kümeleme doygun, üstelik tam yanlış yerde

`speaker_id`, kanal içinde açgözlü en-yakın-merkez kümelemeyle üretiliyor:
kosinüs 0,75, kanal başına en çok 64 küme. Tavan üç kanalda doldu ve
bunlardan ikisi korpusun %79'unu taşıyan kanallar:

| kanal | küme | klip | küme başına klip |
|---|---|---|---|
| seslikitaplarmavi | 64 (tavan) | 172.933 | 2.702 |
| BirDinle | 64 (tavan) | 158.884 | 2.483 |
| OkumaSaati | 64 (tavan) | 7.202 | 113 |

Tavan dolduğunda yeni seslendiren kendi kümesini açamaz, en yakın mevcut
kümeye yazılır. Yani korpusun büyük kısmında `speaker_id`, ayrı
seslendirenleri birleştirmiş bir etikettir. TTS'te konuşmacı kimliği
koşullama sinyali olduğu için bu, kusurlu değil doğrudan yanıltıcı bir alan.

**Karar.** Kanal başına küme tavanı kaldırılır; kümeleme kayıt düzeyinde
doğrulanır (bir kaydın baskın kümesi ile klip kümesi tutarlı olmalı) ve
kümeleme güveni `speaker_cluster_margin` olarak yayımlanır. Küme sayısı
veriden çıkar, konfigden değil.

## 9. Ses seviyesi normalize edilmedi

Karar bilinçliydi ve kartta yazılı, ama TTS için bedeli var. `train`
havuzunda bütünleşik ses yüksekliği %5–%95 arasında **12,5 LU** yayılıyor;
kanal medyanları arasında fark daha da büyük: `idea_stüdyo` −34,7 LUFS,
`kitaplar` −16,3 LUFS, arada 18,4 LU var. Model bu haliyle ses yüksekliğini
keyfî bir değişken olarak öğrenir.

**Karar.** Kaynak düzeyinde hedefli LUFS uygulanır (klip başına değil, ki
doğal dinamik korunsun), uygulanan kazanç ve ölçülen LUFS sütun olarak
yayımlanır. Normalizasyonu istemeyen kullanıcı kazancı geri alabilir.

## 10. Üç metin alanı aslında tek alan

`text` ile `text_raw` yayımlanan `train` kliplerinin yalnızca **%2,39'unda**
farklı; `text_normalized` ise hiç farklı değil. Üç sütun yayımlandı ama
bilgi tek sütunluk.

**Karar.** `text_raw` (ASR çıktısı), `text` (hafif temizlik),
`text_spoken` (okunuşa çevrilmiş). Üçüncüsü [§3](#3-boş-normalizasyon-yuvası)
ile birlikte gerçekten üretilir; hangi dönüşümlerin uygulandığı klip başına
`text_ops` listesinde yayımlanır.

## 11. 16 kHz tavanı

v1 16 kHz mono yayımladı. Bu, korpusu güncel TTS mimarilerinin çoğu için
üst sınırdan mahrum bırakıyor ve kaynak kayıtların çoğu daha yüksek hızda.

**Karar.** 24 kHz taban (`prepare.target_sr`), kaynak daha düşükse yükseltme
yapılmaz ve gerçek kaynak hızı `source_sample_rate` sütununda yayımlanır.

## 12. İki geçişli ASR uyuşması yanlış şeyi ölçüyor

v1'in transcript güvenilirlik sinyali, aynı modelin iki geçişi arasındaki
CER'di. Yayımlanan `train` havuzunda bu değerin **medyanı 0,000**, p95'i
0,018. Kararlı bir çözücü kendisiyle, ikisi de yanlışken bile uyuşur; ölçülen
şey doğruluk değil çözücü kararlılığı. (İnsan referanslı denetimde temiz
havuz CER'i 0,0012 çıktı — yani transcript'ler gerçekten iyi, ama bunu
gösteren şey iki geçiş uyuşması değil, o ayrı denetimdi.)

**Karar.** Güven sinyali zorlamalı hizalamadan gelir: kelime başına hizalama
olasılığı, klip başına asgarisi ve ortalaması sütun olarak yayımlanır
(`word_confidence`). Bu hem transcript'i hem zaman damgalarını sınar ve
zaman damgaları zaten bölütlemenin dayanağıdır.
