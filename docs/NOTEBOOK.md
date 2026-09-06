# Araştırma defteri

Makale bu dosyadan yazılacak. Defter konu konu düzenlidir: her başlık, o
konunun **bugün geçerli olan** sonucunu ve o sonucun nereden geldiğini
söyler. Ara adımlar, düzeltme günlükleri ve eskimiş örnek koşular burada
tutulmaz; onların izi git geçmişindedir.

## Bu defterin kuralı

**Hiçbir kayıt önceki bir yayına ya da önceki bir veri kümesine atıf
yapmaz.** Makale sıfırdan yazılıyor; ne bir önceki sürümü genişletiyor, ne
ondan alıntılıyor, ne de onu taban olarak anıyor. Buradaki her sayı bu
depodaki kodla, bu depodaki konfigle ve ham kayıtlardan üretilmiştir.
Mühendislik gerekçelerinin tutulduğu `DESIGN.md` iç belgedir ve makale
malzemesi değildir.

Bütün sayılar tek bir koşudan gelir: **`work/full-1`**, manifest
`work/full-1/manifests/clips.jsonl`, koşu kaydı `run.json` (commit, aşama
sürümleri, ağırlık revizyonları, konfig). Örnek koşular (`sample-*`)
silinmiştir ve makalede anılmaz; yalnızca kör dinleme turları o
örneklemler üzerinde yapıldığı için burada tarihleriyle anılır — dinleme
sonuçları koşudan bağımsızdır.

---

## Korpus: ham kayıtların ölçülmüş sınırları

30 Ağustos 2026, `scripts/inventory.py`; ham kökteki **her** dosya
ffprobe'dan geçirildi ve künyesi `work/inventory.jsonl`'e yazıldı.

**2.700 dosya, 2.698 okunabilir ses, 3.440,2 saat, 200,1 GB, 27 kanal.**
Bir dosya ffprobe ile açılamıyor (bozuk m4a), biri README.

Kayıt uzunluğu: medyan 41,4 dk, p75 90,9, p90 185,0, p95 257,5, p99 517,7,
azami **14,92 saat**.

| kayıt uzunluğu | kayıt | saat | korpus payı |
|---|---|---|---|
| < 10 dk | 168 | 20,4 | %0,6 |
| 10–30 dk | 911 | 274,0 | %8,0 |
| 30–60 dk | 635 | 462,8 | %13,5 |
| 1–2 saat | 467 | 654,7 | %19,0 |
| 2–4 saat | 351 | 973,4 | %28,3 |
| 4–8 saat | 131 | 700,5 | %20,4 |
| 8 saat+ | 35 | 354,4 | %10,3 |

Korpusun **%30,7'si dört saatten uzun tek parça kayıtlarda.** Bu, hattın
mimarisini belirleyen olgudur: çok saatlik kaydı sabit bellekle işlemek
zorunluluktur, tercih değil.

Biçim tekdüze: 2.618 dosya AAC (3.379,7 saat), 80 MP3 (60,5 saat); 2.693
dosya 44,1 kHz; bit hızı p5 128 / medyan 129 / p95 130 kb/s. Kaynağın
gerçek bant genişliği kanal başına bir kayıtta ölçüldü (ortadan 60 s,
32k FFT): kesim frekansı **medyan 15,7 kHz** (en düşük 13,0, en yüksek
15,8); 12 kHz üstünde kalan enerji payı medyan %0,05. Hedef 24 kHz
(Nyquist 12 kHz) kaynağın tavanının altında kalıyor — yükseltmenin
karşılığı, düşürmenin gerekçesi yok.

Kanal payları dengesiz: `seslikitaplarmavi` %19,5 (671,0 saat), `BirDinle`
%15,5 (534,4), `sess-Seslikitap` %7,4, `dinleyiniz` %7,4, `Peri_Mia` %7,0;
ilk iki kanalın payı **%35,2**. Kanal başına saat tavanı **yoktur**:
korpusu 3.440 → 1.849 saate indirecek böyle bir tavan bilinçli olarak
uygulanmadı, çünkü kanal çeşitliliğini eşikle budamak bu hattın reddettiği
şeydir.

**Makaleye:** §Korpus (bütün sayılar), §Yöntem (24 kHz kararının kaynak
bant genişliğiyle gerekçesi), §Sınırlar (kanal payı, tek kodlama profili).

---

## Hat: aşamalar, modeller, sabitlenmiş ağırlıklar

