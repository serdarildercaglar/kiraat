# Özellikler: ne ölçülüyor, nasıl hesaplanıyor, nasıl elde ediliyor

Bu belge makalenin yöntem bölümünün hammaddesidir. Her yayımlanan sütun ve
onu üreten işlem, koddaki gerçek parametrelerle (`configs/default.yaml`)
anlatılır. Sütunların kısa tanımları `kiraat/schema.py`'de tutulur ve
`python -m kiraat schema` ile tablo olarak basılır; burası o tablonun
açıklamalı, anlatısal karşılığıdır. Buradaki her sayı ya konfigden ya da
`docs/NOTEBOOK.md`'ye tarihli olarak düşülmüş bir ölçümden gelir.

Hattın iki tasarım ilkesi bütün özelliklerin biçimini belirler. Birincisi,
kesim cümle sınırındadır: klipler ses enerjisinin düştüğü yerde değil, ASR
ve zorlamalı hizalamadan gelen kelime zaman damgaları üzerinde, cümle
sınırlarında kesilir. İkincisi, hiçbir ölçüm klip elemez: aşamalar yalnızca
ölçüm üretir, her klip bütün ölçümleriyle yayımlanır ve varsayılan eğitim alt
kümesi, sürümlü ve konfigde yazılı bir kural listesinin ürettiği
`recommended` bayrağı ile gerekçesinden ibarettir. Kullanıcı aynı sütunlardan
kendi kuralını koyabilir.

İşlem sırası: kaynak hazırlama → konuşma bölgesi bulma (VAD) → ASR →
zorlamalı hizalama → kanal düzeyinde kalıp metin madenciliği → cümle hizalı
bölütleme ve sınır iyileştirme → klip ölçümleri → arka plan müziği ölçümü →
yineleme işaretleme → politika ve dışa aktarma.

## 1. Kaynak hazırlama (`prepare`)

Her kaynak kayıt (`.m4a`, `.mp3`, `.wav`, `.flac`, `.opus`, `.webm`) ffmpeg
ile tek kanala indirilir, 24 kHz'e yeniden örneklenir ve 16 bit kayıpsız
FLAC olarak çözülür (`-sample_fmt s16`; örnekler PCM 16 bit WAV yolundakiyle
bit bazında aynıdır, dosya onun yarısı kadardır — 2.100 saatlik tam koşuda
ara sesin 366 GB yerine ~160 GB tutmasının şartı).
Kaynağın kendi hızı 24 kHz'in altındaysa yükseltme yapılmaz;
bu durumda çıktı kaynağın gerçek hızındadır ve o hız `source_sample_rate`
sütununda yayımlanır ki kullanıcı üst-örneklenmiş kaynakları ayırt edebilsin.
Filtre zinciri iki adımdır: 40 Hz yüksek geçiren süzgeç (uğultu ve DC
bileşeni için) ve −1 dBFS tepe sınırlayıcı (`alimiter`, otomatik seviye
`level=false`; varsayılan açık olsaydı sınırlayıcı çıkışı tam ölçeğe
yükseltir ve tavanı boşa çıkarırdı). Sınırlayıcı kaynak hızında
uygulanıp ses sonra 24 kHz'e indirildiği için örnekler-arası taşma
olabilir; 19 kayıtlık örnekte tepe medyanı tavanı 0,06 dB, p90'ı 0,15 dB
aşıyor, kırpılma tek örnek düzeyinde — `peak_dbfs`/`clip_ratio` sütunları
bunu olduğu gibi raporlar. Klip başına ses
seviyesi normalizasyonu **yapılmaz**; kaydın doğal seviyesi korunur ve
seviye, `rms_dbfs`/`peak_dbfs` sütunlarıyla kullanıcıya bırakılır.

Kaydın süresi kapsayıcının bildirdiği değerden değil, çözülen sesten
ölçülür. İkisi arasındaki uyumsuzluk kesik indirmeyi ele verir: çözülen süre
kapsayıcı süresinin %95'inden kısaysa kayıt `truncated_source` işaretini alır
(`source_flags`). Beş kayıtlık örnekte bir kaynakta kapsayıcı 210 dakika
derken çözülen ses 19,4 dakikaydı.

