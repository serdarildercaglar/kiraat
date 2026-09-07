---
license: cc-by-4.0
language:
- tr
task_categories:
- text-to-speech
- automatic-speech-recognition
pretty_name: KIRAAT — Türkçe okuma-konuşma korpusu
size_categories:
- 1M<n<10M
tags:
- speech
- turkish
- read-speech
- tts
- audiobook
---

# KIRAAT — Türkçe okuma-konuşma korpusu

Türkçe sesli kitap **YouTube kanallarından toplanmış kamuya açık
kayıtlardan** üretilmiş, cümle hizalı bir okuma-konuşma (read-speech)
korpusu. Kanal künyesi aşağıdaki tabloda; her klip hangi kanaldan geldiğini
`channel` sütununda taşır.

| | |
|---|---|
| klip | **1.840.404** |
| süre | **3.105,7 saat** |
| önerilen alt küme | **1.547.494 klip / 2.575,2 saat** |
| kanal | 27 |
| konuşmacı (kümeleme) | **90** |
| kaynak kayıt | 2.680 |
| ses | 24 kHz, mono, FLAC |
| dil | Türkçe |

## Bu korpusu ayıran iki şey

**Kesim cümle sınırındadır.** Klipler sessizlikte değil, ASR ve zorlamalı
hizalamadan gelen kelime zaman damgaları üzerinde cümle sınırlarında
kesilir. Bunun ölçülmüş karşılığı var: aynı kayıtlarda sessizlik hizalı
kesimle karşılaştırıldığında (27 kanaldan 206 kayıt, 240,5 saat), sessizlik
hizalı kesimde kliplerin **%12,81'i cümle ortasından başlıyor ve bunu
gösteren hiçbir işaret taşımıyor**; cümle hizalı kesimde bu oran **%0,00**
(kırık başlangıçların tamamı `forced_split` ya da künye işaretiyle
görünür).

**Hiçbir eşik klip elemez.** Kalite ölçümleri sütun olarak yayımlanır;
hangi kliplerin varsayılan eğitim alt kümesine gireceğini sürümlü bir
politika belirler ve her dışlamanın gerekçesi `exclusion_reasons`
sütununda yazılıdır. Politikanın kendisi de kör dinleme denetiminden
geçmiştir: alandaki iki standart kalite eşiği (`clip_ratio`,
`word_confidence`) denetimde tutunamadığı için kaldırıldı. Kendi eşiğinizi
sütunlardan kesebilirsiniz; `recommended=false` olan klipler silinmemiştir.

## Bölmeler

| bölme | klip | saat | kayıt | kanal | konuşmacı |
|---|---|---|---|---|---|
| train | 1.512.448 | 2.517,08 | 2.579 | 27 | 89 |
| dev | 5.750 | 9,54 | 40 | 27 | 26 |
| test | 5.473 | 9,30 | 45 | 27 | 26 |

Bölme **kayıt düzeyindedir**: bir kaydın klipleri tek bölmeye girer, yani
değerlendirme modelin hiç duymadığı bir kayıt üzerinde yapılır. `dev` ve
`test` kanal dengelidir (kanal başına eşit süre hedefi). Metin sızıntısı
denetlenmiş ve temizlenmiştir: `train` ile birebir aynı cümleyi taşıyan
dev/test klipleri düşürüldü, kalan örtüşme **sıfır**.

Konuşmacı örtüşmesi bilinçli olarak bırakılmıştır: test'in 26
konuşmacısından 25'i `train`'de de geçer, yani bu **görülmüş konuşmacı**
değerlendirmesidir. Görülmemiş konuşmacı deneyi isteyen `speaker_id`
sütunundan kendi bölmesini kurabilir.

## Nasıl üretildi

ffmpeg ile 24 kHz mono çözme → faster-whisper `large-v3` ile uzun form ASR
(kelime damgalı) → torchaudio `MMS_FA` ile zorlamalı hizalama → kanal
düzeyinde künye/anons madenciliği → cümle sınırında bölütleme ve ses
tabanlı sınır iyileştirme → klip ölçümleri (VAD konuşma oranı, sessizlikler,
seviye, BS.1770 ses yüksekliği; HDemucs + AudioSet ile müzik; DNSMOS P.835;
ECAPA-TDNN ile konuşmacı gömmesi) → sürümlü politika ile önerilen alt küme.

Bütün ağırlık revizyonları ve aşama sürümleri koşu kaydında (`run.json`)
sabittir; hattın kodu açık: <https://github.com/serdarildercaglar/kiraat>.