`python -m kiraat run`; durum sqlite deposunda (`kiraat/store.py`), işler
CPU/GPU havuzlu dağıtıcıda (`kiraat/scheduler.py`) koşar. Aşama sırası:

| aşama | ne yapar | model / ayar |
|---|---|---|
| `prepare` | çözme, 24 kHz mono, 40 Hz yüksek geçiren, −1 dB tepe | ffmpeg |
| `asr` | uzun form yazıya çevirme, kelime damgası | faster-whisper `large-v3`, revizyon `edaa852e`, beam 5, sıcaklık 0, `condition_on_previous_text: false` |
| `align` | zorlamalı hizalama, kelime başına skor | torchaudio `MMS_FA` (+`<star>`) |
| `boilerplate` | kanal düzeyinde künye/anons madenciliği | kelime n-gramı, eşik kanal kayıtlarının %40'ı (en az 2), `max_words: 24` |
| `segment` | cümle sınırında kesim, ses tabanlı sınır iyileştirme | `kiraat/segment.py`, `kiraat/boundaries.py` |
| `clip_qc` | konuşma oranı, iç sessizlik, uç sessizlikler, seviye, LUFS | silero VAD; BS.1770 (pyloudnorm) |
| `music` | müzik/konuşma dB'si ve AudioSet müzik skoru | torchaudio `HDEMUCS_HIGH_MUSDB_PLUS`; `MIT/ast-finetuned-audioset-10-10-0.4593` |
| `dnsmos` | P.835 SIG/BAK/OVRL | DNS-Challenge `sig_bak_ovr.onnx`, sha256 konfigde sabit, ONNX Runtime CUDA |
| `speaker` | kayıt başına ses kimliği ve kayıt içi tutarlılık | ECAPA-TDNN `speechbrain/spkrec-ecapa-voxceleb`, revizyon `5c0be387` |
| `export` | manifest + koşu kaydı | `manifests/clips.jsonl`, `run.json` |

Değişmez iki kural koda gömülüdür: **kesim cümle sınırındadır** ve
**hiçbir eşik klip elemez** — klip aşamaları yalnızca ölçüm üretir,
`ClipStage.validate_output` bir aşamanın `recommended`/`decision` yazmasını
hata sayar. Eşiklerin hepsi `configs/default.yaml` içindedir; `Config.load`
bilinmeyen bölüm ya da anahtarı sessizce yutmaz. Sütun şeması tek
kaynaktadır (`kiraat/schema.py`) ve veri kartı oradan üretilir. Yöntem
ayrıntıları `docs/FEATURES.md`'de.

Uç sessizlik sütunları (`leading_silence_sec`, `trailing_silence_sec`)
politikayı besleyen VAD geçişinden değil, paysız ve kısa eşikli **ayrı bir
geçişten** ölçülür: politika geçişinin 100 ms'lik payı ve 300 ms'lik
sessizlik eşiği bölütlemenin 250 ms'lik kuyruk payından uzun olduğu için
son konuşma bölgesini kapatamıyor ve kuyruk sessizliğini yapısal olarak
sıfır gösteriyordu.

**Makaleye:** §Yöntem (bütün tablo), §Yeniden üretilebilirlik (revizyonlar,
koşu kaydı).

---

## Tam koşu: korpusun sayıları

`work/full-1`, 6 Eylül 2026'da tamamlandı.