## 2. Konuşma bölgesi bulma (VAD)

VAD kesim aracı değildir; yalnızca ASR'ye hangi bölgelerin verileceğini
belirler ve klip düzeyinde ölçüm üretir. Model Silero VAD'dır, 16 kHz'de
koşar. Parametreler: olasılık eşiği 0,50, en kısa konuşma 250 ms, en kısa
sessizlik 300 ms, bölge kenar payı 100 ms. Aynı parametre kümesi hem ASR
öncesi süzgeçte hem de klip ölçümlerinde (§7) kullanılır.

## 3. Otomatik konuşma tanıma (`asr`)

Model Whisper large-v3'tür; faster-whisper (CTranslate2, float16) ile tek
GPU'da, kelime zaman damgası açık olarak koşar. Dil Türkçe olarak sabitlenir;
ışın genişliği 5, sıcaklık 0. İki ayar halüsinasyona karşı bilinçlidir:
`condition_on_previous_text` kapalıdır, böylece bir pencerede başlayan
halüsinasyon sonraki pencerelere zincirlenemez; ve çözme, VAD bölgelerinin
30 saniyelik pencerelere toplandığı toplu modda yapılır (`batch_size` 16),
pencereler bağımsız olduğundan önceki metne koşullanma zaten yoktur.

Çıktı, kayıt başına bir kelime dosyasıdır: her kelime için metin, başlangıç,
bitiş ve Whisper'ın kelime olasılığı (`prob`). Bu olasılık, kelimeyi
oluşturan alt-belirteçlerin olasılıklarının ortalamasıdır ve ses kalitesini
değil, çözücünün o kelimeye ne kadar şaşırdığını ölçer: nadir özel isimler,
ünlemler ve ağız sözcükleri temiz seste bile düşük değer alır (bkz. §11).
Kayıt düzeyinde ayrıca Whisper'ın dil olasılığı (`language_prob`) ve
kelime sayısı saklanır.