## Kalite dağılımları (önerilen alt küme)

| sütun | p05 | p50 | p95 |
|---|---|---|---|
| süre (s) | 2,76 | 5,82 | 10,56 |
| `loudness_lufs` | −27,99 | −20,92 | −12,54 |
| `dnsmos_ovrl` | 2,862 | 3,296 | 3,491 |
| `dnsmos_sig` | 3,271 | 3,563 | 3,710 |
| `dnsmos_bak` | 3,631 | 4,109 | 4,210 |
| `speech_ratio` | 0,851 | 0,977 | 1,000 |
| `align_score_mean` | 0,858 | 0,961 | 0,994 |
| `n_words` | 5 | 11 | 21 |

Korpusun tamamında kliplerin **%83,6'sı** `dnsmos_ovrl ≥ 3,0` — alanda
sık kullanılan eşik. Ses **normalize edilmemiştir**; seviye sütun olarak
verilir, kararı kullanıcıya bırakılır.

## Önerilen alt küme politikası (v6)

`recommended=true` olması için: `speech_ratio ≥ 0,60`,
`internal_silence_sec ≤ 1,0` ve şu işaretlerden hiçbirinin bulunmaması —
`oversize`, `forced_split`, `gap_split`, `short`, `duplicate`,
`boilerplate`, `background_music`.

Yineleme tanımı: metnin aynı **ve** sesin aynı olması (süre, LUFS, RMS,
tepe birebir). Aynı metnin ayrı bir okuması yineleme sayılmaz, prozodi
çeşitliliği olarak tutulur.

## Sütunlar

