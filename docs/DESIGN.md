# Tasarım: v1'in kusurları ve v2'nin kararları

Bu belge, `turkish-tts-audiobooks` (v1) hattının ürettiği yayımlanmış korpus
üzerinde yapılan ölçümleri ve her ölçümün kiraat'ta hangi tasarım kararına yol
açtığını kaydeder. Sayılar v1'in yayımlanan manifestolarından ve durum
veritabanından, 27–28 Ağustos 2026'da doğrudan sayıldı.

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