Whisper'ın kelime damgaları çapraz-dikkat tahminidir ve iki bilinen kusuru
vardır: kelime bitişleri sistematik olarak erkendir ve iki kelime arasında
boşluk bırakmadan birini diğerine yapıştırabilir (beş kayıtlık örnekte
kliplerin %10'unda sınırdaki iki kelime arasında boşluk 0,0 s). Bu kusurlar bölütlemeyi
doğrudan etkilediği için iki ayrı düzeltme vardır: zorlamalı hizalama (§4)
ve sınır iyileştirme (§5.5).

## 4. Zorlamalı hizalama (`align`)

Her ASR kelimesi, Whisper'dan bağımsız bir modelle sese yeniden oturtulur.
Model torchaudio'nun `MMS_FA` paketidir (Meta MMS zorlamalı hizalayıcısı,
1.100'den fazla dil, romanize karakter sözlüğü, `<star>` belirteçli). Kelime
metinleri `uroman` ile romanize edilir; her kelime, bir `<star>` belirteci
ve romanize karakterlerinin sözlük kimliklerinden oluşan bir hedef dizisine
çevrilir. Uzun bir kayıt tek parçada hizalanamaz (kafes T×N büyür), bu
yüzden Whisper'ın kaba damgaları kılavuz alınarak kayıt yaklaşık 30
saniyelik parçalara bölünür (`chunk_sec` 30, en fazla 60; parça sınırı
yalnızca 0,3 s'den geniş kelime boşluklarına konur; her parçanın iki yanına
0,5 s ses payı eklenir). Her parça için modelin kare başına log-olasılık
matrisi alınır, `torchaudio.functional.forced_align` ile CTC zorlamalı
hizalama yapılır ve `merge_tokens` ile belirteç aralıkları birleştirilir.

Kelime başına üç alan üretilir. `align_start`/`align_end`, kelimenin
romanize karakterlerinin ilk ve son karesinin zamanıdır (parça ekseninden
kayıt eksenine taşınmış). `align_score`, kelimenin karakter belirteçlerinin
kare olasılıklarının ortalamasıdır (0–1). Model çıktısı zaten
log-olasılıktır ve `with_star=True` sonuna normalize edilmemiş bir `<star>`
sütunu ekler; emisyon **yeniden normalize edilmez** — bir `log_softmax`
daha uygulamak star'a olasılığın yarısını verir ve bütün skorları 0,5
tavanına sıkıştırır (29 Ağu 2026'da düzeltildi, defterdeki kayda bakınız).
Hizalanamayan parça ya da kelime
(çok kısa ses, sözlükte karşılığı olmayan belirteç, kafesin sığmaması)
boş kalır. Beş kayıtlık örnekte 31.982 kelimenin %99,6'sı hizalandı.

Klip düzeyinde bu alanlar `align_score_min` ve `align_score_mean` olarak
özetlenir. Bölütleme, klip sınırlarını Whisper damgaları yerine hizalayıcı
damgalarından alır (`align.enabled: true`). Aynı örnekte hizalayıcı damgası
Whisper'a göre kelime başında ortalama +0,19 s (p10 +0,11, p90 +0,41), kelime
sonunda +0,10 s (p10 +0,03, p90 +0,20) ileridedir — Whisper'ın "erken damga"
kusurunun sayısı budur. Hizalayıcı skorunun Whisper kelime olasılığıyla sıra
korelasyonu yalnızca +0,34'tür; iki sinyal farklı şeyler ölçer (biri
ses–metin uyuşması, diğeri çözücü sürprizi). `confidence_source` sütunu,
klibin `word_confidence` alanlarının hangisinden geldiğini söyler; hizalayıcı
skoru kalibre edilene kadar varsayılan `asr`'dir ve hizalayıcı skoru her
hâlükârda kendi sütunlarında yayımlanır.

## 5. Cümle hizalı bölütleme (`segment`)

### 5.1 Kelime dizisinin hazırlanması

Whisper'ın ayrı belirteç olarak verdiği ekler — kesme işaretinden sonra
küçük harfle devam eden parçalar ("Button" + "'ın"), tire sonrası parçalar
ve tek başına kalmış noktalama — bir önceki kelimeye yapıştırılır
(`attach_clitics`). Birleşen kelimenin zaman aralığı ikisinin birleşimi,
olasılığı ikisinin asgarisidir. `n_words` bu birleştirilmiş dizide sayılır.

### 5.2 Cümle sınırı

Sınır kararı transcript üzerinde verilir. Bir belirteç `.`, `!`, `?` (ve
bunları izleyen kapanış tırnağı/parantez) ile bitiyorsa ve bir sonraki
belirteç yeni cümle gibi başlıyorsa (ilk harfi büyük ya da rakam) cümle
biter. Nokta belirsiz olan tek işarettir; şu durumlarda cümle bitirmez:
gövde bilinen bir kısaltmaysa (dr, prof, vb, vs, bkz, hz, sok, no…
listesi `kiraat/text/sentences.py`), tek harfli baş harfse ("A. Hamdi"),
içinde nokta olan bir kısaltmaysa ("M.Ö."), ya da sıra sayısıysa ve
ardından "bölüm, kitap, cilt, kısım, perde, sayı, baskı, dünya" gibi bir
sözcük geliyorsa ("3. bölüm"). Büyük/küçük harf kararları Türkçe eşlemeyle
(I/ı, İ/i) verilir. Bu tasarımın doğrudan sonucu, bir klibin cümle
ortasından başlamasının yapısal olarak imkânsız olmasıdır;
`tests/test_segment.py` üretilen hiçbir klibin küçük harfle başlamadığını
sınar.

### 5.3 Süre bütçesi, birleştirme ve bölme

Süre parametreleri `segment.min_sec` 1,5 s, `target_sec` 7 s, `max_sec`
15 s, `max_join_gap_sec` 1,2 s'dir. Ardışık cümleler, birleşik süre 15 s'yi
aşmadığı ve aralarındaki sessizlik 1,2 s'yi geçmediği sürece hedef süreye
doğru aynı klipte birleştirilir; 1,2 s'den uzun bir ara bölüm geçişi
sayılır ve cümleler yapıştırılmaz. Tek başına 15 s'yi aşan bir cümle önce
içindeki en büyük sessizlik boşluğundan (1,2 s üstü varsa) bölünür: parçalar
metin olarak bütün görünüyorsa (büyük harfle başlayıp cümle sonuyla bitiyor)
işaret almaz, aksi hâlde `gap_split` alır. Boşluk yoksa cümle iç
noktalamasından — önce noktalı virgül, sonra iki nokta, uzun/kısa tire,
en son virgül aranır — hedef süreye en yakın noktadan bölünür ve parçalar `forced_split` işareti taşır.
Hiç iç noktalama yoksa cümle bölünmez; bütün olarak, `oversize` işaretiyle
yayımlanır — kararsız kalınan veri silinmez, işaretlenir. 1,5 s'den kısa
klipler `short` işareti alır. Kanal düzeyinde madenlenmiş kalıp ifadeler
(§9) kendi başına klip olur, `boilerplate` işareti taşır ve komşularıyla
birleşmez; böylece künye ilk cümleye yapışmaz.

### 5.4 Nefes payı

Her klibin iki ucuna pay bırakılır: başa 0,15 s, sona 0,25 s. Pay, komşu
klibe olan boşluğun ortasını geçemez; aksi hâlde ASR kelime bitişleri erken
olduğu için önceki kelimenin kuyruğu klibe sızıyordu (dinleme denetiminde
duyuldu).

### 5.5 Sınır iyileştirme (`boundaries`)

Damga çevresinde payın çözemediği durum, Whisper'ın iki kelimeyi boşluksuz
yapıştırmasıdır: verilecek boşluk yoktur ama gerçek sessizlik (nefes)
damganın hemen yakınında durur. Bölütlemeden sonra, komşu iki klip
arasındaki her sınırda ses enerjisine bakılır. 24 kHz sesten 20 ms
pencere / 10 ms adımla dB zarfı çıkarılır; sınır damgasının 0,05 s öncesi
ile 0,60 s sonrası taranır (öncesi kasıtlı kısa: bitişler erken olduğu için
sessizlik hep sonradadır). Yerel konuşma seviyesinin 25 dB altına düşen ve
en az 60 ms süren bir sessizlik bulunursa sınır oraya konur; bulunamazsa
penceredeki en düşük enerjili ana konur. Metne, klip sırasına ve kelime
aralıklarına dokunulmaz; yalnızca `start`/`end` değişir. Sınırı taşınan
klipler iç kayıtta `snapped_start`/`snapped_end` bilgisini taşır (şu an
yayımlanmıyor, bkz. §12).

`start`, `end` ve `duration` sütunları bu adımların hepsinden sonraki
değerlerdir. `lead_gap_sec`/`trail_gap_sec`, klibin ilk/son kelimesiyle
kayıttaki komşu kelime arasındaki boşluktur; kaydın ilk/son kelimesinde
boştur. Küçük değer, komşu cümlenin klibe bulaşma riskinin göstergesidir.

## 6. Metin alanları

Üç alan yayımlanır ve üçü de farklıdır. `text_raw`, klibin kelime
aralığındaki ASR belirteçlerinin boşlukla birleştirilmiş, dokunulmamış
hâlidir. `text`, hafif temizliktir: birden fazla boşluk teke indirilir,
bölünmez boşluk düzeltilir, tekrar eden noktalama ("!!", "...") teke iner;
sayılar, kesme işaretleri ve özgün noktalama korunur. `text_spoken`,
okunuşa çevrilmiş metindir ve eğitimde kullanılması amaçlanan alandır:
kısaltmalar açılır ("vb." → "ve benzeri", "dr." → "doktor"; 14 girişlik
liste), yüzde ("%50" → "yüzde elli"), para birimi simgeleri ("50₺" →
"elli lira"), saat ("14:30" → "on dört otuz"), ondalık ("1,5" → "bir virgül
beş"), küçük harfli sözcük izleyen sıra sayısı ("3. bölüm" → "üçüncü
bölüm") ve kalan tam sayılar (trilyona kadar, Türkçe sayı adlarıyla)
çevrilir. Bütün harf işlemleri Türkçe küçük/büyük harf eşlemesiyle yapılır.

## 7. Klip ölçümleri (`clip_qc`)

Her klip FLAC dosyasından okunur (okunamazsa `unreadable_audio` işareti,
ölçüm yok). Seviye ölçümleri doğrudan örneklerden hesaplanır:
`peak_dbfs` = 20·log10(max|x|), `rms_dbfs` = 20·log10(RMS), `clip_ratio` =
|x| ≥ 0,99 olan örneklerin oranı (dijital kırpılma). Konuşma ölçümleri için
klip 16 kHz'e indirilir ve §2'deki parametrelerle Silero VAD koşulur;
bölge sınırları örnek indeksinden alınıp saniyeye çevrilir (ms çözünürlük):
`speech_ratio` konuşma sayılan toplam sürenin klip süresine oranı,
`internal_silence_sec` ardışık konuşma bölgeleri arasındaki en büyük boşluk,
`leading_silence_sec` ilk konuşma bölgesine kadar geçen süre,
`trailing_silence_sec` son bölgeden klip sonuna kalan süre. Klipte hiç
konuşma bulunmazsa baş/son sessizlik klip süresine eşitlenir. clip_qc CPU
işçi havuzunda koşar.

## 8. Arka plan müziği (`music`)

Sorulan soru "bu klip konuşma mı müzik mi" değil, "konuşmanın **altında**
müzik var mı" sorusudur; ikili bir konuşma/müzik sınıflandırıcısı bunu
yanıtlayamaz, çünkü altında müzik olan anlatım onun için hâlâ konuşmadır
(iki hazır ikili sınıflandırıcı 19 kayıtlık örnekte sınandı: biri müziksiz
kliplerin üçte ikisine "müzik" dedi, diğeri AudioSet skoruyla aynı bilgiyi
verdi; ikisi de kullanılmıyor). Ölçüm bu yüzden iki katmanlıdır ve ikisi de
yayımlanır; işaret ikisinin birlikte sağlanmasını ister.

`music_score_audioset`: AudioSet üzerinde ince ayarlanmış Audio Spectrogram
Transformer (`MIT/ast-finetuned-audioset-10-10-0.4593`) 16 kHz'de,
10,24 s pencere / 5 s adımla koşar; çok etiketli sigmoid çıktısından sekiz
müzik etiketinin ("Music", "Background music", "Soundtrack music", "Theme
music", "Musical instrument", "Singing", "Song", "Jingle (music)") azamisi
alınır ve pencereler üzerinden en büyük değer klibin skorudur. Ucuzdur, her
klipte hesaplanır; konuşmayla birlikte var olabilir.

`music_to_speech_db`: fiziksel ölçü. Klip 44,1 kHz'e çevrilir, torchaudio'nun
`HDEMUCS_HIGH_MUSDB_PLUS` kaynak ayrıştırıcısıyla (mono sinyal iki kanala
kopyalanarak) dört bileşene ayrılır: vokal, davul, bas, diğer. Konuşma =
vokal bileşeni, eşlik = diğer üçünün toplamı; sütun
20·log10(RMS_eşlik / RMS_vokal)'dir, −80 dB tabanıyla. Negatif değer müziğin
konuşmanın altında olduğunu söyler; konuşma tamamen sessizse 0 dB döner.
Ayrıştırma pahalıdır: yalnızca AudioSet skoru 0,05 eşiğini geçen kliplerde
koşar, koşmadıysa sütuna taban değer −80 yazılır ve `music_db_separated`
false olur. Dört bileşenin ayrı seviyeleri `music_stem_db` olarak yalnızca
ayrıştırıcının koştuğu kliplerde yazılır.

`background_music` işareti iki yayımlanan sütundan türetilir:
`music_to_speech_db` > `music.inaudible_db` (−40 dB; kör dinlemeyle, 28 Ağu
2026, 34 klip, beş bant: −40 dB altındaki 10 klipte 9 "yok" 1 "hafif";
−40…−33 bandında 6/6 "belirgin") **ve** `music_score_audioset` ≥
`music.audioset_min` (0,3). İkinci koşul 29 Ağu 2026'da eklendi: tek başına
dB oranı, ayrıştırıcının konuşma kaydındaki oda tınısını "eşlik" saydığı
bir kanalda 41 müziksiz klibi işaretlemişti (dinlemeyle doğrulandı; o
kliplerde AudioSet medyanı 0,10, gerçek müzikte 0,53). İşaret yayımlanan
sütunlardan türetildiği için kullanıcı veriyi yeniden üretmeden kendi
eşiklerini kesebilir. Politika (v3) dB sütununa değil bu işarete bakar.

## 9. Kanal düzeyinde kalıp metin madenciliği (`boilerplate`)

Künye ve anonslar ("seslendiren …", kanal jingle metni) bir kaydın içeriği
değil, kanalın kalıbıdır: aynı kanalın kayıtlarında, çoğunlukla başta ve
sonda, kelimesi kelimesine tekrar eder. Bu yüzden tek kayıttan değil,
kanalın bütün kayıtlarından öğrenilir. Her kaydın ilk 80 ve son 80 kelimesi
küçük harfe indirilip noktalamadan arındırılır; 3–24 kelimelik bütün
n-gram'lar çıkarılır ve kaç ayrı kayıtta geçtikleri sayılır. Eşik, kanal
kayıt sayısının %40'ı ve en az 2 kayıttır (üç kayıtlı kanalda 2, elli
kayıtlı kanalda 20). Aynı sayıda kayıtta geçen daha uzun bir ifadenin
içinde kalan kısa ifadeler atılır; uçları örtüşen aynı sayımlı ifadeler tek
ifadede birleştirilir (13 kelimelik bir jingle iki örtüşen n-gram olarak
gelir). Bulunan ifadelerin bir kayıttaki geçtiği kelime aralıkları
bölütleyiciye verilir; o aralıklar ayrı klip olur ve `boilerplate` işareti
taşır — silinmez. Yöntemin bilinen sınırı: değişken yuvalı şablonlar ("<yazar>'ın <kitap>
adlı kitabından", "<yazar>, <gazete>") kelimesi kelimesine tekrar
etmediğinden yakalanmaz; beş kanal × üç kayıtlık örnekte hiçbir ifade
bulunmadı ve künyelerin hepsi bu türdendi. Şablon madenciliği açık
maddedir.

## 10. Yineleme işaretleme (`dedupe`)

Kural: aynı metin **aynı sesle** tekrar ediyorsa yinelemedir, aynı metin
**farklı sesle** okunuyorsa prozodi çeşitliliği açısından değerlidir ve
tutulur. Karşılaştırma anahtarı, `text` alanının Türkçe küçük harfe
indirilmiş, noktalamasız, tek boşluklu hâlidir; ses anahtarı konuşmacı
kimliğidir (konuşmacı aşaması bağlanana kadar kanal). Aynı (metin, ses)
grubunda en uzun süreli klip korunur (`duplicate_of` boş), diğerleri
`duplicate` işareti ve korunan klibin kimliğini alır. Politika bunları
önerilen alt kümeden düşürür; veri kümesinde kalırlar.

## 11. Politika ve karar sütunları (`recommended_subset`)

`recommended`, `exclusion_reasons` ve `policy_version` üçlüsü, konfigdeki
sürümlü kural listesinin ürünüdür. Sürüm 4'ün kuralları: `speech_ratio`
≥ 0,60; `clip_ratio` ≤ 0,002; `internal_silence_sec` ≤ 1,0 s;
`word_confidence` ≥ 0,60; ve `oversize`, `forced_split`, `gap_split`,
`short`, `duplicate`, `boilerplate`, `background_music` işaretlerinden
hiçbirinin bulunmaması. Müzik kuralı v3'te `music_to_speech_db` sütunundan
`background_music` işaretine taşındı (dB VE AudioSet ≥ 0,3), çünkü dB tek
başına bir kanalda müziksiz klipleri eliyordu. `dnsmos_ovrl` ≥ 3,0 kuralı
v4'te kaldırıldı: DNSMOS aşaması bağlı değil, sütun hiç üretilmiyor ve
kural `allow_missing` ile her klipte sessizce geçiyordu — politika
uygulanmayan bir eşiği uygulanıyormuş gibi gösteriyordu. Sağlanmayan her kural gerekçe olarak
yazılır: `metrik<eşik`, `metrik>eşik`, `isaret:ad[,ad]`, ölçüm eksikse ve
kural eksikliğe izin vermiyorsa `eksik_olcum:metrik`. Politika değişince
veri yeniden üretilmez, yalnızca bu üç sütun yeniden hesaplanır.

Kuralların her biri bir ölçüme dayanır ve bir sinyal ancak dinleme
denetiminden geçtikten sonra kural olabilir. Müzik eşiği bu yoldan geçti
(§8). `word_confidence ≥ 0,60` kuralı ise şu an inceleme altındadır: beş
kayıtlık örnekte kliplerin %6,8'ini yalnızca bu kural dışlıyor; dışlanan
kliplerde ortalama kelime olasılığı 0,94, hizalayıcı asgari skoru
tutulanlarla aynı (0,37'ye 0,41), düşük değeri üreten kelime çoğunlukla bir
karakter adı, ünlem ya da işlev kelimesi. Kararın dinleme denetimine
bağlandığı deney `docs/NOTEBOOK.md`'de kayıtlıdır.

## 12. Üretilen ama henüz yayımlanmayan özellikler

Hattın ürettiği ve yayım kararı bekleyen dört şey vardır. Birincisi ve en
önemlisi, **kelime düzeyinde** zaman damgası ve güven: ASR kelime dosyası
(metin, başlangıç, bitiş, olasılık) ile hizalayıcının kelime başına
`align_start`, `align_end`, `align_score` alanları. Her klibin kelime
aralığı (`word_span`) iç kayıtta durduğundan, bunlar klip başına bir `words`
sütunu olarak kesilip yayımlanabilir. İkincisi, kaynak düzeyi ölçümler:
`language_prob`, `container_duration`, kelime sayısı, hizalanan kelime
sayısı ve oranı, hizalayıcı skor medyanı, kullanılan ASR modeli. Üçüncüsü,
sınır iyileştirmenin klibi taşıyıp taşımadığı (`snapped_start`/`snapped_end`).
Dördüncüsü, kanal başına madenlenen kalıp ifadeler; bunlar veri kümesine
değil makaleye malzemedir. VAD bölgeleri saklanmaz.

## 13. Tasarımda kararlaştırılmış, henüz üretilmeyen sütunlar

Konuşmacı kümesi ve küme kenar payı (`speaker.model:
pyannote/wespeaker-voxceleb-resnet34-LM`, kosinüs eşiği 0,75), kaynak
düzeyinde LUFS ve uygulanan kazanç, DNSMOS (`dnsmos_ovrl`; politikada
"eksikse geç" olarak duruyor) ve isteğe bağlı dış müzik sınıflandırıcısı
olasılığı (`music_prob_external`). Bunlar üretildikçe `kiraat/schema.py`'ye
ve bu belgeye eklenir; makaleye yalnızca bu depoda üretilmiş hâlleri girer.