| sütun | tür | birim | aşama | açıklama |
|---|---|---|---|---|
| `id` | string |  | segment | Klip kimliği: `srcNNNNN-KKKKK`; kaynak kaydın numarası ve klibin kayıt içindeki sırası. |
| `channel` | string |  | prepare | Kaynak kaydın geldiği YouTube kanalı (klasör adı). Konuşmacı kimliği değildir; bir kanalda birden çok okuyucu olabilir. |
| `source_sample_rate` | int | Hz | prepare | Kaynak kaydın kapsayıcıdaki gerçek örnekleme hızı. Klipler 24 kHz'e yeniden örneklenir; 24 kHz'in altındaki kaynaklar üst-örneklenmiş demektir, bu sütun onu ayırt eder. |
| `source_flags` | list[string] |  | prepare | Kaynak kayıt düzeyindeki işaretler. `truncated_source`: çözülen ses, kapsayıcının bildirdiği sürenin %95'inden kısa (bozuk/yarım indirme). |
| `start` | float | s | segment | Klibin kaynak kayıt içindeki başlangıç zamanı; cümle sınırındaki kelime damgasından, sınır iyileştirmesi ve baş payı uygulanmış. |
| `end` | float | s | segment | Klibin kaynak kayıt içindeki bitiş zamanı; `start` gibi. |
| `duration` | float | s | segment | Klip süresi, `end - start`. |
| `text_raw` | string |  | asr | ASR (Whisper large-v3) çıktısı, dokunulmamış; klibin kelime aralığından birleştirilmiş. |
| `text` | string |  | segment | Hafif temizlenmiş metin: boşluk, tırnak ve tekrar eden noktalama düzeltilmiş; sayı ve kısaltmalar olduğu gibi. Okunabilir/arşiv sürümü. |
| `text_spoken` | string |  | segment | Okunuşa çevrilmiş metin: sayılar, sıra sayıları, saat/tarih/para birimi ve yaygın kısaltmalar Türkçe okunuşuyla yazılmış. TTS eğitiminde kullanılması amaçlanan alan. |
| `n_words` | int |  | segment | Klipteki kelime sayısı (ASR kelimeleri, klitikler — de/da, mi, ki — bir önceki kelimeye bağlanmış). |
| `word_confidence` | float |  | segment | Klipteki kelimelerin en düşük olasılığı, `confidence_source`'a göre Whisper kelime olasılığı ya da hizalayıcı skoru. Tek bir nadir kelime (özel isim, ünlem) değeri düşürür; bir kapı değil, sıralama sinyalidir. |
| `word_confidence_mean` | float |  | segment | Aynı kaynaktan kelime olasılıklarının klip ortalaması. |
| `confidence_source` | string |  | segment | `word_confidence` sütunlarının kaynağı: `asr` (Whisper kelime olasılığı) ya da `align` (zorlamalı hizalama skoru). |
| `align_score_min` (isteğe bağlı) | float |  | align | Zorlamalı hizalayıcının (MMS_FA, CTC) kelime başına ortalama kare olasılığının klipteki en düşüğü. Ses ile metnin uyuşmasını Whisper'dan bağımsız ölçer; 0 = hizalanamadı. |
| `align_score_mean` (isteğe bağlı) | float |  | align | Hizalayıcı kelime skorlarının klip ortalaması. |
| `lead_gap_sec` (isteğe bağlı) | float | s | segment | Klibin ilk kelimesiyle kayıttaki bir önceki kelime arasındaki boşluk. Kaydın ilk kelimesiyse boş. Küçük değer, önceki cümlenin klibe bulaşma riskidir. |
| `trail_gap_sec` (isteğe bağlı) | float | s | segment | Klibin son kelimesiyle kayıttaki bir sonraki kelime arasındaki boşluk; kaydın son kelimesiyse boş. |
| `leading_silence_sec` | float | s | clip_qc | Klip başından VAD'ın (Silero) bulduğu ilk konuşmaya kadar geçen süre; paysız, kısa sessizlik eşikli ayrı VAD geçişinden. |
| `trailing_silence_sec` | float | s | clip_qc | VAD'ın son konuşmasından klip sonuna kadar geçen süre; aynı paysız geçişten. |
| `internal_silence_sec` | float | s | clip_qc | Klip içindeki en uzun konuşmasız aralık (VAD bölgeleri arasındaki en büyük boşluk). |
| `speech_ratio` | float |  | clip_qc | VAD'ın konuşma saydığı sürenin klip süresine oranı (0–1). |
| `peak_dbfs` | float | dBFS | clip_qc | Mutlak tepe örnek seviyesi. |
| `rms_dbfs` | float | dBFS | clip_qc | Klibin RMS seviyesi (kazanç uygulanmamış, kaynağın kendi seviyesi). |
| `clip_ratio` | float |  | clip_qc | Tam ölçeğe dayanan örneklerin (\|x\| ≥ 0,99) oranı; dijital kırpılma ölçüsü. |
| `loudness_lufs` (isteğe bağlı) | float | LUFS | clip_qc | BS.1770 tümleşik ses yüksekliği (pyloudnorm). Sese kazanç uygulanmaz; seviye normalizasyonu kullanıcıya bırakılır, bu sütun onun girdisidir. 0,4 s'lik ölçüm bloğundan kısa ya da tümüyle sessiz kliplerde boş. |
| `music_score_audioset` (isteğe bağlı) | float |  | music | AudioSet AST sınıflandırıcısının müzik etiketleri (Music, Background music, Soundtrack…) üzerindeki azami skoru, klip pencereleri üzerinden en büyük değer. Ucuz eleme sinyali; konuşmayla birlikte var olabilir. Okunamayan klipte (`unreadable_audio`) boş. |
| `music_to_speech_db` (isteğe bağlı) | float | dB | music | Kaynak ayrıştırmasından (HDemucs) gelen fiziksel ölçü: eşlik (davul+bas+diğer) enerjisinin vokal enerjisine oranı. Ayrıştırıcı koşmadıysa taban değer −80. `background_music` işareti bu sütundan konfigdeki eşikle türetilir. Okunamayan klipte boş. |
| `music_db_separated` (isteğe bağlı) | bool |  | music | Ayrıştırıcı bu klipte gerçekten koştu mu. Hayırsa `music_to_speech_db` ölçüm değil taban değerdir (AudioSet skoru eleme eşiğinin altındaydı). Okunamayan klipte boş. |
| `music_stem_db` (isteğe bağlı) | dict[string,float] | dB | music | Ayrıştırıcının dört bileşeninin (drums, bass, other, vocals) ayrı ayrı enerji seviyeleri; yalnızca ayrıştırıcının koştuğu kliplerde yazılır. `music_to_speech_db` bunlardan türetilir. |
| `dnsmos_sig` (isteğe bağlı) | float |  | dnsmos | DNSMOS P.835 konuşma kalitesi kestirimi (SIG, 1–5): konuşmanın kendi bozulması. Referans uygulamayla birebir: 9,01 s pencereler, polinom eşleme, pencere ortalaması. Okunamayan klipte (`unreadable_audio`) boş. |
| `dnsmos_bak` (isteğe bağlı) | float |  | dnsmos | DNSMOS P.835 arka plan kestirimi (BAK, 1–5): arka plan gürültüsünün rahatsızlığı; yüksek değer temiz demektir. Okunamayan klipte boş. |
| `dnsmos_ovrl` (isteğe bağlı) | float |  | dnsmos | DNSMOS P.835 genel kalite kestirimi (OVRL, 1–5). Bir kapı değildir: politika kuralı ancak kör dinleme denetiminden sonra konabilir (politika v4 kaydı). Okunamayan klipte boş. |
| `flags` | list[string] |  | export | Klip işaretleri; hiçbiri klibi silmez. `forced_split`: tek başına süre tavanını aşan cümle iç noktalamasından bölündü; `gap_split`: aynı cümle uzun sessizlikte bölündü; `oversize`: bölünecek iç noktalama yok, cümle tavanı aşarak bütün bırakıldı; `short`: süre `segment.min_sec` altında; `background_music`: `music_to_speech_db` eşiğin üstünde; `duplicate`: aynı kayıt/kanal içinde aynı metnin tekrarı (bkz. `duplicate_of`); `boilerplate`: kanalın kayıtlarında tekrar eden künye/anons kalıbı; `unreadable_audio`: klip dosyası okunamadı, ölçümleri yok. |
| `duplicate_of` (isteğe bağlı) | string |  | export | Klip bir yinelemeyse korunan kopyanın kimliği; değilse boş. Yineleme, metnin aynı VE sesin aynı olmasıdır: ses kimliği `dedupe.identity_fields` (süre, LUFS, RMS, tepe) birebir tutuyorsa klip aynı kaydın kopyasıdır. Aynı metnin ayrı bir okuması yineleme DEĞİLDİR, prozodi çeşitliliği olarak tutulur; kanal anahtara girmez. |
| `speaker_id` (isteğe bağlı) | string |  | export | Kaydın konuşmacı kümesi (`spkNNNN`). Kümeleme korpusun tamamı üzerinde yapılır: birleştirme eşiği ölçülen iki dağılımın eşit hata noktasından alınır (kayıt içi klip benzerliği ve farklı kanalların kayıt benzerliği), küme sayısı verilmez. Kimlik kayıt düzeyindedir; kaydın bütün klipleri aynı değeri taşır. Kapı değildir, politikada kuralı yoktur. |
| `speaker_consistency` (isteğe bağlı) | float |  | speaker | Kaydın gömülen kliplerinin birbirine kosinüs benzerliğinin ortalaması (0–1). Düşük değer kayıtta birden çok ses olduğunu gösterir (röportaj, çok sesli okuma) ve o kaydın tek konuşmacı gibi ele alınamayacağını söyler. |
| `speaker_margin` (isteğe bağlı) | float |  | export | Kaydın kendi küme merkezine benzerliği eksi en yakın diğer kümeye benzerliği. Küçük değer kümeler arası sınıra yakın bir kaydı işaret eder; negatif değer yanlış kümede olabileceğini söyler. |
| `recommended` | bool |  | export | Sürümlü politikanın (`recommended_subset`) bu klibi varsayılan eğitim alt kümesine önerip önermediği. Veri elemez; kullanıcı ölçüm sütunlarından kendi kuralını koyabilir. |
| `exclusion_reasons` | list[string] |  | export | `recommended=false` ise sağlanmayan kuralların listesi: `metrik<eşik`, `metrik>eşik`, `isaret:ad[,ad]`, `eksik_olcum:metrik`. Önerilen kliplerde boş. |
| `policy_version` | string |  | export | `recommended` ve `exclusion_reasons`'ı üreten politika sürümü; kurallar konfigde sürümlüdür ve değişince yalnızca bu üç sütun yeniden hesaplanır. |