| | |
|---|---|
| kaynak | 2.699 (1'i okunamadı) |
| kanal | 27 |
| klip | **1.840.404 / 3.105,70 saat** |
| önerilen alt küme (politika v6) | **1.547.494 klip / 2.575,22 saat** |

Envanterdeki 3.440 saatten manifestteki 3.105,7 saate düşüş (%90,3 verim)
sessizlik, künye kesimi ve cümle sınırı dışında kalan artıklardan gelir.
Önerilen alt küme kliplerin %84,1'i, saatlerin %82,9'u.

**Sütun dağılımları** (önerilen alt küme, 1.547.494 klip):

| sütun | p05 | p50 | p95 | ortalama |
|---|---|---|---|---|
| süre (s) | 2,76 | 5,82 | 10,56 | 5,99 |
| `loudness_lufs` | −27,99 | −20,92 | −12,54 | −20,61 |
| `dnsmos_ovrl` | 2,862 | 3,296 | 3,491 | 3,253 |
| `dnsmos_sig` | 3,271 | 3,563 | 3,710 | 3,536 |
| `dnsmos_bak` | 3,631 | 4,109 | 4,210 | 4,041 |
| `speech_ratio` | 0,851 | 0,977 | 1,000 | 0,955 |
| `music_score_audioset` | 0,001 | 0,006 | 0,228 | 0,034 |
| `music_to_speech_db` | −80,0 | −80,0 | −40,94 | −75,42 |
| `align_score_mean` | 0,858 | 0,961 | 0,994 | 0,946 |
| `align_score_min` | 0,278 | 0,800 | 0,976 | 0,740 |
| `word_confidence` | 0,550 | 0,917 | 0,999 | 0,866 |
| `n_words` | 5 | 11 | 21 | 11,7 |
| `internal_silence_sec` | 0,000 | 0,000 | 0,664 | 0,166 |

Korpusun tamamında DNSMOS: OVRL ortalama 3,208 (p05 2,69 / p50 3,27 /
p95 3,49; en düşük 0,96, en yüksek 3,74). Kliplerin **%83,57'si**
`dnsmos_ovrl ≥ 3,0` — alanın yerleşik eşiği bu korpusta neyi eleyeceğini
göstermek için kaydedilir, kural değildir.

**İşaretler** (bütün klipler): `background_music` 207.196, `forced_split`
52.501, `short` 20.904, `oversize` 6.731, `gap_split` 5.141, `boilerplate`
1.053, `duplicate` 576. Havuzu asıl daraltan tek başına müzik işaretidir.

**Önerilen alt kümede kanal payı:** `seslikitaplarmavi` 539,5 sa (%20,9),
`BirDinle` 444,8 (%17,3), `dinleyiniz` 223,2 (%8,7), `sess-Seslikitap`
199,2 (%7,7), `ZubeyirSener` 148,5 (%5,8), `ses-arşiv` 142,6 (%5,5); ilk
iki kanal **%38,2**. 27 kanalın hepsi alt kümede temsil ediliyor.

**Makaleye:** §Veri (bütün tablolar), §Sınırlar (kanal yığılması).

---

## Bölütleme ablasyonu — makalenin ana sonucu

6 Eylül 2026, `scripts/ablate_segmentation.py`. Aynı kayıtlar, aynı kelime
zaman damgaları, aynı süre ayarları; değişen tek şey kesimin nerede
yapıldığı. Cümle kolu tam koşunun ürettiği kliplerdir; taban kol
`kiraat/segment_vad.py` ile üretildi — silero VAD'ın konuşma bölgeleri
aradaki sessizliklerde kesilir, tavanı aşan tek bölge tavanda sert kesilir.
Örneklem kanal dengeli: **27 kanaldan 206 kayıt, 240,5 saat.**

| ölçüm | cümle hizalı | sessizlik hizalı |
|---|---|---|
| klip | 141.379 | 76.466 |
| saat | 240,54 | 254,18 |
| cümle ortasından başlayan | 1.967 (%1,39) | 10.943 (**%14,31**) |
| cümle ortasında biten | 2.405 (%1,70) | 12.117 (%15,85) |
| **işaretsiz** kırık başlangıç | **0 (%0,00)** | 9.798 (**%12,81**) |
| işaretsiz kırık bitiş | %0,01 | %11,59 |
| iki ucu birden kırık | 418 | 2.673 |
| süre medyanı | 5,94 s | 12,90 s |
| süre %5–%95 | 2,69 – 10,96 s | 5,10 – 15,40 s |
| süre tavanına dayanan | %0,64 | %14,70 |
| `align_score` ortalaması | 0,9442 | 0,9459 |
| klip başına en düşük `align_score`, ortalaması | **0,7319** | 0,6469 |

Asıl satır işaretsiz olanıdır. Cümle kolunda kırık başlangıçlı **hiçbir
işaretsiz klip yok**: %1,39'luk kırık başlangıcın tamamı `forced_split` ya
da künye işareti taşıyor, yani kusur görünür ve önerilen alt kümeye
girmiyor. Taban kolda kırıkların neredeyse hepsi işaretsiz (%12,81) —
sessizlikte kesen bir hattın elinde kırığı gösterecek sinyal yoktur.

Kusur kanala göre değişiyor ama hiçbir kanalda kaybolmuyor: taban kolda
kırık başlangıç oranı **%7,0 – %35,0** arasında, cümle kolunda **%0,00 –
%5,02**.

İki yan bulgu. Sessizlik hizalı kesim daha çok saat üretiyor (254,2'ye
karşı 240,5) ama neredeyse yarısı kadar klip: klipler iki kat uzun ve
%14,7'si süre tavanına dayanıyor — yani kesim noktasını cümle değil tavan
belirliyor. Ortalama hizalama güveni iki kolda aynı, ama klip başına **en
düşük** kelime güveninin ortalaması cümle kolunda belirgin yüksek (0,732'ye
karşı 0,647): sessizlikte kesilen klipler kenarlarında daha çok kötü
hizalanmış kelime taşıyor.

Ölçüm dosyası `work/full-1/ablation/segmentation.json` (kaynak başına
döküm dâhil).

**Makaleye:** §Bölütleme'nin ana tablosu.

---

## Sınır iyileştirme ve kulakla doğrulama

Cümle sınırında kesmek kesim noktasını belirler, sınırın tam yerini
belirlemez: kelime damgaları kelimenin bittiği anı erken verir.
`kiraat/boundaries.py` bu yüzden komşu klipler arasındaki damga çevresinde
küçük bir pencerede ses enerjisine bakıp kesimi gerçek sessizliğe çeker;
eşikleri konfigdedir (`boundaries` bölümü).

Doğrulaması kulaktır ve iki turda yapıldı (28–30 Ağustos, kanal ve ölçüm
gizli). İkinci turda kesik hece bulundu ve sınır iyileştirme bu bulgu
üzerine yazıldı; üçüncü turda **28/28 klip temiz** (kırık başlangıç 0,
kırık bitiş 0, kesik hece 0). Dördüncü turda (30 Ağustos, 30 klip: 20
şüpheli + 10 kontrol, karışık) **20/20 ve 10/10 klipte sıfır kesik kelime,
sıfır kırık başlangıç, sıfır kırık bitiş** — yani sınır iyileştirme
damganın ötesindeki gerçek sessizliğe yaslanıyor ve doğru yapıyor; kusurlu
olan damgaydı. Denetim ölçütü buna göre damgadan sese taşındı: FAIL ölçütü
artık "klibin kendi kelime aralığındaki bir kelime tamamen sınırların
dışında mı kalıyor", yani metin sesle uyuşuyor mu.

**Makaleye:** §Yöntem (sınır iyileştirme), §Doğrulama (dinleme protokolü).

---

## Kalite sütunları

### Müzik

Soru: konuşmanın altında müzik olup olmadığı nasıl ölçülür? Üç aday
karşılaştırıldı (28 Ağustos): AudioSet AST'nin çok etiketli müzik skoru;
kaynak ayrıştırmasından (HDemucs) gelen eşlik/konuşma enerji oranı (dB); ve
harici ikili konuşma/müzik sınıflandırıcısı. İkili sınıflandırıcı soruyu
yanıtlamıyor — hiç müziği olmayan kliplere 0,999, müziği −22 dB'de açıkça
duyulan kliplere 0,006 verdi; birbirini dışlayan iki sınıfla eğitilmiş bir
model için "altında müzik olan konuşma" kategorisi yok. **Karar:** harici
model kaldırıldı; iki sütun (`music_score_audioset`, `music_to_speech_db`)
yayımlanır, ikili yanıt bu sütunlardan eşikle türetilir.

İki sütunun ilişkisi bu depoda ölçüldü (31 Ağustos, 3.097 ayrıştırılan
klip): **Spearman +0,479.** Yani AudioSet skoru dB'nin yerini tutmuyor,
ikisi ayrı şey ölçüyor — kural bu yüzden ikisinin VE'sidir:
`music_to_speech_db > −40` **ve** `music_score_audioset ≥ 0,3`
→ `background_music` işareti.

Eşik kulakla oturdu. Birinci turda (29 Ağustos) ilk tahmin −30 dB
çürütüldü: −40…−33 bandında 6/6 klipte müzik "belirgin", −40 altında 10
klipte 9 "yok". İkinci turda (31 Ağustos) işaretin üç kanalda yığılması
sınandı — 36 klip, dört dB bandına dengelenmiş, kanal ve skor gizli:
işaretlilerin **%86'sında** kulak da müzik duydu, işaretsizlerin 11/14'ü
temiz. **Eşik −40 dB'de kaldı**; işaret kanal tınısını değil gerçek müziği
yakalıyor.

### DNSMOS P.835

Alanın yerleşik algısal kalite kestirimi; DNS-Challenge deposundaki
`sig_bak_ovr.onnx` ile, referans uygulamayla aynı pencereleme (9,01 s
pencere, 1 s adım, pencere başına ikinci derece polinomla MOS eşlemesi,
pencerelerin ortalaması). Korpus genelindeki dağılım yukarıdaki tabloda.
Sütun olarak yayımlanır; `dnsmos_ovrl ≥ 3,0` kuralı **politikada yoktur**
ve kör dinleme denetiminden geçmeden konmayacaktır.

### Ses yüksekliği

`loudness_lufs` BS.1770 tümleşik ses yüksekliğidir ve sütun olarak
yayımlanır; ses **normalize edilmez**. Korpusta klip medyanı −20,92 LUFS,
%5–%95 aralığı −27,99 … −12,54. Normalizasyon kullanıcının tercihidir,
korpusun dayatması değil.

### Hizalama güveni ve sınırları

`align_score`, zorlamalı hizalayıcının kelime başına verdiği skordur;
sütun olarak yayımlanır, kapı değildir. İki bilinen sınırı belgelidir:
**rakamlar hizalanmaz** (okunuşa çevirip hizalama reddedildi; sözcük
damgası Whisper yedeğine düşer) ve **cümle başı kısa sözcüklerde çöp
hizalama** görülür (245 kelime, 289 klip, %2,12; sebebi bilinmiyor, parça
sınırı hipotezi elendi). Alanın 2026 değerlendirmesi de hizalayıcı
skorunun "modelin kendine güveni" olduğunu, doğrulukla karıştırılmaması
gerektiğini söylüyor.

**Makaleye:** §Kalite ölçümleri, §Sınırlar.

---

## Politika: önerilen alt küme (v6)

Politika konfigde sürümlüdür ve üç kuraldan oluşur:

- `speech_ratio ≥ 0,60`
- `internal_silence_sec ≤ 1,0`
- şu işaretlerden hiçbiri: `oversize`, `forced_split`, `gap_split`,
  `short`, `duplicate`, `boilerplate`, `background_music`

Politikanın tarihi, **kaldırılan** kuralların tarihidir; her biri kör
dinlemeyle düştü ve her birinin sütunu yayımlanmaya devam ediyor:

| kural | ne oldu | kanıt |
|---|---|---|
| `clip_ratio ≤ 0,002` | v5'te kaldırıldı | 536 klibin 532'si tek kanaldaydı (kanal özelliği, klip değil); 25 kliplik kör dinlemede 25/25 "eğitime girsin" |
| `word_confidence ≥ 0,60` | v6'da kaldırıldı | 30 klip, altı bant, kanal ve ölçüm gizli: 29'unda metin birebir doğru; eşik bu 30'un 15'ini eliyordu |
| `dnsmos_ovrl ≥ 3,0` | v4'te kaldırıldı, geri konmadı | kural konduğunda sütun hiç üretilmiyordu ve sessizce geçiyordu; sütun 31 Ağustos'tan beri var ama kural kör dinleme olmadan konmaz |

Buradaki örüntü makalenin ikinci sonucudur: **alanın standart kalite
eşikleri, dinleme denetimine sokulduğunda tutunamadı** ve eledikleri
kliplerin neredeyse tamamı dinleyiciye göre eğitime uygundu. Kanıt yükü
kapıdadır, veride değil.

Kör dinleme protokolü altı tur koşuldu (müzik ×2, sınır kesimi ×2,
`clip_ratio`, `word_confidence`): kanal ve skor gizlenir, klipler bantlara
dengelenir, cevaplar dosyaya yazılır. Politikaya girecek her yeni sinyal
için tekrarlanır.

**Makaleye:** §Politika, §Katkı (eşiksiz yayım).

---

## Yineleme: aynı metnin ayrı okuması yineleme değildir

Kural (6 Eylül 2026, kullanıcı kararı): aynı metin farklı bir okumayla
geçiyorsa **prozodi çeşitliliğidir ve tutulur**; yineleme, metnin aynı
**ve** sesin aynı olmasıdır. "Aynı ses" ölçüyle tanımlıdır: süre, LUFS,
RMS ve tepe değerlerinin birebir tutması (`dedupe.identity_fields`).
Kanal anahtara girmez — ölçümler tutuyorsa aynı kaydın kopyasıdır.

Karar ölçümle verildi (`scripts/probe_dedupe.py`, 1.840.404 klip):

| tanım | yineleme sayılan klip |
|---|---|
| metin + kanal (eski anahtar) | 72.839 |
| ölçülen **bütün** değerler birebir aynı | **0** |
| ses ölçümleri birebir aynı, kanal içinde | 592 |
| ses ölçümleri birebir aynı, kanal fark etmeksizin | 598 |
| süre 0,1 s / LUFS 0,1 dB'ye yuvarlanmış | 15.752 |

İkinci satır kuralın harfiyen uygulanamayacağını gösteriyor: kanalların
her bölüme koyduğu jenerik cümle üç bölümde de aynı ses (süre 3,12 s, LUFS
−12,88, RMS −12,67, tepe −0,05 birebir) ama `word_confidence` ve
`leading_silence_sec` farklı, çünkü bunlar sesin değil klibin çevresinin
ölçümü. Son satır ise fazla gevşek: "Hayır."ın 0,70 ve 0,74 saniyelik iki
ayrı okuması aynı kovaya düşüyor.

Manifestte yineleme işareti taşıyan klip: **576.** Bunların 453'ü tek
kanalda (`seslimakalem`) toplanıyor — o kanalın bölüm jeneriği. 150 klibin
ses kimliği kurulamıyor (okunamayan ses) ve yineleme aranmadan geçiliyor.

**Makaleye:** §Yöntem (yineleme tanımı), §Veri (576 klip).

---

## Değerlendirme bölmesi: train / dev / test

6 Eylül 2026, `kiraat/split.py` + `scripts/make_splits.py`.

Bölme **kayıt düzeyindedir**: bir kaydın klipleri tek bölmeye girer, yani
değerlendirme modelin hiç duymadığı bir kayıt üzerinde yapılır. `test` ve
`dev` **kanal dengelidir** (kanal başına eşit süre hedefi), çünkü korpusun
kanal payları çok dengesiz ve değerlendirme kümesi o dengesizliği taşırsa
raporlanan sayı iki kanalın sayısı olur. Kanalın klipli kayıtlarından en az
biri `train`'de kalır; kayıtlar saatlerce sürdüğü için dev/test kanal
başına saat hedefine indirilir ve hedefi aşan klipler `train`'e **geçmez**,
kullanılmadan bırakılır — bölmenin tek garantisi budur.

| bölme | klip | saat | kayıt | kanal |
|---|---|---|---|---|
| train | 1.512.448 | 2.517,08 | 2.579 | 27 |
| dev | 5.750 | 9,54 | 40 | 27 |
| test | 5.473 | 9,30 | 45 | 27 |

Sızıntı denetimi: **kayıt sızıntısı 0** (kurulum gereği, yine de sınanır);
metin sızıntısı temizlik öncesi test 2.263 / dev 2.723 klip — bunlar
`train` ile birebir aynı cümleyi taşıyordu ve değerlendirme kümesinden
düşürüldü, `train` dokunulmadı; **temizlik sonrası kalan sızıntı 0**.

Eksik: test kümesinin elle doğrulanması. Küme kurulu ve denetimi temiz ama
"elle doğrulanmış" sıfatını hak etmesi için bir dinleme turu gerekiyor.

**Makaleye:** §Değerlendirme kümesi.

---

## Konuşmacı: eşik veriden, küme sayısı verilmeden

`speaker` aşaması kayıt başına ECAPA-TDNN merkez vektörü ve kayıt içi
tutarlılık ölçer; **kim kimdir kararı aşamada verilmez.** Kümeleme korpus
düzeyinde yapılır (`scripts/cluster_speakers.py`) ve birleştirme eşiği
ölçülen iki dağılımın eşit hata noktasından alınır; küme sayısı hiçbir
yerde verilmez.

Ölçüm (6 Eylül 2026, 27 kanaldan 105 kayıt, kayıt başına 8 klip ≥3 s):

| dağılım | çift | p05 | p50 | p95 |
|---|---|---|---|---|
| kayıt içi (klip–klip) | 2.940 | 0,560 | 0,742 | 0,853 |
| aynı kanal (kayıt–kayıt) | 153 | 0,131 | 0,872 | 0,940 |
| farklı kanal (kayıt–kayıt) | 5.307 | 0,053 | 0,179 | 0,420 |

Eşit hata noktası **0,483**, oradaki hata **%1,9**. Bu eşikle ortalama
bağlantılı birleştirme: 105 kayıt → **31 küme**, en büyüğü 8 kayıt, 6 küme
tek kayıtlık, kenar payı medyanı 0,507, **negatif kenar paylı kayıt yok**.

İki bulgu tasarıma dokunuyor. Aynı kanal dağılımının p05'i 0,131: **kanal
konuşmacı değildir** — 27 kanalın 8'i birden çok konuşmacı barındırıyor.
Ve 31 kümenin 9'u birden çok kanala yayılıyor: aynı seslendiren birden çok
kanalda yayımlıyor, dolayısıyla kanal dengesi konuşmacı dengesi değildir.

Ölçüm 105 kayıtlık örneklemdir; tam korpusta tekrarlanıp sütun olarak
bağlanması sırada.

**Makaleye:** §Konuşmacı, §Sınırlar (kanal ≠ konuşmacı).

---

## Hız ve maliyet (yeniden üretilebilirlik)

Tek makine: RTX 3090 (24 GB) + 12 CPU işçisi. Tam koşuda ölçülenler:

| aşama | havuz | ölçülen hız | 1,84 M klip / 3.440 saat için |
|---|---|---|---|
| `align` | GPU | 94 ses-saati/saat (tek işçi); iki işçiyle 91 | darboğaz aşaması |
| `clip_qc` | CPU | 46 klip/s = 166 bin klip/saat (12 işçi) | ~11 saat |
| `music` | GPU | 28 klip/s (iki GPU işçisi) | ~18 saat |
| `dnsmos` | GPU | 81,1 klip/s = 292 bin klip/saat | 6,30 saat |
| `speaker` | GPU | ~1 s/kayıt | ~45 dakika |
| `export` | CPU | — | 5 dakika |

`align` darboğazının profili ölçüldü: model ileri geçişi %56,
`F.merge_tokens` %28, `forced_align` %10. `merge_tokens` skor tensörü
GPU'da kaldığı için her belirteç aralığında ayrı senkron yapıyor; skorlar
CPU'ya alınınca aynı kaynak 109× yerine **188× gerçek zamanda** hizalanıyor
ve çıktı özdeş kalıyor.

Disk: `work/full-1` 567 GB — ara ses 284 GB (24 kHz mono FLAC), klipler
246 GB (1,84 M klipte ortalama ~159 KB), align 2,7, asr 1,5, veritabanı
1,4 GB. Ara ses HF yayınına kadar saklanır.

GPU koşuları 280 W güç kapağı altında yapıldı (kart geçmişte kısa devre
gördü): 318 → 270 W, fan %96 → %73, iş çıkarma kaybı %6.

**Makaleye:** §Yeniden üretilebilirlik, §Hat maliyeti.

---

## Alanın yerleşik yöntemi: neyi paylaşıyoruz, nerede ayrılıyoruz

Okunanlar: Emilia / Emilia-Pipe (arXiv 2407.05361, 2501.15907), LibriTTS
(1904.02882), Libriheavy (2309.08105), GigaSpeech 2 (ACL 2025,
2406.11546), ManaTTS (NAACL 2025, 2409.07259), WenetSpeech4TTS, Hi-Fi TTS,
AutoPrep, MLS/YODAS/SPGISpeech, KazakhTTS/KazakhTTS2, BibleTTS ve hizalama
araçlarının 2026 durum değerlendirmesi (2606.18466).

**Ortaklaştığımız yerler.** LibriTTS kesimi sessizlikte değil cümle
sınırında yapar ve gerekçesi bizimkiyle aynıdır: cümle düzeyi bürün ancak
cümle bütünken öğrenilir; Libriheavy de kesimi cümle sınırına koyar.
LibriTTS 16 kHz'i "yüksek kaliteli TTS için çok düşük" bulup 24 kHz'e
geçer; Emilia da 24 kHz'de yayımlar. LibriTTS hem ham hem normalize metni
yayımlar; bizde bu üç alandır (`text_raw`, `text`, `text_spoken`).
GigaSpeech 2, düşük kaynaklı diller için tam bizim sıramızı kurar: Whisper
ile yaz, MMS ile zorlamalı hizala, sonra çok boyutlu süz.

**Ayrıldığımız yer — eşik.** Yerleşik hatların hepsi kalite ölçüsünü kapı
yapar: Emilia DNSMOS OVRL ≥ 3,0 altındaki her klibi atar (Emilia-Large'da
2,4), LibriTTS "clean" altkümesinde SNR ≥ 20 dB ister. LibriTTS'in daha
sıkı hattı LibriSpeech'in 982 saatini 585 saate indirir. kiraat hiçbir
eşikle klip elemez; ölçümü sütun olarak yayımlar ve kararı sürümlü
politikaya bırakır. Bu ayrılığın gerekçesi ölçülüdür: iki standart kalite
ölçüsü kör dinlemede tutunamadı (yukarıdaki politika tablosu).

**Ayrıldığımız yer — sese dokunmamak.** Emilia yayımladığı sesi kaynak
ayrıştırmasından geçirir ve −20 dBFS'e normalize eder; yayımlanan dalga
biçimi işlenmiş sestir. kiraat ayrıştırmayı yalnızca ölçmek için koşturur
ve sesi olduğu gibi bırakır, seviyeyi sütun olarak verir.

**Süre bandı.** Emilia 3–30 s, LibriTTS/Libriheavy 30 s'ye kadar, pratik
kılavuzlar 2–12 s. Bizde `min_sec 1,5` / `target 7` / `max 15`; üretilen
dağılım medyan 5,8 s, p95 10,6 s.

**Uzun kayıt konusunda literatür yol göstermiyor.** Emilia'nın girdileri
20,09–3.596,27 saniye aralığında, yani en uzunu bir saat. Libriheavy uzun
formu kitap metnine hizalayarak çözüyor; bizde referans metin yok. Bizim
korpusumuzda kayıtların %30,7'si dört saatin üstünde, en uzunu 14,9 saat —
"çok saatlik tek parça kaydı sabit bellekle işlemek" bu hattın kendi
sorunu ve makalede yöntem katkısı olarak anlatılacak.

**Makaleye:** §İlgili çalışmalar, §Katkı (eşiksiz yayım, çok saatlik kayıt).

---

## Bilinen sınırlar

- **Rakamlar hizalanmaz.** Zorlamalı hizalayıcının sözlüğünde rakam yok;
  o kelimelerin damgası ASR yedeğine düşer. Okunuşa çevirip hizalamak
  bilinçli olarak reddedildi (metnin kendisini değiştirirdi).
- **Cümle başı kısa sözcüklerde çöp hizalama:** 245 kelime, 289 klip
  (%2,12). Sebep bilinmiyor; parça sınırı hipotezi elendi.
- **Kanal yığılması:** önerilen alt kümede ilk iki kanalın payı %38,2.
- **Tek kodlama profili:** korpusun tamamı ~129 kb/s AAC, kaynak bant
  kesimi medyan 15,7 kHz; iki kanal 13 kHz civarında dar bantlı.
- **Konuşmacı kimliği henüz sütun değil:** ölçüm 105 kayıtlık örneklemde
  doğrulandı, tam korpusa bağlanmadı.

---

## Koşulacak deneyler

Makalenin dayanacağı ölçümlerden henüz yapılmamış olanlar. Biri
tamamlandığında yukarıya konu başlığı olarak taşınır ve buradan düşer.

1. **Korpusla TTS eğitip değerlendirme — nihai kanıt.** Alanın standardı:
   önerilen alt küme ve bütün korpusla ayrı ayrı model eğitip MOS/CMOS,
   CER/WER ve konuşmacı benzerliği raporlamak; politika ve katmanlamanın
   kanıtı aynı deneyden çıkar. Düzenek tasarlanacak.
2. **Test kümesinin elle doğrulanması.** Bölme kurulu ve sızıntısı sıfır;
   dinleme turu yapılmadı.
3. **Konuşmacı sütununun tam korpusa bağlanması.** Aşama yazıldı ve
   ölçüldü; 2.698 kayıtta koşturulup `speaker_id` sütunu üretilecek.
4. **Hizalama güveni geçerlemesi.** Kelime başına hizalama olasılığının
   transcript doğruluğuyla ilişkisi; insan referanslı küçük bir örneklemde
   CER ile karşılaştırma.
5. **`dnsmos_ovrl` eşiğinin kör dinlemesi.** Sütun korpusun tamamında var;
   ≥3,0 kuralının neyi eleyeceği ölçülebilir durumda. Kural ancak bantlara
   dengelenmiş bir dinleme turundan sonra konabilir.
6. **Şablon künye madenciliği.** Kelimesi kelimesine n-gram, "<yazar>'ın
   <kitap> adlı kitabından" gibi değişken yuvalı kalıpları bulamıyor.
   Sabit iskelet + yuva madenciliği ya da künye sözlüğüyle cümle düzeyinde
   işaret; kör dinlemeyle doğrulama.
7. **Klip başına dil kimliği.** Türkçe olmayan klipleri görünür kılar
   (Emilia ≥0,8 ile kapı yapıyor; bizde sütun olur). Model seçimi ister.
8. **`duration / n_words` dağılımı.** LibriTTS'in ses–metin uyuşmazlığı
   ölçüsü iki yayımlanan sütundan türetilebiliyor; aykırıların gerçekten
   uyuşmazlık olup olmadığı kör dinlemeyle sınanmalı. Düşük öncelik.
9. **Yayın paketi.** HF dışa aktarımı, parçalama, veri kartı
   (`python -m kiraat schema` çıktısından), kelime düzeyi damgaların ve
   kaynak düzeyi ölçümlerin yayımı.