## Bilinen sınırlar

- **Metin ASR çıktısıdır**, insan eliyle düzeltilmemiştir; `text_raw`,
  `text` ve `text_spoken` alanları aynı ASR metninden türetilir.
- **Rakamlar zorlamalı hizalanmaz**: hizalayıcının sözlüğünde rakam yok, o
  kelimelerin damgası ASR'ye düşer.
- **Cümle başı kısa sözcüklerde çöp hizalama** görülür (ölçülen pay %2,12);
  `align_score_min` bunu görünür kılar.
- **Kanal ve konuşmacı yığılması**: önerilen alt kümede ilk iki kanalın
  payı %38,2; 90 konuşmacının ilk beşi saatlerin %54,4'ünü taşıyor.
- **Kanal konuşmacı değildir**: 27 kanalın 13'ünde birden çok okuyucu var.
  Konuşmacı kimliği kümelemeden gelir ve kayıt düzeyindedir.
- **Tek kodlama profili**: kaynaklar ~129 kb/s AAC; kaynak bant kesimi
  medyan 15,7 kHz, iki kanalda 13 kHz civarı.
- **Test kümesi elle doğrulanmamıştır**; sızıntı denetimi otomatiktir.

## Kanal künyesi

Aşağıdaki kanalların kamuya açık kayıtlarından üretilmiştir. Korpusu
kullanan çalışmaların bu künyeyi taşıması beklenir.

| kanal | kayıt | klip | saat | önerilen saat | konuşmacı |
|---|---|---|---|---|---|
| seslikitaplarmavi | 279 | 332.847 | 580.7 | 539.5 | 2 |
| BirDinle | 235 | 285.797 | 487.9 | 444.8 | 6 |
| dinleyiniz | 83 | 138.254 | 239.4 | 223.2 | 32 |
| sess-Seslikitap | 176 | 149.786 | 226.2 | 199.2 | 4 |
| Peri_Mia | 216 | 132.779 | 206.9 | 80.1 | 1 |
| Pandoramedyaseslikitap | 67 | 112.170 | 193.6 | 91.0 | 1 |
| ZubeyirSener | 99 | 110.294 | 185.6 | 148.5 | 1 |
| ses-arşiv | 234 | 92.190 | 154.6 | 142.6 | 7 |
| cantadakitap | 291 | 74.328 | 126.4 | 111.9 | 1 |
| anahtarca | 175 | 61.242 | 111.7 | 92.5 | 3 |
| kitaplar | 146 | 63.096 | 103.0 | 73.4 | 2 |
| seslikutuphanemkanali | 50 | 45.723 | 77.9 | 74.4 | 1 |
| kitapdinle | 33 | 41.540 | 72.0 | 68.6 | 1 |
| idea_stüdyo | 43 | 33.102 | 54.9 | 52.6 | 1 |
| MuratKaraOfficial2021 | 71 | 24.059 | 39.3 | 34.9 | 1 |
| seslimakalem | 182 | 19.144 | 37.5 | 30.9 | 1 |
| SesliKitaPodcast | 41 | 18.232 | 31.1 | 22.7 | 1 |
| seslikitapturkish | 27 | 17.238 | 28.9 | 25.8 | 7 |
| sesli-kitaplar | 44 | 13.255 | 24.5 | 15.3 | 3 |
| eba | 39 | 15.104 | 24.4 | 23.4 | 9 |
| Seslendiriyor | 28 | 14.262 | 24.1 | 20.2 | 7 |
| OkumaSaati | 58 | 14.889 | 22.0 | 21.5 | 1 |
| SESLİKİTAPEVİ | 29 | 13.041 | 21.2 | 8.5 | 1 |
| denizinötesindekisesler | 16 | 7.786 | 14.8 | 13.4 | 1 |
| seskitap | 12 | 5.558 | 9.1 | 8.7 | 2 |
| bizimkütüphane | 3 | 4.024 | 6.9 | 6.7 | 1 |
| KitaplarinKedisi | 3 | 664 | 1.0 | 1.0 | 2 |
| **toplam** | **2.680** | **1.840.404** | **3.105,7** | **2.575,2** | **90** |
## Lisans ve kullanım

Korpus **CC BY 4.0** ile yayımlanır. Tek şart atıftır; atıf hem bu veri
kümesini hem de yukarıdaki **kanal künyesini** içermelidir.

**Ticari kullanım serbesttir.** Bu korpusla model eğitebilir, eğittiğiniz
modeli ticari ürünlerde kullanabilir, satabilir ve dilediğiniz lisansla
dağıtabilirsiniz — modelin lisansı size aittir, bu korpusun lisansı ona
bulaşmaz. Türev veri kümeleri de serbesttir; onlar için de tek beklenti
kaynağın ve kanal künyesinin belirtilmesidir. Ne gayri ticari kısıtı ne de
aynı lisansla paylaşma (share-alike) koşulu vardır.

Kayıtlar Türkçe sesli kitap YouTube kanallarının kamuya açık
yayınlarındandır. **Hak sahibi itiraz ederse ilgili kanalın kayıtları veri
kümesinden kaldırılır**; bunun için depo üzerinden ya da veri kümesi
tartışma sayfasından bize ulaşmanız yeterlidir.

## Atıf

```bibtex
@misc{kiraat2026,
  title  = {KIRAAT: A Sentence-Aligned Turkish Read-Speech Corpus},
  author = {Serdar I. {\c{C}}a{\u{g}}lar},
  orcid  = {0000-0002-5776-2431},
  year   = {2026},
  url    = {https://github.com/serdarildercaglar/kiraat}
}
```
