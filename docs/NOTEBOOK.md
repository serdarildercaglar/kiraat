# Araştırma defteri

Makale bu dosyadan yazılacak. Yapılan her iş — karar, ölçüm, deney, çıkmaz
sokak — tarihiyle buraya düşülür ve makalenin ilgili bölümüne hangi malzemeyi
verdiği yazılır. Amaç, yayın zamanı geldiğinde hiçbir sayının kaynağını
aramak zorunda kalmamak.

## Bu defterin kuralı

**Hiçbir kayıt önceki bir yayına ya da önceki bir veri kümesine atıf yapmaz.**
Makale sıfırdan yazılıyor; ne bir önceki sürümü genişletiyor, ne ondan
alıntılıyor, ne de onu bir taban olarak anıyor. Buradaki her sayı bu depodaki
kodla, bu depodaki konfigle ve ham kayıtlardan üretilmiş olmalı.

Bunun pratik sonucu şu: bir ölçüm başka bir yerde yapılmışsa, makaleye
girmeden önce **burada yeniden koşturulur**. Aksi hâlde makale, kaynağını
gösteremeyeceği bir sayıyı rapor etmiş olur. Aşağıda "yeniden koşulmalı"
diye işaretlenmiş kayıtlar tam olarak bu durumdadır.

Mühendislik gerekçelerinin tutulduğu `DESIGN.md` **iç belgedir** ve makale
malzemesi değildir; oradaki karşılaştırmalar makaleye taşınmaz.

## Hangi sayı geçerli (31 Ağu 2026)

Defter bir günlüktür: eski kayıtlar, o gün ölçüleni olduğu gibi tutar ve
silinmez. Ama makaleye yalnızca **bugün geçerli olan** sayı girer. Aşağıdaki
liste, hangi kaydın hâlâ geçerli olduğunu söyler; eskimiş yerlerde ayrıca
satır içi `Düzeltme` / `Geçersiz` notu vardır.

**Geçerli ölçümler.**

| ne | değer | kaynak |
|---|---|---|
| ham korpus | 3.440,2 saat, 2.698 okunabilir kayıt, 27 kanal | envanter, 30 Ağu (`work/inventory.jsonl`) |
| kayıt uzunluğu | medyan 41,4 dk, p99 517,7 dk, azami 14,92 saat; %30,7'si 4 saatten uzun | aynı |
| kaynak biçimi | 44,1 kHz stereo AAC ~129 kb/s; bant kesimi medyan 15,7 kHz | aynı |
| denetim örneklemi | `sample-25d`: 81 kaynak, 27 kanal, 13.628 klip / 23,18 saat | 31 Ağu koşusu, commit `afe1109` |
| önerilen alt küme | 11.285 klip (%82,8) / 18,97 saat, **politika v6** | aynı |
| ses yüksekliği | klip medyanı −21,5 LUFS; kanal medyanları −33,4 … −12,3 (21,1 LU) | aynı |
| DNSMOS P.835 | OVRL medyan 3,28 (p5 2,67 – p95 3,48); SIG 3,56; BAK 4,10 | aynı |
| müzik korelasyonu | Spearman(AudioSet, dB) +0,479, 3.097 ayrıştırılan klip | aynı |
| uzun kayıt sınavı | `long-smoke`: 14,92 saatlik tek kayıt, 7.170 klip / 13,46 saat | 30 Ağu |
| hız | 41,5× (dağıtıcılı, sample-25c, `dnsmos` aşaması öncesi); tek kaynak zincirinde 34,5× | 30 Ağu |
| klip aşaması maliyeti | `dnsmos` GPU'da ~13 ms/klip (CPU'daki 2,07 çekirdek-s geçersiz), `clip_qc` 0,10, `music` 0,11 çekirdek-s | 31 Ağu, sample-25d logu |
| tam koşu beklentisi | ~83 saat, ~557 GB, ~1,73 milyon klip | yukarıdakilerden |

**Geçersiz sayılar — makaleye girmez.**

- **Bu depoda üretilmemiş her sayı.** Korpus büyüklüğü bir dönem dışarıdan
  alınmış bir rakamla ("2.370 kayıt, 2.942 saat") anılıyordu; o rakam
  çıkarıldı, yerine ölçülen envanter geçti. Defterin kuralı gereği makale
  önceki bir yayına ya da veri kümesine ne taban ne atıf olarak değinir.
- **Eskimiş örnek koşular.** `sample-5*`, `sample-15`, `sample-24`,
  `sample-25`, `sample-25b` koşularının klip sayıları ve önerilen oranları
  yalnızca o günün hattını anlatır; hepsi silindi ve düzeltilmiş hatla
  `sample-25c` olarak, 31 Ağustos'ta (metin kuralları, LUFS, DNSMOS) da
  `sample-25d` olarak yeniden koşuldu. Korpus sayısı olarak yalnızca
  `sample-25d` ve `long-smoke` kullanılır; `sample-25c` yalnızca hız
  ölçümü (41,5×) ve ASR belirlenimciliği karşılaştırması için anılır. (Kör dinleme sonuçları
  koşudan bağımsızdır ve geçerliliğini korur.)
- **Politikadan düşmüş kurallar.** `dnsmos_ovrl ≥ 3,0` (v4'te kaldırıldı,
  o gün hiç ölçülmüyordu; sütun 31 Ağu'dan beri var ama kural kör dinleme
  olmadan geri konmadı), `clip_ratio ≤ 0,002` (v5, kör dinleme),
  `word_confidence ≥ 0,60` (v6, kör dinleme). Politika **v6**'dır ve üç
  kuralı vardır; bu üç eşik makalede yürürlükteymiş gibi anlatılamaz.
- **Uygulanmamış ayarlar.** `export.max_hours_per_channel: 120` hiçbir
  zaman kod tarafından okunmadı ve kaldırıldı; kanal başına saat tavanı
  **yoktur**. Aynı şekilde müzik eşiğinin ilk tahmini −30 dB kör dinlemeyle
  çürütüldü, geçerli eşik **−40 dB**'dir.
- **Müzik korelasyonunun v1 ölçümü** (+0,799, 28 Ağu, 70 v1 klibi) bu depoda
  tekrarlandı ve yerine +0,479 geçti (31 Ağu, 3.097 klip).
- **Dağıtıcı öncesi hız tahminleri** (10,9×, 27×, 31×, 38×) hattın o günkü
  hâlini anlatır; geçerli hız 41,5×'tir.

---

---

## 2026-08-28 — Korpusun adı ve kapsamı

Ad `kiraat`; "sesli okuma" anlamındaki *kıraat* sözcüğünden. Makalede KIRAAT,
depo `kiraat`, veri kümesi kimliği `kiraat-turkish-read-speech` olarak
planlandı. Ayırt edici adın makalede, tarif edici kimliğin arama
görünürlüğünde işe yaraması amaçlandı.

Ham malzeme, Türkçe sesli kitap, sesli edebiyat ve sesli makale yayınlayan
herkese açık YouTube kanallarından derlenmiş kayıtlardır. Kaynakların telif
durumu temizlenmemiştir; yayın politikası ve kaldırma yolu, veri kümesi
kartında ayrıca ele alınacak.

> **Düzeltme (31 Ağu 2026).** Bu kayıtta önce "2.370 kayıt, 2.942 saat"
> yazıyordu; o sayı bu depoda ölçülmemişti, dolayısıyla defterin kuralına
> göre makaleye giremez ve buradan çıkarıldı. Ölçülen kapsam **2.698
> okunabilir kayıt, 3.440,2 saat, 27 kanal** (30 Ağu 2026,
> `scripts/inventory.py`); §Korpus'a giren sayı odur.

**Makaleye:** §Korpus (kapsam ve etik çerçevesi; sayılar envanter
kaydından), §Etik ve lisans.

## 2026-08-28 — Cümle hizalı bölütleme

Hattın merkezî tasarım kararı: kesim, sessizlik tespitinde değil, ASR ve
zorlamalı hizalamadan gelen kelime zaman damgaları üzerinde **cümle
sınırlarında** yapılır. Gerekçe, seslendirenin nefes yerleriyle cümle
sınırlarının örtüşmemesi; sessizliğe göre kesmek cümleyi ortadan böler.

Uygulama `kiraat/segment.py`. Sözleşme testle sabitlendi
(`tests/test_segment.py`): üretilen hiçbir klip küçük harfle başlamaz, hepsi
cümle sonu noktalamasıyla biter, hiçbir kelime kaybolmaz. Tek başına üst
süre sınırını aşan cümle iç noktalamasından bölünür ve `forced_split`
işaretiyle ayrılabilir; bölünemiyorsa atılmaz, `oversize` işaretiyle bütün
olarak çıkar.

**Yeniden koşulmalı — ablasyon.** Makalenin asıl iddiası bu kararın ölçülmüş
karşılığı olacak. Aynı ham kayıtlar üzerinde iki bölütleme koşturulup
karşılaştırılmalı: (a) yalnız VAD tabanlı kesim, (b) cümle hizalı kesim.
Raporlanacak ölçüler: cümle ortasından başlayan klip oranı, cümle sonu
noktalamasıyla bitmeyen klip oranı, süre dağılımı, ve kelime başına hizalama
güveni. Bu deney henüz koşulmadı.

**Makaleye:** §Yöntem, §Ablasyon (ana sonuç tablosu).

## 2026-08-28 — Skor tabanlı çıktı sözleşmesi

İkinci tasarım kararı: hiçbir eşik klip elemez. Klip aşamaları yalnızca ölçüm
üretir; önerilen alt küme, konfigde sürümlenen bir kural listesinden
hesaplanır ve her dışlamanın gerekçesi klip kaydına yazılır. Sözleşme kodda
zorunlu: `ClipStage.validate_output`, bir aşamanın çıktısına
`recommended`/`decision` yazmasını hata olarak reddeder.

Bunun yayın açısından değeri, korpusun tek bir politika kararına
kilitlenmemesi: politika değişince veri yeniden üretilmiyor, yalnızca bayrak
yeniden hesaplanıyor ve kullanıcı kendi eşiğini kesebiliyor.

**Makaleye:** §Yöntem, §Yayın politikası. Politika sürümü ve kural listesi
makalede olduğu gibi verilebilir.

## 2026-08-28 — Türkçe metin politikası

Üç metin alanı üretiliyor ve üçü de yayımlanacak: `text_raw` (ASR çıktısı),
`text` (hafif temizlik), `text_spoken` (okunuşa çevrilmiş, eğitimde
kullanılan). Okunuşa çevirme Türkçe sayılar (`1923` → "bin dokuz yüz yirmi
üç"), sıra sayıları, yüzde, para birimi, saat, ondalık ve kısaltma
açılımlarını kapsıyor; `kiraat/text/normalize.py`, 30 testle.

Cümle sınırı bulma ayrı bir sorun ve kısaltmalar, tek harfli baş harfler,
sıra sayıları ile tırnak kapanışları elle ele alındı
(`kiraat/text/sentences.py`). Türkçeye özgü harf eşlemesi (I/ı, i/İ) ayrı bir
modülde toplandı; `str.lower()` bu depoda kullanılmıyor.

**Makaleye:** §Metin işleme. Normalizasyon kapsamı tablo olarak verilebilir.

## 2026-08-28 — Arka plan müziği ölçümü (deney)

**Soru:** bir klipte konuşmanın altında müzik olup olmadığı nasıl ölçülür?

Üç aday sinyal karşılaştırıldı. Birincisi AudioSet AST'nin müzik etiketleri
üzerinden alınan çok etiketli skor — ucuz, konuşmayla birlikte var olabiliyor.
İkincisi kaynak ayrıştırmasından (torchaudio `HDEMUCS_HIGH_MUSDB_PLUS`) gelen
fiziksel ölçü: eşlik enerjisinin konuşma enerjisine oranı, dB. Üçüncüsü
harici, ikili bir konuşma/müzik sınıflandırıcısı.

**Sonuç.** 70 klip, AudioSet skorunun beş bandından katmanlı örneklemeyle
seçildi. Ayrıştırma tabanlı dB ölçüsüyle sıra korelasyonları: AudioSet skoru
**+0,799**, harici ikili sınıflandırıcı **+0,311**. İkili sınıflandırıcı
soruyu yanıtlamıyor — hiç müziği olmayan kliplere 0,999 ve 0,915, müziği
−22 dB'de açıkça duyulan kliplere 0,006 ve 0,009 verdi. Bunun sebebi
yapısal: birbirini dışlayan iki sınıfla eğitilmiş bir model için "altında
müzik olan konuşma" diye bir kategori yok.

AudioSet skoru güçlü bir yordayıcı ama tek başına yetmiyor; örneklemde
AudioSet 0,444 olan bir klipte hiç müzik yokken (−80 dB), 0,050 olan bir
klipte müzik −15,7 dB'de, yani açıkça duyulur durumda.

**Karar.** Üç sütun da yayımlanır (`music_score_audioset`,
`music_to_speech_db`, isteğe bağlı `music_prob_external`); ikili "müzik var
mı" yanıtı yayımlanan dB sütunundan eşikle türetilir, böylece yeniden
kesilebilir. Harici model varsayılan olarak kapalı.

**Yeniden koşulmalı.** Örneklem başka bir kaynaktan çekildi; makaleye girmeden
önce aynı deney bu depodaki klipler üzerinde tekrarlanmalı. Ölçüm betiği
`scripts/probe_music.py` hazır, girdi manifestosunu değiştirmek yetiyor.

**Makaleye:** §Kalite ölçümleri, §Ablasyon (ikincil sonuç).

## 2026-08-28 — Bölütleme, gerçek kayıtlarda ilk koşu (örnek)

Hat henüz uçtan uca bağlı değil; bu koşu hazır parçaları (uzun form ASR →
`kiraat.segment.segment`) beş kaydın ilk altı dakikasına elle bağlayarak
yapıldı: `scripts/probe_segment.py`. Beş kayıt beş ayrı kanaldan seçildi,
toplam 28,7 dakika, 3.059 kelime. ASR `faster-whisper` large-v3
(`condition_on_previous_text=false`, sıcaklık 0, VAD yalnızca konuşma bölgesi
bulucu); kelime zaman damgaları Whisper'ın kendi hizalamasından, çünkü
konfigdeki zorlamalı hizalayıcı henüz bağlanmadı. Bu yüzden buradaki sayılar
**hizalayıcı bağlandığında yeniden koşulmalı**.

**Sonuç.** 143 klip üretildi. Küçük harfle başlayan klip **0**; cümle sonu
noktalamasıyla bitmeyen **2** (%1,4), ikisi de `forced_split` işaretli, yani
tasarımın öngördüğü ve önerilen alt kümeden düşen istisna. Süre medyanı
11,5 s (p5 5,3, p95 18,6). İşaretler: `forced_split` 2, `oversize` 2,
`short` 3. Klip başına asgari kelime olasılığı medyan 0,794; 0,40'ın
altında 4 klip.

**Çıktıda görülen üç kusur** — hepsi bölütleyicinin dışında, ama hattın
sorumluluğunda:

1. *Künye sızması.* Kaydın başındaki başlık ve seslendiren künyesi
   ("… seslendiren Vasfiye Sarıkaya Sanki bir tufandı.") ilk cümleye
   yapışıyor, çünkü ASR künyeden sonra noktalama koymuyor ve boilerplate
   aşaması henüz yok. Beş kaydın üçünde ilk klip böyle.
2. *Uzun sessizlik cümleyi bölmüyor.* Bir kayıtta başlık ile ilk cümle
   arasında 49 saniyelik boşluk var (giriş müziği), ama noktalama olmadığı
   için bölütleyici ikisini tek "cümle" sayıp 53,9 saniyelik `oversize`
   klip üretti. `_split_oversize` iç noktalama bulamayınca uzun iç
   boşluğu (`max_join_gap_sec` üstü) kesim adayı saymalı.
3. *Kesme işaretinde bölünen belirteçler.* Whisper "Button 'ın",
   "Arz -ı Mev 'ud" gibi 101/3.059 belirteci ayrı kelime olarak veriyor;
   metin bu hâliyle yayımlanamaz. ASR sonrası kelime birleştirme adımı
   (kesme/tire ile başlayan belirteç öncekine yapışır) gerekiyor.

**Kör dinleme denetimi (aynı gün).** 40 klip — kayıt başına 4 kiraat + 4
karşılaştırma klibi — kanal ve sistem gizli, karışık sırada bir dinleme
sayfasına kondu; sorular: cümle başında mı başlıyor, cümle bitince mi
bitiyor, başta/sonda kelime kesik mi. Anahtar
`work/probe_segment/listen/key.json`, cevaplar `listen/answers-1.json`.
Dinleyici 37/40 klibi cevapladı. kiraat'ın 20 klibinin **20'si** cümle
başında başlıyor ve cümle sonunda bitiyor; karşılaştırma kliplerinde 2
kırık başlangıç, 3 kırık bitiş, 3 kesik kelime. Yani metin ölçüsü
(küçük harf / noktalama) ile kulak aynı şeyi söylüyor.

Tek kusur, bir kiraat klibinde başa **önceki kelimenin son harfinin
sızması** (çeyrek saniyeden az). Sebebi kelime zaman damgalarında:
"kurduruyordu." 121,62'de bitiyor, "Bu" 121,74'te başlıyor, aradaki
boşluk 0,12 s; `lead_pad_sec` 0,15 olduğu için klip başı önceki kelimenin
bitişine dayanıyor ve Whisper'ın kelime bitişleri erken olduğundan sesin
kuyruğu içeri giriyor. Örneklemde cümle sonundan sonraki boşlukların
%28'i 0,15 s'nin altında (90/318, 30'u sıfır), yani bu tekil bir vaka
değil. İki çözüm birlikte gerekli: pay, komşu kelimeye dayanmak yerine
boşluğun ortasında durmalı (`_pad`), ve kelime bitişleri zorlamalı
hizalayıcıdan gelmeli.

**Ayrıca ölçüldü (modelsiz).** Metin normalizasyonu 50.000 cümlelik bir
örnekte `text` üzerinde %5,28 satırı değiştiriyor (sayı, ondalık, yüzde,
yıl), hafif temizlik %2,30; hata yok. İki kusur görüldü: "6. Bölüm" →
"altı. Bölüm" (büyük harfli sıra sayısı takipçisi tanınmıyor) ve "1922'de" →
"bin dokuz yüz yirmi iki'de" (ek, kesme işaretiyle kalıyor). Yineleme
işaretleme (metin, konuşmacı) anahtarıyla 416 bin klipte 13 saniyede
çalışıyor; farklı kanallarda tekrar eden 1.532 metin doğru biçimde
korunuyor.

**Makaleye:** §Ablasyon (ön sonuç; hizalayıcıyla yeniden koşulacak),
§Metin işleme (bilinen sınırlar).

## 2026-08-28 — Klip süresi: birleştirme kuralı ve tavan kararı

İlk koşuda süre medyanı 11,5 s, p95 18,6 s çıktı; hedef 9 s iken. Kaynağı
cümleler değil (tek cümle medyanı 4,0 s, 295 cümlenin yalnızca 42'si 9 s
üstü), birleştirme kuralı: gruba "hedefe ulaşana kadar" cümle ekleniyordu,
bu da klipleri hedef artı bir cümle uzunluğuna taşıyordu.

**Karar.** Kural "hedefi aşma" olarak değiştirildi: grup `min_sec` üstündeyse
ve bir cümle daha eklemek hedefi aşacaksa grup kapanır
(`kiraat/segment.py`, testi `test_birlestirme_hedefi_asmaz`). Hedef 7 s,
tavan 15 s. Tavan eğitim bütçesiyle tutarlı seçildi: dizi bütçesi ~25 s
hedef sese izin veriyor ama otoregresif model eğitimde gördüğü sürenin
ötesine iyi genellemediği için tek seferde üretilmesi beklenen en uzun
cümle (15 s) tavan alındı; tek cümlelerin %97'si zaten bu sürenin altında,
dolayısıyla tavan iç noktalamada bölmeye nadiren zorluyor.

**Aynı beş kayıtta yeniden koşu (ASR önbellekten).** 232 klip, medyan
6,7 s (p5 3,7, p95 13,6); dağılım 5 s altı 60, 5–10 s 132, 10–15 s 37,
15 s üstü 3 (üçü de `oversize`, yani iç noktalaması olmayan tek cümleler).
Küçük harfle başlayan 2, cümle sonu olmayan 8; bunların **hepsi
`forced_split` işaretli** ve önerilen alt kümeden düşüyor — tek istisna
pencere sonunda kesilen son klip, o da deneme penceresinin ürünü. 211/232
klip işaretsiz. `forced_split` sayısı 2'den 14'e çıktı ve 10'u tek
kanalda (uzun, liste gibi cümleler); tavanı düşürmenin bedeli bu ve
kabul edildi.

**Makaleye:** §Yöntem (süre politikası ve gerekçesi), §Korpus (süre
dağılımı — hizalayıcı bağlanınca tam koşuda yeniden ölçülecek).

## 2026-08-28 — Dört düzeltme ve ikinci koşu

İlk koşuda görülen kusurlar düzeltildi ve aynı beş kayıt yeniden koşuldu
(ASR önbellekten; 233 klip, medyan 6,6 s, p95 13,3 s).

1. **Sınır payı boşluğun ortasını geçmiyor** (`segment._pad`). Kör
   dinlemede duyulan harf sızmasının sebebi payın komşu kelimenin bitişine
   dayanmasıydı. Bu koşuda 54 klibin baş boşluğu 0,15 s'nin altında; ikinci
   dinleme turu bunlara öncelik veriyor.
2. **Noktalamasız uzun "cümle" uzun iç sessizlikte kesiliyor**
   (`_split_oversize`, `gap_split` işareti). 54 saniyelik klip artık 3,8 s'lik
   başlık ("Edgar Allan Poe'dan Kuyu ve Sarkaç", `gap_split`) ve temiz bir
   ilk cümle ("Bitkindim. O uzun acıyla…", işaretsiz). Metin olarak bütün
   görünen parça işaret almıyor; kırık görünen alıyor ve önerilen alt
   kümeden düşüyor.
3. **Kesme işaretinde bölünen ekler birleştiriliyor** (`attach_clitics`):
   "Button 'ın" → "Button'ın", "Arz -ı Mev 'ud" → "Arz-ı Mev'ud". Açılış
   tırnağıyla başlayan gerçek kelimelere dokunulmuyor.
4. **Boilerplate madenciliği** (`kiraat/boilerplate.py`,
   `scripts/probe_boilerplate.py`): kanal başına 8 kaydın ilk ve son
   dakikası çözülüp en az 3 kayıtta kelimesi kelimesine tekrar eden diziler
   arandı. Bulunanlar: BirDinle "seslendiren vasfiye sarıkaya" (5/8),
   ses-arşiv "son altyazı m k" (3/8 — ASR halüsinasyonu, tam da istenen
   yakalama), idea_stüdyo "dinlediğiniz için teşekkür ederiz" (5/8) ve
   "abone olmayı unutmayınız" (3/8); anahtarca'da künye yok, 0. Bulunan
   aralıklar bölütleyicide ayrı klip oluyor ve `boilerplate` işareti
   taşıyor: "Ferman Ömer Seyfettin | seslendiren Vasfiye Sarıkaya | Sanki
   bir tufandı. Gök delinmiş…" — ilk gerçek cümle artık künyeden temiz.
   **Sınır:** dinleyiniz'de künye "Yazan X Seslendiren Y" kalıbında ama
   isimler kayıt başına değiştiği için kelimesi kelimesine tekrar 0 ifade
   verdi. Kalıp madenciliği (isim yuvalı şablon) ayrıca gerekecek; şimdilik
   o kanalda künye ilk klibe yapışık kalıyor ve yalnızca `short`/`no_end`
   ölçüleriyle görünür.

**Sonuç.** 233 klibin 209'u işaretsiz. Kırık uçlu 14 klibin 13'ü
işaretli (`forced_split` 12, `gap_split` 4, `boilerplate` 1, `short` 6 —
çakışmalı); işaretsiz tek kırık klip 6 dakikalık deneme penceresinin
sonunda kesilen klip. Süre dağılımı: 5 s altı 63, 5–10 s 131, 10–15 s 37,
15 s üstü 2 (`oversize`).

**İkinci kör dinleme turu** yayına kondu: 32 klip (24 kiraat — baş/son
boşluğu 0,15 s altındakiler öncelikli, yani pay düzeltmesinin sınandığı
yer — ve 8 karşılaştırma klibi). Sayfa `scripts/listen_ui.py` ile
üretiliyor, cevap `--score` ile anahtarla eşleştiriliyor.

**Makaleye:** §Yöntem (boilerplate ve süre politikası), §Korpus (işaret
dağılımı). Sayılar hizalayıcı bağlanınca tam koşuda yenilenecek.

## 2026-08-28 — İkinci kör dinleme: kesik son hece ve sıfır boşluk

32 klibin 32'si cevaplandı (`work/probe_segment/listen/answers-2.json`).
kiraat'ın 24 klibinde kırık başlangıç **0**, kırık bitiş 2 (ikisi de
`forced_split`, yani beklenen istisna), ama **3 klipte son hece kesik**:
"anımsatıyor|du", "hissetti|m", "vardır|." Karşılaştırma kliplerinde
kesik yok (8'de 0), kırık bitiş 1.

**Teşhis.** Üç klibin üçünde de son kelimenin bitişi ile sonraki kelimenin
başlangıcı Whisper'da aynı zaman damgası (boşluk 0,0 s): "anımsatıyordu."
144,79–145,39 → "Ekim" 145,39. Whisper bir kelimenin bitişini bir
sonrakinin başına yapıştırdığında boşluğu ortadan bölmenin de payın da
verebileceği bir şey kalmıyor ve kelime bitişi erken olduğu için son hece
dışarıda kalıyor. Dinlenen 24 klipte son boşluğu sıfır olan 6 klip vardı,
3'ü kesik çıktı; sıfırdan büyük boşluklu 18 klipte hiç kesik yok. Tüm
koşuda 233 klibin 22'sinde (%10) son boşluk sıfır, 22'sinde baş boşluk
sıfır; yani kusur örneklemin değil zaman damgasının.

**Çıkarım.** Sınır, ASR zaman damgasından değil sesten alınmalı: iki klip
arasındaki gerçek sessizlik, damganın yakınında ama tam üstünde değil.
Bölütleyici bugün sese hiç bakmıyor; komşu klipler arasında damga
çevresinde küçük bir pencerede en düşük enerjili noktayı (nefes/sessizlik)
bulup sınırı oraya çekmek gerekiyor. Zorlamalı hizalayıcı bağlansa da bu
adım kalmalı, çünkü hizalayıcı da kelime sınırını ses enerjisine göre
değil harf olasılığına göre koyar.

**Makaleye:** §Yöntem (sınır iyileştirme adımı, gerekçesiyle).

## 2026-08-28 — Ses tabanlı sınır iyileştirme

Bir önceki kaydın çıkarımı uygulandı: `kiraat/boundaries.py`. Bölütlemeden
sonra, damgalar arası boşluğun iki payı da (0,15 + 0,25 s) barındıramadığı
her komşu klip çiftinde, önceki klibin son kelime damgasından 0,05 s önce
başlayıp 0,6 s sonrasına uzanan pencerede 20 ms'lik enerji zarfına bakılır.
Yerel konuşma seviyesinin (±1 s içinde 90. yüzdelik) 25 dB altındaki en az
60 ms'lik en uzun sessizlik bulunursa önceki klip o sessizliğe 0,25 s
uzar, sonraki klip sessizliğin sonundan 0,15 s önce başlar; sessizlik
yoksa ikisi de penceredeki en sessiz ana konur. Pencere sonraki kelimenin
damgasıyla kısılmaz — boşluk sıfırken o damga da yanlıştır — ama önceki
kelimenin başına taşamaz ve klipler çakışmaz. Üç sentetik test
(`tests/test_boundaries.py`): 80 ms erken biten damga sessizliğe düşer,
kesintisiz konuşmada en sessiz an seçilir, geniş boşluklu çiftlere
dokunulmaz.

**Aynı beş kayıtta.** 233 klibin 92 çiftinde sınır taşındı; klip sonu ASR
damgasına göre medyan **+0,35 s** ileri (en az +0,03, en çok +0,69).
Sıfır boşluklu 22 klibin hepsi en az 0,05 s uzadı. İkinci turda kesik
bulunan üç klip: +0,38, +0,35, +0,61 s. Çakışan çift 0. Süre dağılımı
değişmedi (medyan 6,7 s).

**Üçüncü kör dinleme turu** yayına kondu: 32 klip, 28'i kiraat ve sıfır
boşluklu klipler öncelikli — yani düzeltmenin tam hedefi — 4'ü
karşılaştırma. Soru aynı: kesik hece var mı.

**Makaleye:** §Yöntem (sınır iyileştirme; hizalayıcı bağlansa da kalır).

## 2026-08-28 — Üçüncü kör dinleme: sıfır boşluklu kliplerde kesik yok

32 klibin 32'si cevaplandı (`work/probe_segment/listen/answers-3.json`).
kiraat'ın 28 klibi — hepsi sıfır boşluklu, yani ikinci turda kesik veren
sınıfın tamamı — **28/28 temiz**: kırık başlangıç 0, kırık bitiş 0, kesik
hece 0. Karşılaştırma kliplerinde 4'te 1 kırık bitiş (cümle ortasından
giren "sizin olacak denilmiştir. …" klibi), kesik yok.

Üç turun toplamı, kiraat klipleri için: 72 dinlenen klipte kırık
başlangıç 0; kırık bitiş 2, ikisi de `forced_split` işaretli; kesik hece
ikinci turda 3 (zaman damgası kusuru), üçüncü turda ses tabanlı sınırla
0. Sınır artık ASR damgasından değil sessizlikten alınıyor ve bu adım
hizalayıcı bağlansa da kalacak.

**Makaleye:** §Değerlendirme — kör dinleme protokolü ve sonuçları (tur
başına klip sayısı, soru seti, kiraat/karşılaştırma ayrımı gizli).

## 2026-08-28 — Hattın gövdesi ve ilk uçtan uca örnek koşu

Bölütleme çekirdeği kapandıktan sonra hattın gövdesi yazıldı: sqlite durum
deposu (`kiraat/store.py`), orkestratör (`kiraat/pipeline.py`,
`python -m kiraat run`) ve aşamalar `prepare` (ffmpeg, 24 kHz mono,
40 Hz yüksek geçiren, −1 dB tepe) → `asr` (faster-whisper large-v3, VAD
yalnızca bölge bulucu) → `boilerplate` (kanal düzeyi) → `segment`
(ek birleştirme, boilerplate aralıkları, cümle hizalı kesim, ses tabanlı
sınır, flac kesimi, üç metin alanı) → `clip_qc` (silero konuşma oranı,
kırpma, iç sessizlik, seviye) → `music` → `export` (politika, yineleme,
manifest). Her aşama bitirdiği nesneyi sürümüyle `done` tablosuna yazar;
yeniden koşu ucuzdur. Kaynak seçimi kanal-dönüşümlüdür.

**Örnek koşu** (`runtime.max_sources: 5`, beş kanaldan birer kayıt, 8,4
saat kapsayıcı süresi, `work/run-1.log`): 24 dakikada hatasız bitti.
ASR toplam 14,8 dk (BirDinle'nin 161 dakikası 479 s), bölütleme 3 dk,
clip_qc 3,7 dk, music 1,7 dk. **2.649 klip, 4,87 saat**; süre medyanı
6,1 s (p5 3,0, p95 12,5), 15 s üstü 27. Önerilen alt küme 2.134 klip
(%80,6), 3,79 saat. İşaretler: `forced_split` 110, `short` 81,
`gap_split` 37, `oversize` 23, `background_music` 2. Metin: küçük harfle
başlayan %2,3 ve cümle sonu olmayan %3,1 (hepsi işaretli parçalar),
`text_spoken ≠ text` %3,9. Konuşma oranı medyanı 0,93, kelime güveni
medyanı 0,888.

**Üç bulgu.**

1. *Kesik kaynak.* bizimkütüphane kaydının kapsayıcısı 210 dk diyor,
   çözülen ses 19,4 dk ("partial file"); ffmpeg yine de 0 döndürüyor ve hat
   kapsayıcı süresini kaydetmişti. Düzeltildi: süre çözülen sesten
   alınır, kapsayıcı süresi ayrıca tutulur, oran `prepare.truncated_ratio`
   altındaysa kayıt `truncated_source` işareti alır ve işlenmeye devam eder.
   Ham malzemede başka kesik dosya olup olmadığı tam koşuda görülecek.
2. *Künye sızması, beklenen biçimde.* Kanal başına tek kayıt olduğu için
   madencilik hiçbir ifade bulamadı ve "Efsuncu Baba, Hüseyin Rahmi
   Gürpınar, seslendiren Vasfiye Sarıkaya." ile "Kanalıma abone olmayı …
   unutmayın." klip oldu. Madencilik ≥3 kayıt ister; örnek koşunun bunu
   sınayabilmesi için `runtime.max_channels` eklendi (5 kanal × 3 kayıt =
   15 kaynak). Bu koşu ölçek kararıdır, onay bekler.
3. *Kelime güveni kuralı erken.* `word_confidence<0.6` kliplerin %10,4'ünü
   düşürüyor ama sütun hâlâ Whisper'ın kendi olasılığı; politika zorlamalı
   hizalama güveni için yazıldı. Hizalayıcı bağlanana kadar bu gerekçe
   geçici sayılmalı; politika değiştirilmedi.

**Makaleye:** §Hat (aşama sırası ve sözleşmeler), §Korpus (sayılar tam
koşuda yenilenecek).

## 2026-08-28 — Rastgele örneklemle tam koşu provası (24 kaynak)

Tam koşudan önce, tam koşuyu taklit eden bir örneklem: tohumlu rastgele
8 kanal × 3 kayıt = 24 kaynak (`runtime.sample_seed: 2026`,
`max_channels: 8`, `max_sources: 24`), ayrı çalışma dizini
`work/sample-24`, hattın tamamı. Kapsayıcı süresi 37,6 saat, çözülen ses
34,4 saat (bir kayıt kesik: 210 dk yerine 19 dk, `truncated_source`).

**Sonuç.** 3 saat 10 dakikada hatasız: **17.933 klip, 32,89 saat** (ses
saatinin %96'sı klibe dönüştü). Süre medyanı 6,2 s (p5 3,2, p95 12,0),
15 s üstü 152. Önerilen alt küme 14.033 klip (%78,3), 24,86 saat.
İşaretler: `background_music` 1.327 (%7,4), `forced_split` 857, `short`
240, `oversize` 111, `gap_split` 107, `duplicate` 15 (kanal anahtarlı),
`boilerplate` 6. Küçük harfle başlayan %2,6, cümle sonu olmayan %3,1;
`text_spoken ≠ text` %4,2.

**Kanal farkları.** Önerilen oran BirDinle %85, bizimkütüphane %86,
denizinötesindekisesler %87, seslikutuphanemkanali %83 iken Peri_Mia
**%32**: kliplerinin %63'ünde müzik −30 dB'nin üstünde (medyan −27,4 dB,
p90 −20,7) — masal anlatımının altında sürekli müzik. anahtarca'da %23,
Seslendiriyor'da %8. Yani `background_music` işareti kanal karakterini
ölçüyor; müziğin eğitimde kabul edilebilir düzeyi (−30 dB) kör dinlemeyle
doğrulanmalı, çünkü Peri_Mia gibi bir kanalın üçte ikisini eliyor.

**Boilerplate.** Sekiz kanaldan yalnızca bizimkütüphane'de ifade bulundu:
sponsor jingle'ı "Kitapların büyüsü kumaşlarda hayat buluyor. Book or Book,
kitaplardan ilham alan edebi zarafet." — 13 kelime, `max_words: 12`
yüzünden iki örtüşen 12'liye bölündü ve ilk kelime ("Kitapların") ayrı
`short` parça olarak kaldı. BirDinle'de "Seslendiren Vasfiye Sarıkaya"
bulunamadı: üç kaydından biri 0,4 dakikalık kanal fragmanı, künye iki
kayıtta kaldı, `min_recordings: 3` geçilemedi; künye ilk klibe 14 s
boyunca yapışık ("Peygamber Enoch'un kitabı Seslendiren Vasfiye Sarıkaya
Enoch'un kitabının…"). denizinötesindekisesler'in kapanışı ("Kanalıma abone
olmayı … unutmayın. Görüşmek üzere.") kayıttan kayıta küçük farklarla
değişiyor, kelimesi kelimesine eşleşme yakalamıyor. Üç düzeltme:
örtüşen ifadeleri birleştirmek ve `max_words`'ü büyütmek; `min_recordings`'i
kanal kayıt sayısına oranla (ör. ≥%40, en az 2) vermek; ve baş/son
bölgesinde **yaklaşık** eşleşme (kelime düzeyinde küçük düzenleme
uzaklığı). Tam koşuda kanal başına onlarca kayıt olacağı için ilk ikisi
yeterli olabilir; üçüncüsü ölçülerek karar verilir.

**Kelime güveni.** `word_confidence<0.6` her kanalda %6–11 klibi
düşürüyor ve düşenlerin çoğu metin olarak sağlam ("Besbelli milislerin
ücreti olan günde on pesatayla…"). Sütun hâlâ Whisper olasılığı;
hizalayıcı bağlanmadan bu kural klip kaybettiriyor. Öncelik: `align`.

**Ölçek.** Ses saati başına: prepare 0,27 dk, ASR 3,41 dk, bölütleme
0,66 dk (18 bin ffmpeg çağrısı), clip_qc 0,77 dk (silero, sıralı), music
0,40 dk; toplam 5,5 dk → **10,9× gerçek zaman**. (Bu satırda korpus
büyüklüğü olarak dışarıdan alınmış bir sayı kullanılıyordu; çıkarıldı —
ölçülen büyüklük 3.440,2 saattir ve hattın bugünkü hızı 41,5×'tir.)
Tam koşu bu hızla yapılmaz. ASR bu koşuda GPU'yu iki Whisper konteyneriyle
paylaştı (ilk koşuda 34× idi); yine de üç iyileştirme gerekli: toplu ASR
(faster-whisper `BatchedInferencePipeline`), klip kesimini tek geçişte
bellekten yazmak (ffmpeg çağrısı yerine soundfile), clip_qc'yi CPU
işçilerine dağıtmak. Hedef ≥30× → tam koşu ≈ 4 gün.

**Küçük.** "P .O .Y .M." gibi noktayla başlayan kısaltma parçaları
birleştirilmiyor.

**Kör dinleme (aynı gün).** 8 kanaldan 4'er önerilen klip, 32 klip,
kanal gizli: **32/32 temiz** — cümle başında başlıyor, cümle sonunda
bitiyor, kesik hece yok (`work/sample-24/listen/answers-1.json`).
Deneme kayıtlarındaki sonuç ölçekte de tutuyor; dört turun toplamında
kiraat'ın 104 önerilen/işaretsiz klibinde kırık başlangıç 0, kesik hece
yalnızca ikinci turun 3'ü (sınır iyileştirmesinden önce).

**Makaleye:** §Korpus (kanal düzeyinde müzik dağılımı), §Hat (ölçek ve
maliyet), §Kalite ölçümleri.

## 2026-08-29 — Dört iş birden: ölçek, hizalayıcı, müzik eşiği, boilerplate

Provanın dört bulgusu aynı gün uygulandı ve beş kaynaklık örnek temiz bir
dizinde (`work/sample-5b`, 5,22 saat ses) yeniden koşuldu.

**1. Ölçek: 10,9× → 31× gerçek zaman.** Toplu ASR (faster-whisper
`BatchedInferencePipeline`, `asr.batch_size: 16`; pencereler bağımsız
olduğu için önceki metne koşullanma zaten yok), klip kesimi kayıt başına
tek çözümle bellekten (soundfile; 18 bin ffmpeg süreci yerine), clip_qc
CPU işçi havuzunda. Ses saati başına dakika: ASR 3,41 → 0,77; bölütleme
0,66 → 0,25; clip_qc 0,77 → 0,15; music 0,40 → 0,27; yeni hizalama 0,31.
Toplam 5,5 → 1,95 dk/saat, yani **31× gerçek zaman** (önce 10,9×).
Not: GPU bu ölçümde iki boşta Whisper konteyneriyle paylaşılıyordu.

**2. Zorlamalı hizalama bağlandı** (`stages/align.py`, torchaudio MMS_FA,
unidecode ile romanizasyon, Whisper damgaları kılavuz olarak ~30 s
parçalar, CTC `forced_align`). 31.982 kelimenin %99,6'sı hizalandı.
Hizalayıcı damgası Whisper'a göre başta **+0,19 s** (p10 +0,11, p90
+0,41), sonda **+0,10 s** (p10 +0,03, p90 +0,20) ileride — Whisper'ın
"erken damga" kusuru artık sayıyla ölçülü. Bölütleme hizalanmış zamanları
kullanıyor; sınır iyileştirme üstünde kalıyor. Güven: klip başına asgari
hizalayıcı skoru medyan 0,40, ortalama 0,48; Whisper asgari olasılığıyla
sıra korelasyonu yalnızca +0,34 — iki sinyal farklı şeyler ölçüyor. 37
kelimede (%0,12) skor tam sıfır: hepsi cümle başındaki kısa sözcükler
("Bu", "Ey", "Biz"), hizalayıcı onları önceki cümlenin hemen ardındaki
40–140 ms'ye sıkıştırmış. Bu yüzden `word_confidence` kaynağı şimdilik
Whisper (`align.confidence_source: asr`), hizalayıcı skoru
`align_score_min/mean` olarak yayımlanıyor; kural olabilmesi için klip
düzeyinde asgari yerine dayanıklı bir istatistik (10. yüzdelik) ve insan
referanslı CER ile kalibrasyon gerekiyor (koşulacak deney 3).

[**Düzeltme, 29 Ağu 2026:** bu iki skor yanlıştı. Aşama emisyona fazladan
bir `log_softmax` uyguluyordu ve bütün hizalayıcı skorlarını tam yarıya
bölüyordu; gerçek değerler 0,80 ve 0,96. Damgalar ve korelasyon
etkilenmedi. Ayrıntı ve kanıt aşağıda, "Tam koşu öncesi denetim"
kaydında; skorun `word_confidence` kaynağı olup olamayacağı yeniden
açık.]

**3. Müzik eşiği kör dinlemeyle −30 → −40 dB** (politika v2). 34 klip,
beş dB bandından 6'şar + ayrıştırılmamış 4 kontrol, kanal ve dB gizli.
Sonuç: −40 dB altındaki 10 klipte 9 "yok" 1 "hafif"; **−40…−33 bandında
6/6 "belirgin"**; −33'ün üstünde karışık ama çoğunluk belirgin/baskın.
"Belirgin/baskın"ı ayıran en az hatalı eşik −40 dB (34'te 7 hata; −30'da
13). İlk tahmin olan −30 dB, kulağın açıkça duyduğu müziği kabul ediyordu.
Karşı örnekler öğretici: −29,6 / −26,6 / −22,0 / −21,6 dB'de dört klip
"yok" — üçü Seslendiriyor ve anahtarca; ayrıştırıcı oda tonunu ya da
efekti eşliğe yazmış olabilir, AudioSet skoru bunlardan ikisinde düşük
(0,17, 0,36). Yani dB tek başına yeterli değil; ileride "dB yüksek ama
AudioSet düşük" durumu ayrı incelenmeli. Etki (24 kaynaklık örneklem):
`background_music` %7,4 → %11,4; Peri_Mia %63 → %91, anahtarca %23 → %34,
Seslendiriyor %8 → %18. Peri_Mia için bu, kanalın karakteridir: masal
anlatımının altında sürekli müzik.

**4. Boilerplate:** örtüşen ifadeler birleşiyor, `max_words` 24, eşik
kanal kayıt sayısının %40'ı (en az 2). Noktayla başlayan kısaltma
parçaları ("P .O .Y .M.") birleşiyor. 24 kaynaklık örneklemde henüz yeniden
koşulmadı.

**Yol üstünde bulunan hata.** Sınır iyileştirme tek kelimelik bir klipte
("En", damgası yanlış) başı bitişinin ötesine çekip −0,01 s'lik klip
üretti, sıfır örnekli FLAC clip_qc'yi düşürdü. Düzeltildi: sınır klibin
kendi bitişini geçemez, gerekirse önceki klip kısalır; clip_qc okunamayan
dosyayı `unreadable_audio` ile işaretler, koşuyu düşürmez.

**Açık politika sorusu — kısa klipler.** Hizalayıcı zamanlarıyla `short`
işareti %3,1 → %5,7 (154 klip): gerçek boşluklar Whisper'ınkinden büyük
olduğu için kısa cümleler ("Haydi oku.", "Yola düşer.") 1,2 s'den uzun
duraklarla ayrı kalıyor. 154'ün 87'si 1,5–2,5 s arasında ve metin olarak
bütün cümleler. `segment.min_sec: 2.5` bunları önerilen alt kümeden
düşürüyor; 1,5'e inmek 5 dakikalık örnekte ~90 klibi geri kazandırır.
Kullanıcı kararı.

**Kör dinleme, hizalayıcı turu** yayında: 5 kanaldan 5'er önerilen klip
(25). Sonuç bekleniyor.

**Makaleye:** §Hat (ölçek), §Yöntem (hizalama ve sınır), §Kalite ölçümleri
(müzik eşiği ve dinleme protokolü), §Ablasyon (Whisper vs hizalayıcı damga
kayması).

## 2026-08-29 — Kısa klip kararı ve hizalayıcı dinleme turu

**Karar:** `segment.min_sec` 2,5 → 1,5 (kullanıcı). Beş kaynaklık örnekte
`short` 154 → 56 klip (%5,7 → %2,0), önerilen alt küme %83,1 → %86,9
(2.405 klip, 4,01 saat); süre p5 2,4 s. Yol üstünde bir açık kapandı:
aşamaların "bitti" sürümü artık konfig bölümünün özetini de içeriyor,
yani bir eşik değişince ilgili aşama kendiliğinden yenileniyor — daha önce
yalnızca kod sürümüne bakıyordu ve `min_sec` değişikliği yeniden koşuyu
tetiklemiyordu.

**Kör dinleme, hizalayıcı turu:** hizalanmış zamanlarla kesilmiş 25 önerilen
klip (5 kanal × 5), **25/25 temiz** — kırık başlangıç 0, kırık bitiş 0,
kesik hece 0 (`work/sample-5b/listen/answers-1.json`). Beş turun toplamı:
kiraat'ın 129 önerilen klibinde kırık başlangıç 0, kesik hece yalnızca
ikinci turun 3'ü (sınır iyileştirmesinden önce).

**Makaleye:** §Yöntem (süre politikası), §Değerlendirme (dinleme turları
özet tablosu).

---

## 2026-08-29 — vLLM Whisper sunucusu ASR'nin yerini tutar mı? (hız evet, metin hayır)

Soru: makinede ayakta duran iki vLLM Whisper konteyneri (`whisper-vllm`,
vLLM 0.11.0, large-v3-turbo, 8000; `whisper-vllm-ts`, vLLM 0.27.1,
large-v3, 8001) hattın in-process faster-whisper ASR'sinden hızlı mı ve
onun yerine geçebilir mi? Deney: `src00001`'in ilk 20 dakikası 16 kHz mono
40×30 s parçaya bölündü, iki sunucuya eşzamanlı istekle gönderildi,
metin `work/sample-5b/asr/src00001.jsonl` (faster-whisper toplu, VAD'lı)
ile jiwer üzerinden karşılaştırıldı. GPU ölçüm sırasında paylaşımlıydı.

Hız: 8001 tek istekte 57×, 8 eşzamanlıda 138×, 16'da 163× gerçek zaman
(`verbose_json` ile 148×); 8000 (turbo) 16'da 218×. Faster-whisper toplu
modu 0,77 dk/saat ≈ 78× idi, yani vLLM ASR'yi yaklaşık iki kat
hızlandırır. Ama ASR toplam sürenin 1,95 dk/saat içinde 0,77'si; ASR'nin
tamamen yok sayılması bile hattı en çok 1,65× hızlandırır, vLLM'in
sağladığı gerçek kazanç 1,95 → ~1,6 dk/saat (tam korpus 4 → ~3,3 gün).

Metin: faster-whisper 1.829 kelimeye karşı 8001 1.568, 8000 1.684 kelime
üretti. WER 8001 için 0,186 (sil 285, yer 31, ekle 24), 8000 için 0,134
(sil 177). Hata neredeyse tamamen **silme**: 40 parçanın 5'inde vLLM
42–47 kelimelik parçaya 3–4 kelime yazıp durdu ("Altyazı M.K.", "İsa yine
dedi,", "Allah'a emanet olun."), yani klasik erken-bitiş/altyazı
halüsinasyonu. Dün tek klipte görülen "7 s'de kesip son cümleyi atladı"
kusurunun sayıya vurulmuş hâli. Sebep vLLM'in VAD'siz sabit 30 s
parçalama yolu ve `verbose_json`'da bile ne `condition_on_previous_text`
ne de VAD denetimi olması. Bu kayıp bölütlemeye doğrudan cümle kaybı
olarak yansır; iki kat hız için ödenecek bedel değil.

Ayrıca vLLM 0.27.1 kelime damgası vermiyor (`words: null`; segment
damgası var, 70 s'de 33 ifade parçası). Açık PR vllm#47664 (çapraz dikkat +
DTW, `--enable-word-timestamps`) bunu ekliyor ama 29 Ağu itibarıyla
birleşmemiş, bakımcı incelemesi görmemiş ve `needs-rebase`; belgesi de
"eğitim verisi hizalaması için zorlamalı hizalayıcının yerine geçmez"
diyor. Hat kelime damgasını zaten MMS_FA'dan aldığı için PR bir ön koşul
değil; asıl engel yukarıdaki silme oranı.

Karar: ASR in-process faster-whisper'da kalır. vLLM yolu ancak silme
oranı VAD'lı parçalama (istemci tarafında VAD bölgelerini gönderip
sunucuda yalnızca çözme) ile faster-whisper düzeyine inerse yeniden
ölçülür; o zaman da kazanç ASR'de 2× ve hatta ~1,2× ile sınırlı.

## 2026-08-29 — Boş GPU'da yeniden koşu: konteynerler süreyi etkilememiş, hat belirlenimci

Dünkü 1,95 dk/saat ölçümü GPU'yu iki boşta Whisper konteyneriyle (~9 GB
VRAM) paylaşırken alınmıştı; "konteynerleri kapatınca hızlanır" varsayımı
sınandı. İki konteyner durduruldu, aynı beş kaynak aynı ayarlarla temiz
dizinde (`work/sample-5c`) baştan koşuldu. Sonuç **1,92 dk/saat**: ASR
0,76, müzik 0,30, hizalama 0,29, bölütleme 0,22, prepare 0,19, clip_qc
0,15 (tam korpus ≈ 3,9 gün). Yani boşta duran konteynerler yalnızca
bellek tutuyormuş, hesaplamayı yavaşlatmamış; varsayım yanlıştı ve
"kapat da hızlansın" önerisi geri alınıyor. ASR ~79× gerçek zamanda
GPU'ya bağlı; kalan aşamalar arasında hâlâ örtüştürme yapılmıyor, en
büyük hız payı orada (ASR+align ≈ 1,05 dk/saat GPU, geri kalan ~0,87
CPU/ffmpeg).

Belirlenimcilik: 5c'nin manifestosu 5b ile karşılaştırıldı — 2.769 klipte
2.769 aynı sınır (±1 ms) ve 2.769 aynı metin. Aynı girdi ve konfigle hat
aynı çıktıyı üretiyor; tam koşuda kaynak tekrarı güvenle yapılabilir.

Ayrıca 5b'nin ilk koşusu clip_qc'de bir klibi okuyamayıp çökmüştü
(`00332.flac`, "Format not recognised"); `clip_qc` o gece okunamayan klibi
`unreadable_audio` bayrağıyla geçecek şekilde düzeltildi ve 5c'de tekrar
etmedi. Test paketi: 87 test, tümü geçiyor.

## 2026-08-29 — Koşu tarayıcısı (`scripts/browse_ui.py`) ve politika düzeltmesi

Kalite takibi için kullanıcıya yönelik bir sayfa: `python scripts/browse_ui.py
--work work/sample-5c` durum deposunu salt-okunur açar (WAL; hat yazarken
okunabilir), aşama ilerlemesini 10 s'de bir yeniler, klipleri tarayıcıda
çalar (FLAC doğrudan; kaynak wav'ından "bağlam" düğmesiyle klibin 2 s
öncesi–sonrası) ve transcript'le birlikte bütün ölçümleri, işaretleri ve
`recommended`/`exclusion_reasons` alanlarını gösterir. Varsayılan görünüm
önerilen alt kümeden tohumlu rastgele örnektir (tohum sayfada durur,
"aynı örnek" ile tekrarlanır); süzgeçler öneri durumu, dışlanma sebebi,
işaret, kanal, süre, metin araması ve her ölçüm için `metrik op değer`
koşulları ("müzikli > −40 dB", "kelime güveni < 0,6" gibi hazır
kategoriler). Sayfadaki iyi/kusurlu/kötü kararları ve notlar
`<work>/manual-notes.jsonl`'a eklenir, `--dump-notes` ile özetlenir. Bu
kör dinleme aracı değildir (o `listen_ui.py`); amaç nihai veriden
rastgele dinleyerek kaliteyi izlemek.

Sayfa ilk açılışta bir tutarsızlığı görünür kıldı: `src00003-00001`
(−32,3 dB müzik) "önerilen" görünüyordu. Sebep: 28 Ağu'daki v2 kararında
`music.inaudible_db` −40'a çekilmiş ama `recommended_subset` kuralındaki
`music_to_speech_db max` −30'da kalmıştı; `background_music` işareti
−40'ta yanıp politika −30'da eliyordu. Kural −40'a düzeltildi (konfig
yorumu), `export` 5c'de yeniden koşuldu: önerilen 2.405 → 2.404, müzik
sebebiyle dışlanan 1 → 2 (`src00003-00000` −21,3 dB, `src00003-00001`
−32,3 dB; ikisi de kanalın açılış jeneriği). Politika sürümü "2" olarak
kalıyor — karar aynı, uygulaması eksikti.

## 2026-08-29 — Sütun şeması tek kaynakta; yayımlanmayan ölçümlerin envanteri; `word_confidence` kuralının anatomisi

**Şema.** Yayımlanan sütunların tür/birim/üreten aşama/açıklama bilgisi
`kiraat/schema.py`'ye kondu; makaledeki sütun tablosu ve veri kartı
`python -m kiraat schema` çıktısından üretilecek, elle yazılmayacak.
`python -m kiraat schema --check <clips.jsonl>` bir manifestoyu şemayla
karşılaştırır; `tests/test_schema.py` export'un sabit anahtarlarını,
clip_qc ölçümlerini ve (varsa) `work/sample-5c` manifestosunu şemaya
karşı sınar. 5c: eksik/fazla sütun yok. Yerel sütunlar (`audio`,
`source_id`, `source_path`) tabloda gizlenir; yayımda `source_path`
herkese açık kaynak kimliğine dönüşecek. Eksik bulunan bir sütun şemaya
eklendi: `music_stem_db` (ayrıştırıcı koşan kliplerde dört bileşenin
seviyesi; 5c'de 2 klip).

**Yayımlanmayan ölçümler (envanter).** Hat, manifestoya girmeyen şunları
da üretiyor: (a) *kelime düzeyinde* zaman damgası ve olasılık
(`asr/srcN.jsonl`: text/start/end/prob) ve hizalayıcının kelime başına
`align_start/align_end/align_score`'u (`align/srcN.jsonl`) — TTS ve ASR
için en değerli ek; klip başına `word_span` ile kesilip `words` sütunu
olarak yayımlanabilir; (b) kaynak düzeyinde `language_prob` (Whisper dil
olasılığı), `container_duration` (kesik kaynak tespiti), `n_words`,
`n_aligned` (hizalanan kelime oranı), `align_score_median`,
`asr_model`/`asr_batch_size`; (c) klip `meta.snapped` — sınır iyileştirme
klibin başını/sonunu komşuya yaslamışsa (`snapped_start/end`); (d) kanal
başına madenlenen boilerplate ifadeleri (`boilerplate/<kanal>.json`);
(e) VAD bölgeleri (yalnızca ASR'ye girdi, saklanmıyor). Karar bekleyen
soru: (a)'nın `words` sütunu olarak, (b)'nin kaynak tablosu olarak
yayımlanması; ikisi de makale için "ne sunuyoruz" bölümüne girer.

**`word_confidence<0.6` dışlaması.** 5c'de 188 klip (%6,8) yalnızca bu
kuralla dışlanıyor; kullanıcı dinlediğinde kliplerin iyi olduğunu gördü.
Anatomi: kural klipteki *en düşük* Whisper kelime olasılığı; dışlanan
kliplerde ortalama güven medyanı 0,94 (tutulanlarda 0,99), yani tek kelime
düşürüyor. O kelime 149 klipte cümle ortasında; 37'sinde büyük harfli
(özel isim: Zo, Agop, Vladimir, Efendi), 45'inde ≤2 harf (he, o, ne, aa),
10'unda sayı, çoğu ünlem/ağız/işlev kelimesi. Hizalayıcı asgari skoru
dışlananlarda 0,37, tutulanlarda 0,41 — bağımsız sinyal kusur görmüyor.
Whisper olasılığı ses kalitesini değil dil modelinin sürprizini ölçüyor;
tek-kelime asgarisiyle kapı olması nadir isim ve konuşma dili içeren,
korpus için değerli klipleri eliyor. Karar verilmedi; seçenekler kuralı
kaldırmak ya da yalnızca gerçek transcript hatasını yakalayan çok düşük
bir eşiğe (~0,3) çekmek. Koşulacak deneyler listesine eklendi.

## 2026-08-29 — Yöntem belgesi: `docs/FEATURES.md`

Makalenin yöntem bölümü için her özelliğin ne olduğu, hangi model ve
parametreyle, hangi formülle hesaplandığı ve hangi sütuna yazıldığı tek
belgede toplandı: `docs/FEATURES.md` (13 bölüm: kaynak hazırlama, VAD, ASR,
zorlamalı hizalama, bölütleme ve sınır iyileştirme, metin alanları, klip
ölçümleri, müzik, kalıp metin, yineleme, politika, yayımlanmayan ve henüz
üretilmeyen özellikler). Parametreler `configs/default.yaml`'dan, formüller
koddan, sayılar yalnızca bu depodaki ölçümlerden (5 kayıtlık örnek, 28 Ağu
kör dinleme) alındı; önceki yayına ya da veri kümesine atıf yok. Kısa
tanımlar `kiraat/schema.py`'de kalır; iki belge birbirini tekrar etmez,
şema tabloyu, FEATURES anlatıyı verir. Sütun ya da parametre değiştiğinde
üçü birden güncellenir: konfig, şema, FEATURES.

## 2026-08-29 — Sütun doğrulaması: üç hata bulundu ve düzeltildi; bilgi içeriği analizi

`scripts/verify_columns.py` yazıldı: bir koşunun her sütununu bağımsız
yoldan yeniden hesaplayıp manifest ve DB ile karşılaştırır (40 denetim: şema,
kimlik/sıra/süre, ses dosyası biçimi ve süresi, 300 rastgele klipte
tepe/RMS/kırpılmanın yeniden hesabı, metin değişmezleri, ölçüm aralıkları
ve iç tutarlılık, kelime güveni ve hizalama skorunun kelime dosyalarından
yeniden hesabı, komşu boşlukları, işaret↔ölçüm, politikanın konfigden
yeniden hesabı, DB↔manifest). 5c'de 38 denetim geçti, ikisi bulgu verdi.

**Bulgu 1 — son klip kaynak sonunu aşıyor.** `src00003-00188`: `end`
1165,46 s, kaynak 1165,27 s; FLAC 5,333 s ama `duration` 5,523. Nefes payı
kaydın sonunu aşınca kesim sessizce kırpıyor, sütun aşan değeri taşıyordu.
Düzeltme: `segment.clamp_to_audio`, bölütleme aşaması sürüm 4→5, birim
testi. Etkisi kayıt başına en çok bir klip.

**Bulgu 2 — sınırlayıcı seviyeyi yükseltiyordu (gerçek hata).** Doğrulama
5c'de 166 klipte `clip_ratio>0` ve 210 klipte tepe ≥ −0,5 dBFS gösterdi;
oysa `prepare` −1 dBFS tavan uyguluyor. Sebep ffmpeg `alimiter`'ın
varsayılan `level=true` seçeneği: sınırlayıcı çıkışı otomatik tam ölçeğe
yükseltiyor. Ölçüm (src00001, 2 dk): ham tepe −7,59 dBFS, `limit=0.8913`
ile −6,34 (+1,25 dB kazanç), `level=false` ile −7,34. Hazırlanmış src00004
0,00 dBFS'e çıkmış ve kırpılmıştı. Yani "doğal seviye korunur" iddiası o
ana kadar yanlıştı ve `rms_dbfs`/`peak_dbfs`/`clip_ratio` sütunları
kaynağın değil sınırlayıcının seviyesini ölçüyordu. Düzeltme:
`alimiter=limit=…:level=false`, `prepare` sürüm 2→3 (bütün hat yeniden
koşar), test. Bu hata 5c ve önceki bütün örnek koşularının seviye
sütunlarını geçersiz kılar; 5c yeniden koşulacak.

**Bulgu 3 — VAD damgaları 0,1 s'ye yuvarlı.** `leading_silence_sec` yalnızca
14 tekil değer (0,0: 1.303 klip, 0,1: 1.403), `internal_silence_sec` 0,1
basamaklı; sebep Silero'nun `return_seconds=True` yuvarlaması.
`internal_silence_sec>1.0` kuralı bu çözünürlükte çalışıyordu. Düzeltme:
örnek indeksinden ms çözünürlük, `clip_qc` sürüm 1→2.

**Bilgi içeriği (5c, 2.769 klip).** `text_raw` kliplerin %99,7'sinde `text`
ile aynı (fark yalnızca "..." → "."), `text_spoken` %96,5'inde aynı; üç alan
da tasarım gereği kalıyor ama makalede bu oranlar verilmeli. Sabit sütunlar:
`confidence_source` (asr), `policy_version` (2), `source_sample_rate`
(44100 — bu örnekte); `duplicate_of` hep boş (tek kayıtlı kanallar),
`music_stem_db` %99,9 boş (2 klip), `music_prob_external` hiç yok. Bağımsız
bilgi taşıyanlar: kelime güveni ile hizalama skoru ortalamaları arasında
korelasyon yalnızca 0,26; `leading_silence` ile `lead_gap` −0,08 (biri VAD,
diğeri ASR damgası — farklı şeyler). `speech_ratio`, sessizlik sütunlarından
neredeyse türetilebilir (korelasyon 0,95) ama VAD'ın iç boşluk toplamını
taşıdığı için tutulur. Aday gereksiz: `music_stem_db` (sözlük tipli, %0,1
dolu, `music_to_speech_db` zaten ondan türetilmiş) — yayımdan düşülmesi
öneriliyor; karar bekliyor.

Doğrulama betiğinde değişmez düzeltmesi: küçük harfle başlayan 36 klibin
hepsi `forced_split` parçasıydı (iç noktalamadan bölünen cümlenin ikinci
yarısı) ve hiçbiri önerilmiyor; denetim bu parçaları muaf tutar ve ayrıca
"bölünmüş küçük harfli parça önerilmiyor" diye sınar.

Ara ölçek koşusu (`work/sample-15`: tohum 7, 5 kanal × 3 kayıt) üç
düzeltmeyle baştan başlatıldı; doğrulama ona uygulanacak.

## 2026-08-29 — Müzik işareti: HDemucs dB'nin kanala bağlı yanlış pozitifleri; AIGenLab modelleri yeniden ölçüldü

Kullanıcı sample-15'te (19 kaynak öncesi 15 kaynak, 8.700 klip) müzik
işaretli kliplerin bir kısmında müzik olmadığını duydu. Sayım: 106 klipte
ayrıştırıcı koştu, 74'ü `background_music` (dB > −40) aldı; işaretlilerin
41'i tek kanaldan (`MuratKaraOfficial2021`), 14 cantadakitap, 10 dinleyiniz,
9 eba. Şüpheli kanalın kliplerinde dB −3…−40 iken AudioSet skoru 0,05–0,13:
ayrıştırıcı ile AST çelişiyor. Yorum: HDemucs müzik üzerinde eğitildiği
için konuşma kaydındaki oda tınısı/gürültü tabanını "diğer" bileşenine
atıyor; dB oranı tek başına o kanalda müzik değil tını ölçüyor. 28 Ağu kör
dinlemesi (34 klip, 5 kaynak) bu tür bir kanal içermiyordu — eşik doğru,
sinyal eksik.

Üç AIGenLab modeli (yerelde önbellekli) üç kümede koşuldu — işaretli 74,
ayrıştırılmış-işaretsiz 32, rastgele temiz 60 (AudioSet < 0,05, ayrıştırıcı
hiç koşmamış):

| model | işaretli 74 (>0,5) | ayrışmış-işaretsiz 32 | temiz 60 |
|---|---|---|---|
| `speech-music-classifier-v3` (whisper-small) | 59 | 28 | **39** (medyan 0,925) |
| `whisper-small-speech-music-classifier` | v3 ile birebir aynı çıktılar | | |
| `AST-speech-music-classifier` | 36 | 2 | **0** (medyan 0,007) |

v3, müziksiz konuşmanın üçte ikisine "müzik" diyor; konuşma/müzik ayrımı
yapan, arka plan sorusunu yanıtlamayan bir model — 28 Ağu bulgusuyla
tutarlı, kullanılamaz. AST varyantı ise temiz kümede sıfır, işaretlilerde
HDemucs'la tam şüpheli kanalda çelişiyor: ikinci koşul adayı.

Aday kural (politika v3): `background_music` = `music_to_speech_db > −40`
**ve** AST kanıtı (`music_score_audioset ≥ t` ya da AIGenLab-AST ≥ 0,5).
Kural dinleme denetiminden geçmeden konmaz: sayfa sample-15'e çevrildi,
kullanıcı `background_music` süzgeciyle 74 klibi dinleyip "iyi = müzik
yok, kötü = müzik var" diye işaretleyecek; sonuca göre eşik ve ikinci
sinyal seçilir, `music` aşamasına `music_prob_external` sütunu
(AIGenLab-AST) eklenir.

## 2026-08-29 — Müzik kuralı v3 (dB VE AudioSet) ve sınır iyileştirmenin ilk heceyi kesmesi

**Müzik.** Kullanıcı sample-15'te `MuratKaraOfficial2021` kanalının 41
işaretli klibinin hepsini dinledi: müzik yok. Bu kanalda dB −3…−40 iken
AudioSet skoru medyan 0,10 / p90 0,20; diğer dört kanalın 33 işaretli
klibinde AudioSet medyan 0,53 (p10 0,08). AIGenLab-AST aynı ayrımı
veriyor (medyan 0,07'ye 0,98) ama tek başına daha gürültülü (0,5 eşiğinde
MuratKara'da 7 yanlış pozitif kalıyor, AudioSet 0,3'te 3). Eşik taraması:
AudioSet ≥ 0,3 koşulu yanlış pozitiflerin 38/41'ini düşürüyor, diğer
kanallardaki işaretlerin 28/33'ünü tutuyor; iki modelin VE'si 3/28, VEYA'sı
7/29 — AudioSet tek başına yeterli ve belgelenmiş bir model olduğu için
kural o. Uygulama: `has_background_music(db, threshold, audioset,
audioset_min=0.3)`; politika v3'te dB metrik kuralı yerine `background_music`
işareti `flag_absent` listesine girdi (iki sütunun VE'si politika
dilinde ifade edilemiyor). AIGenLab-AST `music_prob_external` sütunu olarak
yayımlanır, kural değildir. **Geçici:** MuratKara'da kalan 3 yanlış pozitif
kayıt açılışları (`src00015-00000`, `src00010-00000`, `src00005-00000`;
AudioSet 0,56–0,78) — jenerik olabilir; ve diğer kanallardaki 33 klip
henüz dinlenmedi (özellikle AudioSet < 0,1 olan 5 `dinleyiniz` klibi
muhtemelen aynı türden yanlış pozitif). Dinleme bitince eşik kesinleşir.

Yan bulgu: AIGenLab-AST, ayrıştırıcının hiç koşmadığı 8.594 klibin 81'ine
"müzik" diyor; bunlar medyan 2,5 s'lik tek ünlem/kısa cümle klipleri
("Derilin!", "Güle güle.") ve üçü 0,1 s'lik boş klip — model kısa girdide
güvenilmez, "kaçırılan müzik" değil.

**Sınır iyileştirme hatası.** Üç boş klibin izini sürerken çıktı: `1.`
kelimesi 3186,70–3187,06'da, klip 3187,16–3187,31 — klip kendi kelimesini
içermiyor. Sayım (klip başlangıcı ilk kelimenin hizalayıcı başlangıcından
>50 ms sonra): sample-15'te **219/8.700 (%2,5)**, 5c'de 30/2.769 (%1,1);
gecikme 0,5–0,6 s'de yığılıyor. Sebep: komşu damgalar arası boşluk dar
olduğunda sessizlik bulunamazsa "en sessiz an" pencerenin uzak kenarına
(t_end + 0,60 s) düşüyor ve sonraki klibin başı ilk kelimenin içine
giriyordu; koruma yalnızca klibin sıfır süreli olmamasıydı. Düzeltme:
sınır sonraki klibin ilk kelimesinin (hizalayıcı) başlangıcını geçemez
(`refine_boundaries`, test eklendi), bölütleme sürüm 6. Doğrulama betiğine
"klip kendi kelimelerini kapsıyor" denetimi eklendi. sample-15 bölütlemeden
itibaren yeniden koşuluyor; klip kimlikleri değişmez (kesim noktaları
aynı, yalnızca sınırlar), dinleme notları geçerli kalır.

Ayrıca: `1.`/`3.` gibi tek başına sıra sayısı belirteci ("… sıralayabiliriz.
1. Naip, …") ayrı cümle sayılıp 0,1 s'lik klip oluyor; `short` işaretiyle
dışarıda kalıyor ama cümle bölücüde "sayı + nokta + büyük harf" kuralı
için bir istisna gerekebilir — açık madde.

## 2026-08-29 — Dış sınıflandırıcı kaldırıldı; gürültü ölçümü adayları

Kullanıcı kararı: AIGenLab modelleri kullanılmayacak. Model kartındaki
kullanımla (`pipeline`) son ölçüm — v3/whisper-small, kullanıcının
dinleyip müziksiz bulduğu 41 klibin 34'üne (klip) / 39'una (30 s bağlam)
"müzik", 60 rastgele temiz klibin 39'una "müzik"; AST varyantı 41'de 7/3,
temizde 0/60, yani AudioSet skoruyla aynı bilgi. `music.external_model`
null'a döndü, `music_prob_external` şemadan ve sayfadan çıktı.
`background_music` kuralı dB VE AudioSet ≥ 0,3 olarak kalıyor (v3).

Arka plan gürültüsü için adaylar (müzikten ayrı soru): torchaudio SQUIM
(referanssız STOI/PESQ/SI-SDR; 41 müziksiz klipte SI-SDR medyan 24,0 dB,
rastgele temizde 25,9, diğer kanalların işaretlilerinde 20,9), DNSMOS
P.835 (BAK; `dnsmos_ovrl` sütunu planlanıyor — aşama yazılana kadar konfigde
yeri yok, 30 Ağu 2026), pyannote/brouhaha (SNR +
C50; kapılı model). Karar bekliyor: `quality` aşaması olarak sütun, kapı
değil.

## 2026-08-29 — Sınır düzeltmesi sonrası sayım: 219 → 76; kalanlar dinlemeye

sample-15 bölütleme sürüm 7 ile yeniden koşuldu (kimlikler değişmedi).
"Klip başlangıcı ilk kelimenin hizalayıcı başlangıcından >50 ms sonra"
sayımı **219 → 76** (%2,5 → %0,87); "bitiş son kelimeden önce" 3 → 5.
Kalan 76'nın gecikmesi 0,5 s'de yığılıyor (37 klip): sessizlik bulunmuş ve
damgada başlıyor ama arama penceresinin uzak kenarına kadar sürüyor, sınır
pencere kenarına konuyor. İlk harfe göre ihlal oranı: '1' %16 (9/56 —
sayı belirteçlerinin hizalanması güvenilmez), 'b' %1,9 (26/1.405 —
patlamalı ünsüzün kapanma sessizliği), diğerleri ≤%1,2. Kulak olmadan
karar verilemiyor: bu 76 klibin kimlikleri
`work/sample-15/listen-cut-start.json`'a yazıldı, sayfaya "klip
kimlikleri" süzgeci eklendi; kullanıcı dinleyip "ilk hece kesik mi" diye
işaretleyecek.

Bitişi kelimeden önce olan 5 klip için sebep hizalayıcı damgalarının
çakışması (sonraki kelime öncekinin bitişinden önce "başlıyor"); sınır
artık çakışma aralığının ortasına konuyor (test eklendi), bölütleme
sürüm 8 — sample-15'e bir sonraki koşuda uygulanır.

## 2026-08-29 — Sütun doğrulaması sample-15: depo yeniden koşuda hayalet anahtar bırakıyordu

sample-15 (8.700 klip, müzik kuralı v3 ile) tam doğrulamadan geçirildi;
40 denetimin 32'si geçti, 8'i bulgu verdi. Gerçek hata bir tane: dış model
kapatılıp müzik aşaması yeniden koştuğu hâlde `music_prob_external`
manifestoda duruyordu. Sebep `Store.merge_clip_results`'ın ölçümleri
`dict.update` ile, işaretleri birleşimle katması: yeniden koşan aşamanın
artık üretmediği sütun ya da vermediği işaret silinmiyordu (müzik işareti
kuralı değişseydi eski işaretler de kalacaktı; bu koşuda bölütleme yeniden
koştuğu için maskelendi). Düzeltme: her klip aşaması `produces_metrics`
ve `produces_flags` bildirir; depo bunları önce siler, sonra yeni çıktıyı
katar; başka aşamanın alanlarına dokunmaz (test eklendi; clip_qc ve
music bildirdi, music sürüm 2).

Diğer yedi bulgu denetimin kendi kabullerindendi ve denetim düzeltildi:
müzik işareti artık dB VE AudioSet ile sınanıyor; konuşma bulunmayan
klipte baş=son=süre tanım gereği (3 klip); eleme eşiğinde yuvarlama
toleransı; `music_to_speech_db` stem güçlerinin toplamından faz farkı
kadar sapıyor (eşlik dalga toplamının RMS'i; ±3 dB tolerans); klip kendi
kelimelerini kapsıyor denetimi 76+5 (bilinen, dinlemeye). Bir metin
normalizasyon boşluğu görünür oldu: harf+rakam belirteçleri ("MI6", "M5",
"HTS") okunuşa çevrilmiyor; 414 sayılı klibin 3'ü. Açık madde.

Müzik sonucu (v3 kuralı): `background_music` 74 → **31** (cantadakitap 14,
eba 9, dinleyiniz 5, MuratKara 3); önerilen 7.387 → 7.425.

sample-15 bölütleme sürüm 8 (çakışan damga düzeltmesi) + clip_qc + music
(hayalet anahtar temizliği) ile yeniden koşuyor; doğrulama ona tekrar
uygulanacak.

## 2026-08-29 — sample-15 (16,95 saat, 5 kanal × 3 kayıt) sonuçları

Bütün düzeltmelerle (sınırlayıcı `level=false`, VAD ms çözünürlük, son klip
kelepçesi, sınır iyileştirme v8, müzik kuralı v3, hayalet anahtar temizliği)
üretilmiş son hâl: 8.700 klip, 15,98 saat (%94 verim), önerilen 7.425
(%85,3). Süre: p10 3,5 / p50 6,2 / p90 10,4 s. İlk tam koşunun aşama süreleri
(GPU paylaşımsız): ASR 0,82, hizalama 0,29, müzik 0,29, bölütleme 0,23,
clip_qc 0,19, prepare 0,18 → **2,01 dk/saat** (tam korpus ≈ 4,1 gün); 5c
ile tutarlı.

| kanal | klip | öneri % | kel. güven <0,6 | forced | oversize | müzik | RMS p50 |
|---|---|---|---|---|---|---|---|
| MuratKaraOfficial2021 | 800 | 88,5 | 7,8 % | 14 | 1 | 3 | −22,4 |
| cantadakitap | 306 | 88,9 | 5,6 % | 2 | 0 | 14 | −16,3 |
| dinleyiniz | 5.959 | 82,7 | 8,4 % | 492 | 75 | 5 | −23,7 |
| eba | 1.359 | 94,0 | 3,7 % | 16 | 3 | 9 | −25,6 |
| seslimakalem | 276 | 87,7 | 6,5 % | 15 | 1 | 0 | −16,0 |

Okumalar. (1) Dışlamanın baskın sebebi yine `word_confidence<0.6` (646 klip,
%7,4) — 7. maddedeki dinleme denetimi bekliyor. (2) `dinleyiniz` uzun
cümleli (492 forced_split, 75 oversize): dini vaaz/ders üslubu; bölme
kuralları burada sınanmış oldu, klipler kaybolmadı, işaretle ayrıldı.
(3) Yineleme: 3 kayıtlı kanallarda kelimesi kelimesine tekrar yalnızca
"3." belirteçleri (2 klip); künye/anons yinelemesi yok, çünkü —
(4) **kalıp metin madenciliği hiçbir kanalda ifade bulamadı** ve bu
doğru bir sonuç değil, yöntemin sınırı: cantadakitap her kaydı
"<yazar>'ın <kitap> adlı kitabından" / "… dinlediniz" ile açıp kapıyor,
seslimakalem her kaydı "<yazar>, <gazete>" ile bitiriyor, eba bir kayıtta
"Yazan … Seslendiren …" künyesi taşıyor; bunlar kelimesi kelimesine değil
**şablon** hâlinde tekrar ediyor (değişken yazar/kitap adı), 3+ kelimelik
sabit n-gram vermiyor. Açık madde: şablon madenciliği (sabit iskelet +
değişken yuva) ya da künye sözlüğü ("adlı kitabından", "seslendiren",
"yazan", "dinlediniz") ile cümle düzeyinde işaret. (5) Seviye:
sınırlayıcı düzeltmesinden sonra tepe ≥ −1 dBFS olan 501 klip var ama
dağılım p50 −0,94 / p90 −0,85 dBFS, kırpılma 3 klipte ve tek örnek
düzeyinde: sınırlayıcı 44,1 kHz'de uygulanıp sonra 24 kHz'e indirildiği
için örnekler-arası taşma ≤ ~0,2 dB — kabul edilebilir, belgelendi.
(6) Kanal çeşitliliği: `dinleyiniz` tek başına saatlerin %71'i;
`max_hours_per_channel: 120` tavanı tam koşuda bunu dengeler, örnek
koşuda dengelemez.

> **Geçersiz (30 Ağu 2026):** o tavan hiçbir zaman uygulanmadı — anahtarı
> okuyan kod yoktu — ve kullanıcı kararıyla konfigden çıkarıldı (veri
> azaltılmaz). Kanal dengesizliği tavanla değil, `channel` + `duration`
> sütunlarıyla yayımlanıyor.

Sınır sayımı (v8): başlangıcı ilk kelimeden sonra 78 (%0,9), bitişi son
kelimeden önce 5 — v7 ile aynı düzeyde; kalanlar dinlemede.

Tam sütun doğrulaması (43 denetim, 400 rastgele klipte ses yeniden
hesabı): **41 geçti**; kalan ikisi bilinen açık işler — klip kendi
kelimelerini kapsıyor (83 klip, dinleme bekliyor) ve stem güç toplamı ile
dalga toplamı arasındaki faz farkı (2 klipte 3–4 dB; denetim bilgiye
çevrildi). Hayalet `music_prob_external` yok, müzik işareti kuralla
birebir, politika v3 yeniden hesapla birebir, DB = manifest.

Ardından 20 saat bütçesi: aynı dizine `--max-hours 20` ile 4 kaynak
eklendi (toplam 19 kaynak, ≈24,4 saat; bütçe alt sınır). Yalnızca yeni
kaynaklar işleniyor.

## 2026-08-29 — Örneklemler silindi; 27 kanalın tamamını kapsayan 25 saatlik denetim örneklemi ve kanal kanal manuel denetim aracı

Önceki bütün örnek koşular (`sample-5b`, `sample-5c`, `sample-15`,
`sample-24` ve kök `work/` altındaki ilk uçtan uca koşu; 17 GB) silindi.
Karar kanıtı olan küçük dosyalar — dinleme anahtarları ve cevapları
(`listen*/key.json`, `answers-*.json`), `manual-notes.jsonl`, dinleme
alt küme listeleri ve koşu logları — `work/archive/<örneklem>/` altına
alındı (23 dosya, 296 KB). `probe_segment` ve `probe_boilerplate` dinleme
turlarının anahtarlarını taşıdığı için yerinde bırakıldı. Sebep: şimdiye
kadarki örneklemler 5 kanalla sınırlıydı ve `dinleyiniz` saatlerin
%70'ini alıyordu; kanal kanal kusur envanteri için bütün kanalların eşit
temsil edildiği tek bir örneklem gerekiyor.

**Örneklem tanımı.** İki yeni sınır eklendi: `runtime.max_sources_per_channel`
(kanal başına kayıt sayısı) ve `prepare.max_minutes` (kayıt başına dakika
tavanı; prepare yalnızca ilk bu kadar dakikayı çözer, `ffmpeg -t`; saat
bütçesi kesilmiş süreyle sayılır, kesik-indirme işareti tavana göre değil
tavanla kapsayıcının küçüğüne göre verilir; prepare v4, `cap_sec` meta).
Tavan gerekliydi çünkü kanalların medyan kaydı 0,2 ile 2,2 saat arasında
değişiyor (o gün dışarıdan okunmuştu; 30 Ağu 2026'da bu depoda ölçüldü —
kayıt süresi medyanı 41,4 dk, kanal medyanları envanter raporunda): tam
kayıt alınsaydı "kanal başına 3
kayıt" 121 saat ederdi, kanal başına saat bütçesiyle kısa kayıtlar
seçilseydi örneklem kısa kayıtlara doğru eğilirdi. Tavan bu eğilimi
kaldırır: kayıt seçimi rastgele kalır, yalnızca uzun kayıtların ilk 20
dakikası işlenir. Bedeli, kesilen kayıtlarda kapanış künyesinin
görülmemesi — boilerplate madenciliği açılış künyesini yine görür.

`python -m kiraat run --dry-run` ile seçim koşmadan görüldü (yeni bayrak):
tohum 2026, **27 kanal × 3 kayıt = 81 kaynak, ≤20 dk/kayıt; sayılan
24,70 saat** (ham 121,2 saat). 12 kanalda üç kayıt da 20 dk'dan uzun
(1,00 saat), en küçüğü `eba` 0,49 ve `cantadakitap` 0,55 saat (kısa
kayıtlı kanallar). Koşu `work/sample-25`, 13:31'de başladı:
`--max-sources 0 --max-sources-per-channel 3 --max-minutes 20
--sample-seed 2026`. Prepare 81 kaynak 6 dakikada bitti.

**Manuel denetim aracı.** `scripts/browse_ui.py` kanal odaklı bir denetim
aracına çevrildi (eski serbest süzgeçler "Keşif" sekmesinde duruyor):

- *Denetim sekmesi:* soldaki kanal listesi kanal başına kayıt/saat/klip,
  önerilen oranı, hat ilerlemesi ve denetim ilerlemesini gösterir. Kanal
  seçilince kanal için sabit bir **deste** çekilir — varsayılan 20 klip,
  kanalın üç kaydına dönüşümlü dağıtılmış, tohumlu; `review-decks.json`
  dosyasında kalıcı olduğu için koşu ilerleyip yeni klip gelse de aynı
  klipler gösterilir. Havuz seçilebilir (önerilen alt küme / bütün klipler
  / dışlananlar; manifest henüz yoksa bütün klipler).
- *Klip başına karar:* temiz / kusurlu / kullanılmaz (1/2/3) ve on kusur
  etiketi — baş kesik, son kesik, metin hatalı, okunuş hatalı, müzik,
  gürültü/yankı, yapay ses, künye/anons, başka konuşmacı, diğer — tek harfle
  açılıp kapanır; etiket koyup karar vermeyince "kusurlu" varsayılır. Karar
  verilince sıradaki karar verilmemiş klibe geçilir ve çalınır. Ölçümler
  katlanır bölümde; transcript büyük yazı.
- *Bulgular sekmesi:* kanal × karar/etiket tablosu, kusurlu/kullanılmaz
  kliplerin listesi (kanal ve etikete göre süzülür, kimliğe tıklayınca
  Keşif'te açılır), CSV indirme. Aynı tablo terminalde `--dump-notes`,
  dosyaya `--csv`.
- Not kaydı şeması: `{ts, clip_id, channel, verdict, tags, note}`; eski
  iyi/kusur/kötü kayıtları okunurken yeni adlara çevrilir.

Sayfa headless Chromium ile açılıp üç sekme denetlendi, JS hatası yok;
klip kartları bölütleme bitince sınanacak. Bu tur kör dinleme değildir —
kanal ve ölçümler görünür — amacı kanal başına kusur envanteri çıkarmak ve
hangi sinyallerin kör dinlemeye alınacağını belirlemektir.

## 2026-08-29 — sample-25 sonuçları: 27 kanal, 12.958 klip, 22,4 saat; hız 27×

> **Eskidi (31 Ağu 2026):** bu koşu silindi ve düzeltilmiş hatla yeniden
> koşuldu; buradaki klip sayıları ile önerilen oranı yalnızca o günün
> hattını anlatır. Geçerli örnek koşu `sample-25c`'dir (13.637 klip,
> önerilen %82,8, politika v6).


Koşu 13:31–14:26, **54 dakikada 24,7 saat ses ≈ 27× gerçek zaman**
(sample-5b'de 31× ölçülmüştü; fark müzik aşamasının payı — bu örneklemde
müzikli klip oranı yüksek). Aşama süreleri: prepare 5 dk (~290×), ASR
21 dk (~71×), hizalama 7 dk, bölütleme 6 dk, clip_qc 5 dk, müzik 11 dk.
> **Düzeltme (31 Ağu 2026):** bu satırda tam korpus süresi olarak
> dışarıdan alınmış bir sayı kullanılmıştı. Ölçülen korpus **3.440,2
> saat** (30 Ağu 2026 envanteri) ve ölçülen hız 41,5× — beklenen tam koşu
> **~83 saat**.

**Klipler:** 12.958 klip / 22,42 saat (ses saatinin %91'i klip oldu),
medyan 5,9 s, p5 2,6 / p95 11,6 s. Önerilen alt küme (politika v3)
10.121 klip (%78,1), 17,07 saat. Dışlanma sebepleri: `background_music`
1.251 (+ birleşik 100 kadar), `word_confidence<0.6` 974, `forced_split`
421, `short` 125, `internal_silence>1 s` 59, `oversize` 38. Küçük harfle
başlayan 243 klibin 242'si forced/gap split ya da künye parçası
(tasarım gereği, hepsi dışlanmış); **bir** önerilen klip küçük harfle
başlıyor (`src00001-00000`, kaydın ilk cümlesi — Whisper kaydın ilk
kelimesini büyük harfe çevirmemiş; sınır değil metin kusuru, açık madde).

**Kanal başına** (klip, önerilen %, müzik işareti %): Peri_Mia 539 / %18 /
%80; SESLİKİTAPEVİ 455 / %49 / %38; sess-Seslikitap 608 / %53 / %40;
Pandoramedyaseslikitap %69 / %19; SesliKitaPodcast %70 / %20; kitaplar
%72 / %22; anahtarca %76 / %16; kalan 20 kanal %77–91, müzik ≤%6.
Müzik işareti kanala göre keskin ayrışıyor: üç kanal (Peri_Mia,
SESLİKİTAPEVİ, sess-Seslikitap) fon müziği ile okuyor. `word_confidence`
kuralı 974 klip (%7,5) düşürüyor — kural hâlâ dinleme denetimi bekliyor
(madde 7); bu tur o klipleri de içerecek.

**Künye madenciliği (3 kayıt/kanal, min 2):** 27 kanalın 7'sinde ifade
bulundu: `seslendiren <ad>` üç kanalda (kitaplar, SESLİKİTAPEVİ, ses-arşiv),
kanal açılış/kapanış anonsları (SesliKitaPodcast 5 ifade, Peri_Mia,
seslikitapturkish, bizimkütüphane). 20 kanalda 0 ifade — şablon künye
sorunu (madde 10) sürüyor; `boilerplate` işaretli klip 31.

**Kaynaklar:** 81/81 hatasız. Bilinen kesik `bizimkütüphane` dosyası
(src00058, kapsayıcı 210 dk, ses 19,4 dk) 20 dk tavanın %97'sini
verdiği için `truncated_source` işareti almadı — tavan kesik-indirme
tespitini maskeliyor; ses sağlam olduğu için sorun değil ama tam koşuda
(tavan 0) işaret yine düşer. ffmpeg bu dosyada "partial file" uyarısı
bastı, çıktı sağlam. En kısa kaynak BirDinle src00057: 25 s, 4 klip.

**Sütun doğrulaması (43 denetim):** ilk koşuda 5 FAIL; üçü denetleyicinin
kusuruydu ve düzeltildi — `truncated_source` denetimi 20 dk tavanını
bilmiyordu (63/81 yanlış alarm; artık min(kapsayıcı, tavan)), `M.Ö.` gibi
harf kısaltmaları "düz metin" sayılıyordu (`text_spoken` "milattan önce"
doğruydu), `duplicate_of` karşılaştırması noktalama farkını sayıyordu
(dedupe anahtarıyla karşılaştırılıyor), künye klipleri cümle sınırı
denetiminden dışlanmamıştı. Yeniden koşu: **41 geçti, 2 FAIL**, ikisi de
gerçek:

1. *Küçük harfle başlayan 4 klip* (12.408 içinde): `src00001-00000` kaydın
   ilk cümlesi — Whisper kaydın ilk kelimesini büyük harfe çevirmemiş
   (önerilen alt kümede, tek klip); diğer üçü künye kesiminin artığı —
   "Merhaba değerli dinleyicilerimiz, sizlerle …" cümlesinde künye ifadesi
   virgüle kadar kesilince kalan "sizlerle …" parçası küçük harfle
   başlayan ayrı klip oluyor (üçü de müzik işaretiyle zaten dışlanmış).
   Açık madde 11: künye sonrası kalan cümle parçasına `forced_split`
   benzeri işaret; kayıt başı büyük harf.
2. *Klip ilk kelimesini kapsamıyor: 180 klip (%1,4)*, hepsi
   `snapped_start`. Kalıp tek: klip başı, hizalayıcının ilk kelime
   başlangıcından tam **0,46 s** sonra (112/181), ASR damgasından 0,64 s
   sonra. Sınır iyileştirme, damganın hemen ardında (≤0,10 s içinde
   başlayan) ~0,7 s'lik bir enerji sessizliği buluyor ve sınırı sessizliğin
   sonuna koyuyor; `silence_after_word_sec` kuralı sessizliğin başına
   baktığı için tetiklenmiyor. İki açıklama var: ya Whisper ve hizalayıcı
   duraklardan sonraki ilk kelimeyi 0,5–0,7 s erken damgalıyor (28 Ağu
   üçüncü dinleme turunda enerji tabanlı sınır 28/28 temizdi, bu yönde) ya
   da ilk hece gerçekten kesiliyor. Karar kulağın: 181 klip
   `work/sample-25/listen-cut-start.txt` dosyasında; Keşif sekmesindeki
   "hazır liste" seçicisi (`listen-*.txt` dosyalarını okur) listeyi tek
   seçimle açıyor. Sonuca göre ya kural değişir (sessizliğin sonu damgayı
   0,3 s'den fazla geçemez gibi) ya da denetim ölçütü hizalayıcı damgasından
   sese taşınır.

Manuel denetim: `python scripts/browse_ui.py --work work/sample-25`
sayfası açık; manifest hazır olduğundan kanal desteleri artık kalıcı
çekiliyor (önerilen alt küme havuzu). Beklenen: 27 kanal × 20 klip = 540
karar + 181 kliplik sınır listesi (baş kesik / temiz).

## 2026-08-29 — Dağıtıcı: CPU ve GPU işleri üst üste; sıralı koşuyla özdeş çıktı, 27× → 44×

Hat bu sabaha kadar tek süreçte, aşama aşama ve her aşamada kaynak kaynak
sıralı koşuyordu: ffmpeg çözerken GPU boş bekliyor, ASR sırasında CPU boş
bekliyordu. Sample-25'in sıralı koşusu (81 kaynak, 24,69 saat) 54,7 dk
sürdü: ASR 20,7 dk, müzik 10,9, hizalama 7,1, bölütleme 5,8, prepare 5,2,
clip_qc 5,0. Sorulan soru şuydu: birbirinden bağımsız CPU ve GPU işlerini
paralel koşturmak süreyi kısaltır ama doğruluğa zarar verir mi?

Kodu okuyunca cevap "doğru kurulursa hayır" çıktı ve "doğru"nun üç şartı
belirlendi. Kaynak aşamaları (prepare → asr → align → segment) yalnızca
kendi kaynağının önceki çıktısına bakıyor; klip aşamaları klip başına
bağımsız. Tek istisna künye madenciliği: `boilerplate` kanal düzeyinde
çalışıyor ve kanalın **bütün** kayıtlarının ASR çıktısını okuyor; bir
kaynağın bölütlemesi kanalın diğer kayıtları bitmeden başlarsa madenlenen
ifade kümesi o an hangi kaydın bitmiş olduğuna, yani zamanlamaya bağlı
olurdu. Bu yüzden (1) kanal bariyeri: `segment(s)`, kanalın seçili bütün
kayıtlarının ASR'si bitene ya da hataya düşene kadar hazır olmaz.
(2) Tek yazıcı: işçiler yalnızca sonuç döndürür, sqlite'a ana süreç yazar
ve 'bitti' kaydını yazımdan sonra düşer. (3) İş içi hesap sıralı kodla
aynıdır: aşama nesneleri aynı `process_source` / `process_clips` yolunu
koşar, paketleme yalnızca hangi klibin hangi işçide ölçüleceğini
değiştirir; dolgulu toplu çıkarım yoktur (HDemucs'a klipleri dolguyla
batch hâlinde vermek kenarlarda stem enerjisini değiştirirdi, yapılmadı).

Uygulama `kiraat/scheduler.py`: ana süreç bağımlılık çizgesini kurar, iki
süreç havuzuna dağıtır — CPU havuzu (`runtime.source_workers`, 6: prepare,
segment, clip_qc) ve GPU havuzu (`runtime.gpu_stage_concurrency`: asr,
align, music; her işçi bütün GPU modellerini bir kez yükler). Bir kaynağın
bölütlemesi biter bitmez klipleri clip_qc ve müzik paketlerine bölünüp
kuyruğa girer; GPU kuyruğunda öncelik asr > align > music, çünkü ASR alt
akışı besler, müzik yalnızca kendini. Müzik aşamasında ayrıca ön-yükleme
eklendi: çözme, 16 kHz yeniden örnekleme ve AST log-mel öznitelikleri CPU
işidir ve GPU ölçerken boş bekliyordu; artık iş parçacıkları sonraki
klipleri hazırlıyor (`MusicMeasurer.prepare` / `measure_prepared`; `measure`
API'si aynı). `done` tablosu ve sürüm kontrolü değişmedi, yeniden koşu
aynen kaldığı yerden sürer. Sıralı yol `--serial` ile duruyor. Manifestoda
işaret ve ölçüm sütunlarının sırası aşamaların bitiş sırasına bağlıydı
(dağıtıcıda müzik clip_qc'den önce bitebiliyor); export artık ikisini de
sıralı yazıyor. `configs/default.yaml`'daki hiç okunmayan `lease_sec` ve
`max_job_attempts` anahtarları kaldırıldı.

Testler (`tests/test_scheduler.py`, sahte aşamalarla, gerçek spawn
havuzlarında): sıralı ve paralel koşu bayt bayt aynı manifestoyu üretir;
hiçbir bölütleme kanalının bütün ASR'leri bitmeden başlamaz; bozuk kaynak
`error` alır, ASR'ye gitmez ve bariyeri tıkamaz; yeniden koşu sıfır iş
yapar; klip işi hatası koşuyu durdurur (sıralı kodla aynı). 106 test
geçiyor, 1 atlanıyor.

**Deney 1 (özdeşlik, küçük):** 3 kanal × 2 kayıt × ≤20 dk = 1,92 saat ses
(`scripts/exp_parallel.sh`, tohum 2026). Aynı örneklem sıralı, paralel
(gpu 1) ve paralel (gpu 2) koşuldu; `scripts/compare_manifests.py` 856 klibi
her sütunda karşılaştırdı: **üçü özdeş**. Süre 263 → 237 → 169 s; küçük
örneklemde model yükleme payı büyük, hız sayısı buradan alınmaz.

**Deney 2 (özdeşlik + hız, sample-25):** aynı 81 kaynak paralel modda
(`--gpu-workers 2`, 6 CPU işçi) temiz dizine (`work/sample-25-par`)
yeniden koşuldu. 12.958 klip, sabah sıralı koşuyla **her sütunda özdeş**
(işaret listeleri küme olarak; sıraları farklıydı). Süre 14:38:29 →
15:12:26 = **34,0 dk**, sıralı 54,7 dk'ya karşı 1,61×; hız **27× → 44×
gerçek zaman**. Zaman çizgisi: prepare 2,1 dk'da bitti (sıralıda 5,2;
tamamı ASR'nin altına gömüldü), ASR 17,6 dk'da (iki GPU işçisi), hizalama
+ bölütleme + clip_qc birlikte 15:04'te, müzik 15:03–15:12. Koşu artık
GPU'ya bağlı: ASR ≈ 18 + hizalama ≈ 6 + müzik ≈ 9 dk ≈ 33 dk, duvar saati
34 dk. Bundan sonrası CPU örtüştürmeyle değil GPU işini azaltmakla gelir
(müzik ayrıştırıcı eleği, ASR toplu boyutu); bunlar ölçüm değiştirebilecek
kararlardır, ayrıca ele alınır. İki GPU işçisi bütün modellerle 21,6 GB
VRAM tuttu (RTX 3090, 24 GB); üçüncü işçi sığmaz.

Tam korpus tahmini: ~3.100 saat / 44× ≈ 70 saat ≈ 3 gün (sıralıda ≈ 115
saat). Tam koşu yine örneklem doğrulanıp açık onay gelmeden başlatılmayacak.

## 2026-08-29 — Denetim aracının yüzü sadeleştirildi

Kullanıcı sample-25 denetim sayfasını "çorba gibi" buldu ve eski kör
dinleme sayfasının (`scripts/listen_ui.py`) daha anlaşılır olduğunu söyledi.
Bakınca haklıydı: her klip kartı karar düğmelerini, on kusur etiketini ve not
alanını ayrı ayrı tekrarlıyordu; 20 kartlık deste alt alta bir düğme duvarı
oluyordu. Üstte sekiz aşama çipi, açık duran uzun kılavuz ve kanal
satırlarındaki üç ayrı çubuk da göz gürültüsüydü.

Yapılan: karar/kusur/not denetimleri kartlardan çıkarıldı, yalnızca seçili
klip için alttaki sabit çubukta (oynatıcının hemen altında) tek kopya
duruyor; kartlar eski sayfadaki gibi yalnızca numara, ses, metin (serif) ve
katlanmış ölçümler taşıyor, verilen karar kartın sağ üstünde rozet olarak
görünüyor. Aşama çipleri "koşu durumu" katlanır kutusuna, kılavuz kısaltılıp
varsayılan kapalıya, deste ayarları ve Keşif süzgeçleri katlanır bölümlere
alındı; kanal satırı ad + ilerleme + klip sayısına indi. Klavye kısayolları
ve API değişmedi; sunucu şablonu her istekte okuduğu için yeniden
başlatılmadı. Headless Chromium ile üç sekme denetlendi, konsol hatası yok.

## 2026-08-29 — Denetim sayfası sıfırdan yazıldı: her sütun süzülebilir

Kullanıcının isteği açıktı: sayfa, ölçütlere göre kolayca süzülüp elle
sınanabilir olmalı ve klip kartında görünen her ölçüm — kelime güveni,
hizalama skoru, müzik/konuşma dB, konuşma oranı, iç ve baş/son sessizlik,
komşu boşluklar, RMS, tepe, kırpılma — bir süzgeç seçeneği olmalı. Eski
sayfada süzgeç, elle yazılan birkaç metin koşuluyla sınırlıydı ve ölçümlerin
çoğuna hiç dokunulamıyordu; arayüz de üst üste yamandığı için dağınıktı.

Sunucu tarafında süzgeç tek bir motora çevrildi. `base_rows` bütün klipleri
bir kez çözüp bellekte tutuyor (anahtar: depo damgaları + klip sayısı, yani
hat yazdıkça tazeleniyor), `field` bir klibin herhangi bir sütunundaki değeri
veriyor, `op_match` tek bir süzgeç satırını uyguluyor. `/api/columns` süzülebilen
sütunları depodan okuyarak döndürüyor: klip alanları, metin alanları ve türevleri,
manifestten gelen öneri/dışlanma sebebi/politika sürümü, manuel karar ile kusur
etiketleri, ve bütün ölçümler. Ölçümün türü tek klipten kestirilemediği için
(ilk klipte null olabiliyor) boş olmayan bütün değerlere bakılıp en sık tür
seçiliyor; iç içe ölçümler `music_stem_db.vocals` gibi ayrı sütunlara açılıyor.
sample-25'te 46 sütun çıkıyor. Sıralama da artık her sütunda çalışıyor.
İki uç daha eklendi: `/api/stats` süzgeçten geçen havuzun karnesini (kaç klip,
kaç saat, kaça karar verilmiş, karar dağılımı, en sık etiket/sebep/işaret/kanal)
ve istenirse bir ölçümün dağılımını (yüzdelikler + histogram kovaları, her
kovanın altında ve üstünde kaç klip kaldığıyla) veriyor; `/api/presets` ölçüt
kümesini `<work>/review-filters.json` dosyasına adla kaydediyor.

Arayüz sıfırdan yazıldı (`scripts/review_template.html`; eski
`browse_template.html` artık sunulmuyor). Solda ölçüt kurucu: her satır
[sütun][işleç][değer], satırlar VE ile birleşiyor, işleç listesi sütunun
türüne göre değişiyor (sayıda eşik, metinde içerir/eşittir/düzenli ifade,
listede içinde var/yok, mantıksalda doğru/yanlış, hepsinde boş/dolu) ve
değerin bilinen seçenekleri açılır listeden geliyor. Ortada klipler üç kipte:
tohumlu rastgele örnek, herhangi bir sütuna göre sıralı liste (eşiğin iki ucunu
görmek için), kanal başına kalıcı deste. Seçili klibin bütün ölçümleri rozet
olarak görünüyor ve rozete tıklamak o sütunda süzgeç satırı açıyor — istenen
"her ölçüm bir süzgeç seçeneği" bağı burada kuruluyor. Sağda karne ve eşik
yardımcısı; histogram kovasının soluna tıklamak `<`, sağına tıklamak `>`
koşulu kuruyor, yüzdelik rozetleri de koşula dönüşüyor. Kovaların yüksekliği
karekök ölçekli, çünkü müziksiz kliplerin tamamı −80 dB kovasında toplanıp
ötekileri yassıltıyordu. Altta klavyeyle karar çubuğu duruyor; kör mod metni,
kimliği, ölçümleri ve öneriyi gizliyor, karar yalnızca sesle veriliyor (`r`
ile açılıyor). Ölçüt adres çubuğuna yazılıyor, yani bir sınama bağlantıyla
paylaşılabiliyor.

Karar hâlâ hiçbir klibi elemiyor: sayfa yalnızca ölçüm üretiyor, eleme
konfigdeki sürümlü `recommended_subset` politikasının işi. Headless Chromium
ile denendi: metin süzgeci (`text içerir "çünkü"`) 12.958 klipten 215'ini,
üstüne `word_confidence<0.6` eklenince 13'ünü bırakıyor; kanal destesi, kör
mod ve Bulgular görünümü çalışıyor, konsol hatası yok.

## 2026-08-29 — Tam koşu öncesi denetim: hizalayıcı skoru yarıya bölünmüştü, ara ses FLAC'a çevrildi

Tam korpus koşusu istenince önce sample-25'in deposu ve manifestosu baştan
sona incelendi. Doğrulayıcının bildiği iki FAIL dışında yeni bir kod hatası
çıktı ve tam koşunun diske sığmadığı görüldü; ikisi de koşudan önce
düzeltildi.

**1. `align_score` tam yarıya bölünüyordu (`stages/align.py`).** Aşama
emisyona bir kez daha `torch.log_softmax` uyguluyordu. MMS_FA çıktısı zaten
log-olasılık; `get_model(with_star=True)` sonuna 0 değerli, yani olasılığı
1,0 olan ve kasıtlı olarak normalize edilmemiş bir `<star>` sütunu ekliyor.
Model doğrudan koşturulup ölçüldü: `em.exp().sum(-1)` her karede tam 2,0.
Yeniden normalize edilince star tam 0,5'e oturuyor, gerçek belirteçlerin
hepsi yarıya iniyor. Verideki izi buydu — `align_score_mean` 12.938 klibin
11.362'sinde 0,5 kovasında, mutlak tavan 0,5, medyan 0,48.

Kayma her karede tekdüze (−log 2) olduğu için Viterbi yolu değişmez. Bu
önce üç gerçek parçada doğrulandı (CTC yolu ve kelime damgaları bit bazında
aynı, skorlar tam 2,0000 kat), sonra uçtan uca: aynı üç kaynak eski ve yeni
kodla ayrı work-root'larda koşuldu, 99 klibin **`align_score_min/mean`
dışındaki her sütunu özdeş**, skor oranı 1,9946–2,0028 (fark yalnızca dört
haneye yuvarlama). Yani bölütleme, kesim sınırları, `text_raw`,
`word_confidence`, müzik ve clip_qc ölçümleri hiç etkilenmemiş; yanlış olan
tek şey yayımlanan skor sütunuydu.

Bunun bedeli ölçümden büyük. 28 Ağu kaydı (yukarıda, "Zorlamalı hizalama
bağlandı") skoru "klip başına asgari medyan 0,40, ortalama 0,48" diye
yazmış; gerçek değerler 0,80 ve 0,96. Düşüklük `confidence_source: asr`
kararının gerekçelerinden biri olmuştu ve koşulacak deney 3 (hizalama
güveni geçerlemesi) bu yanlış tabandan planlanmıştı. **Her iki sayı da
yeniden koşulmalı**; hizalayıcı skorunun `word_confidence` kaynağı olup
olamayacağı sorusu yeniden açıktır.

`AlignStage.version` 1 → 2. Doğrulayıcıya sınıf düzeyinde bir muhafız
eklendi: korpus genelinde en yüksek `align_score_mean` 0,9'u geçmeli. Hata
hiçbir aralık denetimine takılmıyordu, çünkü 0,48 de [0,1] içindedir; yeni
denetim eski koşuda FAIL (azami 0,4990), yenisinde PASS (0,9990) veriyor.

**2. Ara ses WAV yerine FLAC (`stages/prepare.py`).** Tam korpusun ölçüsü
alındı: 2.695 dosya, 27 kanal; 80 dosyalık ffprobe örnekleminde kayıt
ortalaması 47 dk, tahmini toplam **~2.100 saat**. sample-25 24,69 saatte
5,94 GB üretti (ara ses 3,97 + klipler 1,97), yani 0,241 GB/saat; tam koşu
~510 GB demek ve diskte 585 GB boş var. Yükün büyüğü ara ses: 24 kHz mono
PCM16 tek başına ~366 GB ve `work/audio/srcNNNNN.wav` hiçbir yerde
silinmiyor.

Silme yerine kayıpsız sıkıştırma seçildi, çünkü silmek bir tuzak kuruyor:
`prepare` 'bitti' kalırken kaynak sesi kaybolduğu için sonraki bir aşama
sürümü (tam da bu turda `align` v2 gibi) yeniden koşulamaz hâle gelirdi.
FLAC ile ~366 GB → ~160 GB, toplam beklenti ~326 GB.

`-sample_fmt s16` zorunlu çıktı ve bunu ölçüm gösterdi: ffmpeg'in FLAC
kodlayıcısı varsayılan olarak s32/24 bit seçiyor, o zaman hem dosya
küçülmüyor (WAV'ın %93'ü) hem de örnekler PCM16 yolundakiyle **aynı
olmuyor** — sessiz bir veri değişikliği olurdu. s16 ile hem `soundfile` hem
`faster_whisper.audio.decode_audio` iki dosyadan bit bazında aynı örnekleri
okuyor; gerçek koşuda ara ses WAV'ın %52'si (4 dk kayıtlar), tam kayıtlarda
%47–49. `PrepareStage.version` 4 → 5.

**3. Politikadan boşa çalışan DNSMOS kuralı kaldırıldı (v3 → v4).**
`dnsmos_ovrl min 3.0` kuralı `allow_missing: true` taşıyordu ve DNSMOS
aşaması bağlı olmadığı için sütun hiç üretilmiyordu: kural 12.958 klibin
hepsinde sessizce geçiyordu. Politika "DNSMOS ≥ 3,0 uygulandı" gibi
okunuyor ama hiçbir klibi etkilemiyordu. Kural yoruma alındı; hiçbir klibin
`recommended` değeri değişmez. `tests/test_config.py` artık politikadaki her
ölçüm kuralının şemada karşılığı olmasını şart koşuyor — bu sınıf hata bir
daha sessizce giremez. Konfigdeki `dnsmos`, `speaker` ve `events`
bölümlerinin başına "bağlanmadı" notu düşüldü (30 Ağu 2026'da bu bölümler
konfigden büsbütün çıkarıldı: not düşmek yetmiyordu, `dnsmos.enabled: true`
hâlâ "açık" görünüyordu); `speaker` yokluğunda dışa
aktarımın kanala düşmesi, yani "aynı metin + farklı ses korunur" kuralının
fiilen "farklı kanal korunur" olarak çalıştığı da oraya yazıldı
(sample-25'te 28 yinelemenin hepsi kanal içiydi, zarar yok).

**Denetimde temiz çıkanlar.** 43 denetimin 41'i geçiyordu ve bilinen iki
FAIL (180 klip ilk kelimesini kapsamıyor, 4 klip küçük harfle başlıyor)
zaten açık madde. Ek olarak bakıldı ve sorun bulunmadı: 12.958 klibin
hepsinin ses dosyası var, 300'lük örneklemde istisnasız 24 kHz mono FLAC ve
süreler ±10 ms içinde; ASR halüsinasyonu yok (ardışık kelime tekrarı sıfır);
künye/abone/altyazı cümlelerinin hepsi önerilen alt kümenin dışında (tek
istisna 6,5 s'lik "İzlediğiniz için teşekkürler."); kaynak hatası 0.
Doğrulayıcıya ikinci bir denetim daha eklendi: `oversize` işareti paylar
eklenmeden verildiği için 38 klip 15,0–15,4 s aralığında işaretsiz kalıp
önerilen alt kümeye giriyor — bu tasarım gereği, ama artık bilgi olarak
raporlanıyor ve pay aşılırsa FAIL veriyor.

**Tam koşu beklentisi.** ~2.100 saat, dağıtıcı 41,5× gerçek zamanda gitti
(sample-25-par: 33,9 dk / 23,5 saat) → **~51 saat**. Doğrulama koşuları
`work/fixcheck` (yeni kod) ve `work/fixcheck-old` (eski kod) altında duruyor.


## 2026-08-30 — sample-25 silindi; aynı örneklem düzeltilmiş hatla yeniden: `sample-25b`

> **Eskidi (31 Ağu 2026):** `sample-25b` de silindi. Bu kayıttaki 12.958
> klip / önerilen %78,1 sayıları tepe sınırlayıcı kalkmadan ve politika
> v5–v6 düzeltmeleri yapılmadan önceki hattındır. Geçerli sayılar aşağıdaki
> `sample-25c` kaydındadır.


Dün akşamki düzeltmelerden (dağıtıcı, hizalayıcı skoru — align v2, ara
ses FLAC — prepare v5, politika v4, yeni denetim sayfası) sonra bütün
örnek çıktılar silindi: `sample-25`, `sample-25-par`, `exp-par`
(sıralı/paralel özdeşlik deneyi), `fixcheck*`. Karar kanıtı olan küçük
dosyalar — `manual-notes.jsonl`, `review-decks.json`,
`listen-cut-start.txt`, koşu logları, `exp-par/times.txt` —
`work/archive/sample-25/` altında.

Yeni koşu `work/sample-25b`: **aynı örneklem tanımı ve aynı tohum (2026)**,
yani aynı 81 kaynak (27 kanal × 3 kayıt, ≤20 dk; sayılan 24,70 saat,
`--dry-run` ile doğrulandı). Tohum bilerek değiştirilmedi: bölütleme kodu
değişmediği için klip kimlikleri ve sınırlar dünkü koşuyla birebir aynı
olmalı, yalnızca `align_score_*` (v2, iki katı) ve `policy_version` (4)
değişmeli — bu, düzeltmelerin etkisini doğrudan karşılaştırmayı sağlar
(`scripts/compare_manifests.py` arşivdeki manifest yok; sayılar defterdeki
dünkü kayıtla karşılaştırılır: 12.958 klip, önerilen 10.121). Dağıtıcı
varsayılan (`runtime.parallel: true`), 09:59'da başladı; denetim sayfası
`python scripts/browse_ui.py --work work/sample-25b` (8765) açık.

**Sonuç (10:39):** koşu 09:59–10:39, **39 dakikada 24,7 saat ≈ 38×**
(dünkü sıralı koşu 54 dk / 27×; dağıtıcı deneyindeki 44× tek başına
GPU'yken ölçülmüştü, bu koşuda denetim sunucusu da aynı makinede). Çıktı
beklendiği gibi dünküyle birebir: **12.958 klip / 22,42 saat, önerilen
10.121 (%78,1) / 17,07 saat**, dışlanma sayıları aynı (müzik 1.251,
word_confidence 974, forced_split 421, short 125). Değişen tek şey
hizalayıcı skoru: `align_score_min` medyan 0,795, p10 0,453, p90 0,953;
0,5 kovasında 270 klip (dün 11.362). Sütun doğrulaması: dünkü iki FAIL
aynen (4 küçük harf → madde 11; 180 sınır klibi → `listen-cut-start.txt`
yeni dizine kopyalandı, kimlikler aynı), kalan denetimlerin hepsi geçti.
Örneklem denetime hazır.

## 2026-08-30 — Tam koşu öncesi kod incelemesi: sürüm zinciri, dağıtıcı eşitliği, tepe sınırlayıcı, kare adımı

83 saatlik tam koşu istenince önce hattın tamamı gözden geçirildi. Beş kusur
çıktı; hiçbiri koşuyu çökertmiyor, hepsi sessizce yanlış ya da boş sayı
üretiyordu. Hepsi düzeltildi ve her biri için hatayı yakalayan bir test
yazıldı; testlerin düzeltme öncesi kodda düştüğü tek tek doğrulandı.

**1. Aşama sürümü yukarı akışı taşımıyordu.** `stage_version` yalnızca
aşamanın kendi adını taşıyan konfig bölümünü özetliyordu. Sonuç ölçüldü:
`AlignStage.version` 1'den 2'ye çıkarıldığı hâlde (skorları yarıya bölen
hata) `align_score_min/mean` sütunlarını klibe yazan `segment`in sürümü
`8+0528b4a1` olarak kalıyordu — mevcut bir DB'nin kaydettiğiyle bayt bayt
aynı. Artımlı yeniden koşuda düzeltme manifestoya **hiç ulaşmıyordu**.

Aynı kökten ikinci bir örnek: `asr` ve `clip_qc` ikisi de `cfg.section("vad")`
okuyor ama `vad` ikisinin de özetinde yoktu. `vad.threshold` değişse hiçbir
şey yeniden koşmaz, `speech_ratio` ve üç sessizlik sütunu korpus boyunca iki
ayrı VAD ayarının karışımı olurdu — hiçbir yerde iz bırakmadan.

Sürüm artık özyinelemeli: kendi kod sürümü + tükettiği konfig bölümleri +
geçişli bağımlılıklarının sürüm dizgeleri. `Stage`e iki bildirim niteliği
eklendi — `config_sections` (kendi adı dışında okuduğu bölümler) ve
`version_ignore` (yalnızca başarım ayarları). Varsayılan bilinçli olarak
muhafazakâr: `config_sections` unutulursa hata geri gelir, `version_ignore`
unutulursa yalnızca fazladan yeniden koşu olur. `runtime` ve `paths` sürüme
girmesi yasak — işçi konfigi `runtime`ı değiştiriyor, sürüm süreçler arasında
kararsız olurdu. Künye madenciliği kayıtlı bir aşama sınıfı değildi ama
`segment` ona bağlı; `BoilerplateStage` (yeni `ChannelStage` alt sınıfı)
yalnızca sürüm ve bağımlılık defterine girmek için eklendi, yürütmesi yerinde
kaldı.

Ölçülen davranış: `align` kod sürümü değişince `align`, `segment`, `clip_qc`,
`music` eskiyor, `prepare` ve `asr` durur; `vad.threshold` değişince `asr` ve
altındaki her şey; `prepare.ffmpeg_threads` değişince hiçbir şey;
`align.confidence_source` değişince `segment` eskiyor ama `align` **durur** —
tercih değişikliği 3.400 saati yeniden hizalatmıyor. CLI'nin verdiği `20.0`
ile YAML'ın verdiği `20` aynı özeti üretsin diye sayılar tek biçime indiriliyor.

**2. Dağıtıcı ile sıralı yol aynı klip kümesini ölçmüyordu.** Sıralı
`run_clip_stage` `pending_clips`i kaynak süzgeci olmadan çağırıyor — depodaki
her bekleyen klibi ölçüyor. `Scheduler._build` ise klip işlerini yalnız
seçilmiş **ve hatasız** kaynaklardan kuruyordu. `export` her iki yolda da
bütün klipleri yazdığı için, klipleri üretildikten sonra hata alan bir
kaynağın klipleri ölçülmeden manifestoya girip `eksik_olcum:*` ile önerilen
alt kümeden sessizce düşüyordu. Aynı kök künyeyi de vuruyordu: kanal listesi
hata süzgecinden geçtiği için dağıtıcı künyeyi daha az kayıttan madenliyor,
farklı ifade kümesi farklı `boilerplate` işaretleri ve farklı klip metni
üretiyordu.

Doğru taraf sıralı yol: `export` bütün klipleri yazdığına göre depodaki her
klip ölçülmelidir. Dağıtıcı artık klip işlerini genel bekleyen kümeden kuruyor
(bu koşuda yeniden bölütlenecek kaynaklar hariç; onlar `_write_source`
üzerinden giriyor), kuyruk boşalınca bölütlemesi hataya düşenler için tek
seferlik bir geç tarama yapıyor, künyeyi de hata süzgeçsiz kanal listesinden
madenliyor. Dağıtıcı belgesine 4. kural eklendi: **kaynak işi seçime, klip işi
depoya bağlıdır.**

Bu, tam koşudan sonra `speaker` aşamasının bağlanabilmesinin de şartıydı:
düzeltme olmadan `--stages speaker export` hata almış kaynakların kliplerini
sessizce atlardı.

Mevcut testler bunu kaçırıyordu, çünkü `fake_stages`teki tek bozuk kaynak
`prepare`de düşüyor ve hiç klip üretmiyor. Üç yeni test yazıldı; üçü de
düzeltme öncesi kodda düşüyor, sonrasında geçiyor.

**3. Hizalama kare adımında 0 → +20 ms testere dişi sapma.** `align.py` kare
süresini `(len(audio)/sr)/T` diye hesaplıyordu. Model koşturulup ölçüldü:
gerçek evrişim adımı tam 20,000 ms, kodunki 20,013 ms (30 s parçada); sapma
parça sonunda tam +20 ms'ye ulaşıp her parça başında sıfırlanıyor — 10, 30 ve
60 s parçalarda aynı sonuç. Gürültü değil, kelimenin parça içindeki konumuyla
orantılı bir eğim. Adım artık `setup()` içinde iki ileri geçişle modelden
çözülüyor (`(L₂−L₁)/(T₂−T₁)/sr`), sabit sayı yok; ölçülen değer 0,020000 s.
`AlignStage.version` 3.

**4. Tepe sınırlayıcı kaldırıldı — ama ilk teşhis fazla güçlüydü, kaydı düzgün
duruyor.** `prepare` sesi `alimiter` ile −1 dBFS'e sınırlıyordu; `clip_qc` ise
tepeyi ve kırpılmayı bu sınırlanmış sesten kesilen klipte ölçüyor. İlk sınama
sentetikti — %57,5'i kırpılmış bir 24 kHz sinüs zincirden geçirildi, çıkışta
tepe tam −1,000 dBFS ve `clip_ratio` 0,000000 — ve buradan "sütun sıfırdan
başka değer alamaz" sonucu çıkarıldı. **Bu sonuç yanlıştı.** Sentetik girdi
zaten 24 kHz olduğu için yeniden örnekleme hiç koşmadı; gerçek kaynaklar
44,1 kHz ve ffmpeg yeniden örneklemeyi filtre zincirinden **sonra** yapıyor,
örnekler arası taşma sınırlanmış tepeleri tavanın üstüne geri çıkarıyor.
sample-25b'de (limitleyici açıkken) 12.958 klibin 2.058'i −1 dBFS'in
üstündeydi ve 3'ünde `clip_ratio > 0`.

Aynı üç kaynak üzerinde kontrollü karşılaştırma yapıldı:

| | limitleyicisiz | limitleyicili |
|---|---|---|
| `clip_ratio > 0` | 6 / 102 | 0 / 99 |
| tepe > −0,1 dBFS | 9 | 0 |
| tepe azami | −0,000 dBFS | −0,890 dBFS |
| RMS medyanı | −22,17 dBFS | −22,19 dBFS |

Yani sınırlayıcı kırpılma sinyalini gerçekten bastırıyor (6 → 0) ve `peak_dbfs`
kaynağın değil hattın tavanının ölçüsü oluyor; kaldırma kararı bu yüzden
doğru. Ama sütun "yapısal olarak sıfır" değildi, yalnızca bastırılmıştı.
Sınırlayıcı artık `peak_ceiling_db: null` ile varsayılan kapalı, isteğe bağlı
kaldı. `PrepareStage.version` 6.

**Bağımsız ve henüz açık ikinci sorun:** politikadaki `clip_ratio max: 0.002`
kuralı **hiçbir yapılandırmada tek bir klip elemedi** — sample-25b'de 0/12.958,
limitleyicisiz koşuda 0/102. Gözlenen azami `clip_ratio` 7×10⁻⁵, eşiğin yirmi
katı altında. Yani eşik ölçülen büyüklüğe göre fazla gevşek ve kural
sınırlayıcı kalksa bile ölü. Eşiğin nereye konacağı dinleme denetimi ister;
açık madde 12 olarak aşağıya eklendi.

**5. Doğrulayıcı ve şema.** Bir gün önce eklediğim iki denetimin kendi kusuru
düzeltildi: `oversize` toleransı 0,4 s diye sabit yazılmıştı (sample-25'teki
azami aşım 0,378 s'ydi — payın hemen altında; 140 kat daha çok klipte yanlış
FAIL verirdi), artık konfigden ve `RefineConfig`ten türetiliyor (15,0 + 1,0 s);
hizalama tavanı muhafızı skor hiç yokken `0/0` ile boş geçiyordu, artık
`align.enabled` açıkken skor yokluğu FAIL. Bir de sınıf denetimi eklendi:
politikada adı geçen her ölçüm korpusta değişkenlik göstermeli. Dürüstlük payı
— bu muhafız `dnsmos_ovrl`i yakalar ama sample-25b'de `clip_ratio`yu
**yakalamadı**, çünkü sütunun iki farklı değeri vardı (0 ve 10⁻⁵). Sabit
sütunu görür, "neredeyse sabit" sütunu görmez. `schema.py`de `duplicate_of`
açıklaması da düzeltildi: konuşmacı aşaması bağlı olmadığı için dışa aktarım
kanala düşüyor ve kural fiilen "aynı metin, farklı kanal korunur" biçiminde.

**Doğrulama.** 120 test geçiyor. Üç kaynaklık koşu paralel ve sıralı yolda
**özdeş** manifest üretti (102 klip). `verify_columns` 45 denetimin 44'ünü
geçti; tek FAIL bilinen açık madde (klip ilk kelimesini kapsamıyor, 1 klip,
dinleme kararı bekliyor). Koşu kaydına artık aşama sürümleri de düşüyor, yani
`run.log` neyin neyi eskittiğini gösteriyor.

**Sürüm dizgeleri (varsayılan konfig, tam koşuya girecek olanlar):**
`prepare=6+b8ead68c`, `asr=2+aa02a9c5`, `align=3+788cdd77`,
`boilerplate=1+7ff09cc9`, `segment=8+361135c3`, `clip_qc=2+1dba94f6`,
`music=2+3b18374a`. (Doğrulama koşusu `--max-minutes 4` ile yapıldığı için
onun kaydındaki dizgeler bunlardan farklıdır — tavan `prepare`in özetine
giriyor ve zincir üzerinden hepsini kaydırıyor. Sürüm zincirinin çalıştığının
yan kanıtı.)

**sample-25b** (bugün 09:59–10:38, düzeltmelerden önce, 81 kaynak / 12.958
klip / 25 saat) limitleyici açıkken ve eski kare adımıyla üretildi; içindeki
`peak_dbfs`, `clip_ratio` ve damga sütunları makaleye taşınmaz. Örnek koşu
düzeltmelerden sonra yeniden yapılacak.

## 2026-08-30 — Köken zinciri: bağımlılıklar, ağırlık revizyonları ve koşu kaydı

Çalışma bir yayına dönüşecek ve hattın kendisi artefakt olacak. Bu gözle
bakınca üç boşluk çıktı; üçü de tam koşudan önce kapatıldı, çünkü bir koşunun
kökeni koşudan sonra yeniden kurulamıyor.

**1. Bağımlılıklar beyan edilmemişti.** `requirements.txt` tek satırdı
(`pyyaml>=6.0`). Hattı çalıştıran her şey — torch, torchaudio, faster-whisper,
ctranslate2, transformers, soundfile, silero-vad, ctc-forced-aligner, numpy —
listede yoktu. Ortamdaki gerçek sürümler okunup tam sürümle sabitlendi
(aralık kullanılmadı: yukarı akıştaki bir yükseltme çıktıyı sessizce
değiştirir ve hata vermez). torch/torchaudio 2.5.1+cu124, faster-whisper
1.2.1, ctranslate2 4.8.1, transformers 4.49.0, silero-vad 6.2.1,
ctc-forced-aligner 1.0.2, soundfile 0.13.1, numpy 2.2.6, pyyaml 6.0.3.

**2. Model ağırlıkları sabitlenmemişti.** `WhisperModel("large-v3")`,
`from_pretrained("MIT/ast-...")` ve `load_silero_vad()` hepsi "o an güncel
olan" demekti. Depolardan biri ağırlıkları yeniden yüklerse bütün transcript'ler
ya da müzik skorları sessizce değişir. HF'den çekilen ikisi commit'e bağlandı:
ASR `edaa852ec7e145841d8ffdb056a99866b5f0a478`
(`Systran/faster-whisper-large-v3`), AudioSet
`f826b80d28226b62986cc218e5cec390b1096902`. `WhisperModel` `revision`
alıyor, `from_pretrained` da. torchaudio paketleri (MMS_FA, HDemucs) ve
silero-vad ağırlığı paket sürümüne bağlı olduğu için ayrı revizyon almıyor;
onları `requirements.txt` sabitliyor. `MusicStage` ayrıca AudioSet modelini
artık konfigden okuyor, dataclass varsayılanından değil (`music` v3).

**3. Manifest kökenini taşımıyordu.** İçinde `policy_version` vardı ama git
commit'i, aşama sürümleri, konfig ve ağırlık kimlikleri yoktu; yani
yayımlanan bir manifest onu üreten koda bağlanamıyordu — oysa makalenin
merkezî iddiası ölçümün karardan ayrılığı ve politikanın yeniden
koşulabilirliği. `kiraat/provenance.py` eklendi ve `export` artık
manifestonun yanına `manifests/run.json` yazıyor: oluşturma zamanı, git
commit'i/dalı/**kirli olup olmadığı**, yedi aşamanın sürüm dizgesi, politika
sürümü, model kimlikleri (revizyon ya da onu sabitleyen paket), paket
sürümleri, sayımlar ve konfigin tamamı. Paket sürümleri `importlib.metadata`
ile okunuyor, modüller içe aktarılmıyor — yalnız `--stages export` koşan bir
çağrı torch yüklemek zorunda kalmasın.

Çalışma ağacı kirliyken üretilmiş manifest commit'ten yeniden üretilemez;
`export` bunu uyarı basıyor ve kayda `git.dirty` olarak yazıyor.
Doğrulayıcıya dört denetim eklendi: kayıt var mı, klip sayısı manifestle
aynı mı, aşama sürümleri depodaki 'bitti' kayıtlarıyla uyuşuyor mu, her
paket ve her ağırlık sabit mi. Uçtan uca sınandı — 33 kliplik koşuda yedi
aşamanın sürümü de depodakiyle birebir uyuştu.

**Düzeltme.** 30 Ağu sabahki kayıtta tepe sınırlayıcısı için "sütun yapısal
olarak sıfırdan başka değer alamaz" denmişti; bu yanlıştı ve üstelik
`docs/FEATURES.md` §1 aynı olguyu zaten daha doğru anlatıyordu — sınırlayıcı
kaynak hızında uygulanıp ses sonra 24 kHz'e indirildiği için örnekler-arası
taşma oluyor (19 kayıtlık örnekte tepe medyanı tavanı 0,06 dB, p90'ı 0,15 dB
aşıyor). O bölüm okunmadan sentetik bir 24 kHz sinyalle sınanmıştı ve
sinyalde yeniden örnekleme hiç koşmadığı için tavan temiz göründü. Ölçümün
doğru hâli: sınırlayıcı kırpılma sinyalini **bastırıyor** (aynı kaynaklarda
`clip_ratio > 0`: 6 → 0), yok etmiyor. Karar değişmiyor, gerekçe düzeldi;
§1 kodla uyumlandı.

**Ölü sütun muhafızı ölçeğe bağlandı.** Politikada adı geçen bir ölçümün
korpusta tek değere çakılı olması küçük örneklemde beklenen bir şey (33
kliplik koşuda `clip_ratio` sabit sıfır çıktı, kusur değil). Denetim artık
500 klipten sonra bağlayıcı, altında bilgi olarak raporlanıyor.

**Açık kalan.** Bölme (train/dev/test) mantığı ve sızıntı denetimi hâlâ yok;
`export` tek bir `clips.jsonl` yazıyor. Aynı kitabın farklı kanallarda farklı
kişilerce okunması yüzünden yalnız kaynak düzeyinde bölmek yetmiyor — bölme
hem kaynağa hem metne göre yapılmalı ve kalan örtüşme ölçülüp raporlanmalı.
Veri hazır olmadan yapılamaz, koşudan sonraya kalıyor.

## 2026-08-30 — `sample-25c`: geçerli denetim örnekleminin toplu sayıları

Örneklem sayıları bugüne kadar üç ayrı kayda dağılmıştı (iki kör dinleme
turu ve düzeltmeler); makalenin §Örneklem bölümü tek bir yerden okunabilsin
diye burada toplanıyor. Koşu `work/sample-25c`, politika **v6**,
doğrulayıcı `HATA YOK`.

**Örneklem.** 27 kanalın hepsinden 3'er kayıt = **81 kaynak**, kayıt başına
en çok 20 dakika (`prepare.max_minutes: 20`), toplam 27 saat ham ses; koşu
39 dakika, yani **41,5× gerçek zaman** (CPU/GPU dağıtıcısıyla).

**Çıktı.** **13.637 klip / 23,17 saat** (ham sesin %86'sı klip oldu).
Süre: medyan 5,9 s, p5 2,7, p95 11,1; 15 saniyeyi aşan 63 klip (`oversize`
payla birlikte). Önerilen alt küme **11.291 klip (%82,8) / 18,98 saat**.

**İşaretler.** `background_music` 1.775 (%13,0), `forced_split` 360 (%2,6),
`short` 165 (%1,2), `oversize` 48 (%0,4), `boilerplate` 35 (%0,3),
`gap_split` 25 (%0,2), `duplicate` 21 (%0,2). Dışlamanın büyük çoğunluğu
tek başına müzik işaretinden geliyor (1.691 klip).

**Kanal dağılımı.** Önerilen oranı kanaldan kanala çok değişiyor: 20
kanalda %88'in üstünde, buna karşılık `Peri_Mia` %6,6, `SESLİKİTAPEVİ`
%30,7, `sesli-kitaplar` %37,0 — üçünde de sebep `background_music`
(Peri_Mia'nın kliplerinin %92,7'si işaretli). Yani müzik işareti korpusta
tek tek kliplere değil, **kanallara** yığılıyor. Hiçbir klip silinmediği ve
politika yeniden hesaplanabildiği için bu bir veri kaybı değil; ama
`recommended` alt kümesi fiilen bazı kanalları dışarıda bırakıyor ve bu,
`clip_ratio` ile `word_confidence` turlarında düşen örüntünün aynısı.
Müzik eşiği kör dinlemeden geçmiş tek sinyaldir (28 Ağu, 34 klip), ama o
dinleme bu kanalları içermiyordu.

**Açık madde 15 — müzik işaretinin kanal yığılması.** `Peri_Mia`,
`SESLİKİTAPEVİ` ve `sesli-kitaplar` kliplerinden bantlara dengelenmiş
30–40 kliplik bir kör dinleme turu; soru: bu kliplerde gerçekten duyulur
müzik var mı, yoksa eşik o kanalların tınısını mı yakalıyor? Sonuç, tam
koşudan sonra da politika yeniden hesaplanarak uygulanabilir — koşuyu
bekletmez.

**Makaleye:** §Örneklem (bütün bu sayılar), §Sınırlar (müzik işaretinin
kanal yığılması).

## 2026-08-30 — Kör dinleme: `clip_ratio` kuralı kaldırıldı (politika v5)

Tepe sınırlayıcı kalkınca `clip_ratio` kuralı canlandı: önceki koşuda tek bir
klip elemiyordu, sample-25c'de **536 klip** elemeye başladı. Dağılıma bakınca
örüntü tanıdık çıktı — 536'nın **532'si tek kanaldaydı** (`sess-Seslikitap`,
kliplerinin %93,2'si), kalan 26 kanal toplam 4 klip verdi. Yani sinyal klip
özelliği değil kanal özelliğiydi. Bu örüntü hattın en tehlikeli hata sınıfı:
doğrulanmamış bir ölçü kapı yapıldığında elediği şey "kötü klip" değil,
"o kanal" oluyor.

O kanal ölçüm olarak gerçekten ayrı duruyor: RMS medyanı **−12,70 dBFS**
(korpus medyanı −21,37, yaklaşık 9 dB daha yüksek) ve **571 klibinin
571'i tam −0,000 dBFS'te tepe yapıyor** — duvara dayanmış bir mastering.
Yani ölçüm bir şey buluyordu. Soru, bulduğu şeyin duyulup duyulmadığıydı.

**Denetim.** 25 klip, altı `clip_ratio` bandından (0 kontrol; 0–0,0005;
0,0005–0,002; 0,002–0,006; 0,006–0,015; >0,015), kanal ve ölçüm gizli,
karışık sırada. Üst iki bant zorunlu olarak tek kanaldan geldi, çünkü o
değerler yalnızca orada var — bu zaten bulgunun kendisi. Sorular: kırpılma
(yok/hafif/belirgin/baskın) ve "bu klip bir TTS modelinin öğrenmesini ister
misin". Sayfada ayrıca "gür ses kırpılma değildir" uyarısı vardı, çünkü
ayırt edilmesi gereken tam buydu.

**Sonuç: 24 "yok", 1 "hafif", 0 "belirgin", 0 "baskın"; 25/25 "eğitime
girsin".** Tek "hafif" cevabı en düşük bantta, `clip_ratio` 0,00001'de —
yani aralığın tabanında, tepesinde değil. Eşiğin üstündeki yedi klibin
(0,0025–0,0227) hiçbirinde bozulma duyulmadı, en yüksek değer dahil.
Korpustaki azami `clip_ratio` 0,0246 olduğu için aralığın tamamı denendi.

En az hatalı eşik hesabı 0,0227 verdi ve bu bir eşik değil, "gözlenen her
şeyin üstü" demek: mevcut kural 0,002'de 7 klibi boşuna eliyor, sıfır
kaçırıyor. Kural kaldırıldı (**politika v5**); sütun yayımlanmaya devam
ediyor, kullanıcı kendi eşiğini kesebilir.

**Etkisi.** Önerilen alt küme %73,6 → **%77,2** (10.042 → 10.522 klip;
16,73 → 17,49 saat). `sess-Seslikitap` %6,1 → **%90,0**. Yani doğrulanmamış
bir eşik, bir kanalın onda dokuzunu duyulmayan bir sebeple siliyordu.

**Gücün sınırı, dürüstçe.** Eşiğin üstünde yalnızca 7 klip dinlendi; 0/7
duyulmaması, gerçek duyulur oranın %35'e kadar çıkabilme ihtimalini dışlamaz
(%95 üst sınır). Ama karar yönü bunu gerektirmiyor: deponun değişmezi bir
sinyalin **kapı olabilmesi için** kör dinlemeden geçmesini şart koşuyor,
tersini değil. Kural geçemedi, dolayısıyla çıktı. Geri konmak istenirse
pozitif bir sonuç gerekir. Ayrıca "eğitime girsin mi" sorusuna 25/25 "evet"
gelmesi, kararın kendisi için tek başına yeterli.

**Makaleye.** Bu, hattın kendi tezinin kendi üzerinde gösterilmiş hâli:
standart, makul bir kalite ölçüsü (dijital kırpılma oranı) makul bir eşikle
bir kanalın %93'ünü sessizce silecekti ve kör dinleme o kliplerin hepsinin
eğitime uygun olduğunu söyledi. Kusur yayımdan **önce** yakalandı, çünkü
kapı olacak her sinyal dinleme sınavından geçiriliyor. Kanıt dosyaları
`work/archive/sample-25c/` altında (`clipping-key.json`,
`clipping-answers-1.json`, `listen-clipping.txt`).

**Araç.** `scripts/listen_ui.py`'ye `clipping` soru kümesi ve `--ids-file`
seçeneği eklendi (bantlara göre dengelenmiş bir liste dışarıda kurulup
verilebiliyor; `listen-*.txt` biçimi `browse_ui`'nin hazır liste
seçicisiyle ortak). Skorlayıcı, müzik eşiği kararındaki yöntemin aynısını
uyguluyor: her aday eşikte kaçan ve boşuna elenen sayılıp en az hatalı olan
bildiriliyor.

## 2026-08-30 — Kör dinleme: `word_confidence` kuralı kaldırıldı (politika v6)

`clip_ratio` çıkınca politikadaki en büyük doğrulanmamış kural
`word_confidence < 0,60` kaldı: **978 klip (%7,2)**, tam koşuda ~220 saat
eder. Müzik kuralı zaten kör dinlemeden geçmişti, geri kalanlar yapısal
işaretler. Ayrıca şemayla politika arasında bir çelişki duruyordu:
`kiraat/schema.py` bu sütunu "bir kapı değil, sıralama sinyalidir" diye
tarif ediyor ama politika onu kapı olarak kullanıyordu.

**Denetim.** 30 klip, altı `word_confidence` bandından beşer tane (kontrol
>0,90; 0,80–0,90; 0,60–0,80; eşiğin hemen altı 0,45–0,60; 0,30–0,45;
<0,30), kanal ve ölçüm gizli, karışık sırada; yarısı kuralın elediği yarısı
önerilen. Müzikli, bölünmüş, kısa ve işaretli klipler havuzun dışında
bırakıldı ki tek değişken metin olsun. Soru ses kalitesi değil: yazılı metin
duyulanla birebir aynı mı (doğru / küçük hata / bir kelime yanlış / birden
çok kelime yanlış) ve klip eğitime girsin mi.

**Sonuç: 29 "birebir doğru", 1 "küçük hata"; 0 "kelime yanlış", 0 "çok
yanlış"; 30/30 "eğitime girsin".** Tek hata en düşük klipte, `word_confidence`
**0,178**'de — "mebus" yerine "meybus" yazılmış. 0,60 eşiği bu 30 klibin
15'ini eliyordu ve 14'ü kusursuz bulundu.

**Kulaktan bağımsız kontrol.** Hizalayıcı skoru ses–metin uyumunu Whisper'dan
bağımsız ölçer, dolayısıyla dinlemenin ikinci bir kanıtıdır. 11.343 işaretsiz
klipte `word_confidence` ile `align_score_min` sıra korelasyonu **+0,262** —
zayıf. Bantlar yine de tek yönlü:

| word_confidence | n | align_score_min medyanı | align_score_mean medyanı |
|---|---|---|---|
| <0,30 | 37 | 0,697 | 0,938 |
| 0,30–0,45 | 182 | 0,682 | 0,942 |
| 0,45–0,60 | 568 | 0,728 | 0,950 |
| 0,60–0,80 | 2.088 | 0,749 | 0,954 |
| >0,80 | 8.468 | 0,827 | 0,966 |

`align_score_min < 0,5` oranı düşük güvenli kliplerde %21,4, yüksek olanlarda
%11,1 — iki katı. Yani sinyal boş değil, `clip_ratio`dan farklı olarak gerçek
bir bilgi taşıyor. Ama en kötü bantta bile `align_score_mean` medyanı 0,938;
hizalama iyi, yani metin sese oturuyor.

**Karar.** Kural kaldırıldı (**politika v6**), sütun yayımlanmaya devam
ediyor. Gerekçe iki katmanlı: (1) deponun değişmezi bir sinyalin kapı
olabilmesi için kör dinlemeden geçmesini şart koşuyor ve 0,60'ta geçemedi;
(2) sinyal zayıf da olsa gerçek olduğu için sütun değerli — şemanın zaten
söylediği yere, sıralama sinyaline geri döndü ve şema–politika çelişkisi
kapandı. Kullanıcı kendi eşiğini kesebilir.

**Etkisi.** Önerilen alt küme %77,2 → **%82,8** (10.522 → 11.291 klip;
17,49 → 18,98 saat). `sess-Seslikitap` iki turun sonunda %6,1 → **%97,4**.

**Gücün sınırı.** Bant başına 5 klip az; kuralın asıl vurduğu 0,45–0,60
bandından yalnızca 5 klip dinlendi ve 5/5 doğru çıktı — gerçek hata oranının
%45'e kadar olabilmesini dışlamaz (%95 üst sınır). Karar yönü yine bunu
gerektirmiyor: kapıyı kaldırmak için kanıt yükü kapıdadır, veride değil.
Eşik geri konmak istenirse elenen popülasyona odaklanmış, 40–60 kliplik bir
tur gerekir.

**İki turun ortak dersi — makaleye.** Bir günde iki ayrı standart kalite
ölçüsü, makul eşiklerle, kör dinlemede tutunamadı: dijital kırpılma oranı bir
kanalın %93'ünü, ASR kelime güveni korpusun %7,2'sini siliyordu ve dinleyici
elenen kliplerin neredeyse tamamını eğitime uygun buldu. İkisi de yayımdan
önce, kendi verimiz üzerinde yakalandı; makalede iddia bu iki turun
ölçümüne dayanır. Kanıt dosyaları `work/archive/sample-25c/` altında.

## 2026-08-30 — Kör dinleme: sınır kesimi temiz; denetim ölçütü damgadan sese taşındı

Doğrulayıcının en uzun süredir açık duran FAIL'i: 161 klipte klip başı,
hizalayıcının ilk kelime damgasını 0,13–0,47 s geçiyordu ve bunların 16'sı
önerilen alt kümedeydi. İki açıklama vardı — ya ilk hece gerçekten kesiliyor,
ya damga yanlış. Karar kulağındı.

**Denetim.** 30 klip: 20 şüpheli (gecikme bantlarına yayılmış, 7'si en uç
değerlerden) + 10 kontrol (denetimi geçen klipler), karışık sırada, hangisinin
hangisi olduğu gizli. Sorular: klip cümle başında mı başlıyor, cümle bitince
mi bitiyor, başta/sonda kelime kesik mi.

**Sonuç: 20/20 şüphelide ve 10/10 kontrolde sıfır kesik kelime, sıfır kırık
başlangıç, sıfır kırık bitiş.** En uç yedi klipte de kesik yok. Yani sınır
iyileştirme damganın ötesindeki gerçek sessizliğe yaslanıyor ve **doğru
yapıyor**; kusurlu olan damgaydı. "Sınır damgayı geçmesin" bir doğruluk
ölçütü değilmiş.

Denetim buna göre değiştirildi: 161 klip artık bilgi olarak raporlanıyor,
FAIL ölçütü damgadan bağımsız ve yapısal olana taşındı — *klibin kendi kelime
aralığındaki bir kelime tamamen sınırların dışında kalıyor mu*, yani metin
sesle uyuşmuyor mu.

**Yanlış teşhis ve geri alınması.** Yeni ölçüt bir klip yakaladı
(`src00017-00127`: metin "4 Nisan 1984…", ses "Nisan"dan başlıyor gibi
görünüyordu, üstelik önerilen alt kümedeydi). Sebebin kısa ilk kelimeden
sonraki duraklamada sınırın ikinci kelimeyi yutması olduğu varsayıldı,
`boundaries.py`'ye bir muhafız ve bir test yazıldı. **Test, düzeltme öncesi
kodda da geçti** — yani senaryoyu üretmiyordu. Kovalayınca gerçek sebep başka
çıktı ve muhafız geri alındı. Buradaki ders yönteme ait: düzeltmenin testi,
düzeltme geri alındığında düşmüyorsa o düzeltme kanıtlanmamıştır.

**Gerçek sebep: rakamlar hizalanamıyor.**

```
'4'      asr=825.150–825.450   align=None            skor=None
'Nisan'  asr=825.450–825.870   align=824.45–826.09   skor=0.0004
'1984,'  asr=825.870–826.250   align=None            skor=None
```

Hizalayıcı romanize **harfler** üzerinde çalışıyor; rakamın sözlük karşılığı
yok, hiç hizalanmıyor ve damgası Whisper yedeğine düşüyor. Komşusu "Nisan" da
hedefsiz kalan akustik bölgeyi yutup 0,0004 skorlu çöp bir hizalama alıyor.
Sonuçta bir kelimede hizalayıcı saati, yanındakinde Whisper saati kullanılıyor
ve sıra bozulabiliyor. Klip aslında doğru — "4" 825,150'de, klip 825,000'de
başlıyor, ses yerinde.

**Ölçüldü (166.614 kelime):**

- Hizalanamayan kelime: **734 (%0,44)**, 733'ü rakam, 1'i noktalama.
- Skoru <0,01 olan çöp hizalama: **245 (%0,147)**; yalnız 5'i hizalanamayan
  bir kelimenin komşusu, yani rakamlar bunun küçük bir kısmını açıklıyor.
- `align_score_min < 0,01` olan klip: **289 (%2,12)**, 221'i önerilen alt
  kümede. `align_score` kapı olmadığı için veri elenmiyor, ama yayımlanan bir
  sütunun %2'si anlamsız.

Çöp hizalamaların örüntüsü 28 Ağustos'ta not edilenin aynısı ve artık ölçekli:
hepsi cümle başındaki kısa sözcükler ("Çünkü", "Ey", "Bu", "Bir", "Biz"),
hizalayıcı onları önceki cümlenin hemen ardındaki 20–220 ms'ye sıkıştırmış.
Sebebin hizalama parçalarının cümle boşluklarında kesilmesi olduğu tahmin
edildi ve **sınandı: tutmadı** — çöp hizalamaların yalnızca %4'ü parça başında
(korpus tabanı %1,6, yani 2 kat zenginleşme, açıklayıcı değil). Sebep açık
kalıyor.

**Doğrulayıcı.** Kapsama denetimi artık yalnızca güvenilir damgalara
uygulanıyor: kelime hem hizalanmış hem skoru ≥0,01 olmalı. Bu ölçütle
`src00017-00127` doğru şekilde düşüyor (damgası güvenilir değil, klip değil).
İki bilgi satırı eklendi: hizalanamayan kelime sayısı ve sınırı damgayı aşan
klip sayısı. Kalan tek FAIL, küçük harfle başlayan 4 klip (açık madde 11).

**Belgelenmiş sınır — rakamlar hizalanmaz.** Hizalayıcının sözlüğü romanize
harflerden oluşur, dolayısıyla rakamların karşılığı yoktur ve hizalanmazlar
(733 kelime, %0,44); damgaları Whisper yedeğine düşer. Bu hattın kabul
edilmiş bir sınırıdır, açık madde değil: hizalamayı okunuş metni üzerinden
kurmak akla gelir ama yapılmayacak — kelime aralığı ile `text_raw`
arasındaki birebir karşılık bozulur ve damgalar normalizasyonun doğruluğuna
bağlanır. Sütunun sınırı makalede böyle anlatılır.

**Açık madde 13 — cümle başı kısa sözcüklerde çöp hizalama.** 245 kelime,
289 klip, sebep bilinmiyor; parça sınırı hipotezi elendi. `align_score`
makalede yayımlanacağı için bunun ya açıklanması ya da sütunun sınırının
belgelenmesi gerekiyor.

## 2026-08-30 — Tam koşu hazırlık denetimi: korpus envanteri ve uzun kayıtta bellek duvarı

> **Kısmen eskidi (31 Ağu 2026):** buradaki envanter sayıları kabaydı
> (3.427,8 saat, "165 kayıt 4 saatten uzun") ve aynı gün dosya dosya
> yapılan ölçümle değiştirildi — geçerli sayılar "Envanter" kaydındadır
> (3.440,2 saat; 4–8 saat bandında 131, 8 saat üstünde 35 kayıt). Bellek
> ölçümleri ve teşhis geçerliliğini koruyor; açık madde 14 kapandı.


Tam koşu öncesi son denetim. Üç şey ölçüldü: ham korpusun gerçek büyüklüğü,
tam koşunun disk ve süre maliyeti, ve hattın örnekte hiç görmediği bir
şeye — saatlerce süren tek bir kayda — verdiği tepki.

**Envanter (ffprobe, 2.695 dosya).** Ham malzeme **3.427,8 saat**, 27 kanal,
2.695 kayıt; biri (`seslimakalem/NEDRET ERSANEL…m4a`) ffprobe ile
okunamıyor, kalan 2.694 okunuyor. Kayıt süresi medyanı **41,4 dakika**,
p90 **184,7 dakika**, azami **14,92 saat**; 4 saatten uzun **165**, 8 saatten
uzun **34** kayıt var. Uzantı listesi dışında kalan 4 `.m4aa` dosyası sessizce
atlanıyor.

Bu sayı defterin ilk kaydındaki "2.370 kayıt, 2.942 saat" ile uyuşmuyor;
makaleye giren §Korpus sayısı buradaki ölçüm olmalı. Kanal dağılımı da
buradan çıktı: `seslikitaplarmavi` %19,6 (671 saat), `BirDinle` %15,6 (534
saat), ilk iki kanalın payı **%35,2**. Konfigdeki `export.max_hours_per_channel:
120` tavanı uygulansaydı 3.427,8 saat **1.849 saate** inerdi; tavanı okuyan
kod yok, yani konfig şu an uygulanmayan bir kural ilan ediyor.

**Bellek duvarı — asıl bulgu.** Bugüne kadarki bütün örnek koşularda
`prepare.max_minutes` 20 idi; hattın gördüğü en uzun kayıt 20 dakikalık.
Tam koşuda tavan kalkıyor ve `segment` ile `align` kaydın tamamını belleğe
alıyor (`sf.read` + `mean` iki kopya). Üstüne `boundaries.envelope`,
kare dizinini `idx = arange(n)[:,None]*hop + arange(frame)[None,:]` ile
maddileştiriyor: 24 kHz'de kare 480, adım 240 örnek, yani örnek başına
16 bayt int64 dizin + 8 bayt toplanmış kare. Ölçüldü (10/30/60 dk, doğrusal):
**saat başına 2,73 GB zirve RSS**. `align`'daki 24→16 kHz yeniden örnekleme
tek çağrıda yapılıyor, o da **saat başına 2,19 GB**.

Kayıt uzunluğuna göre tek işçinin zirvesi:

| kayıt | segment (env+kopya) | align (resample+kopya) | korpusta |
|---|---|---|---|
| 20 dk (örnek) | ~1,0 GB | ~0,8 GB | denendi |
| 4 saat | ~12 GB | ~10 GB | 165 kayıt |
| 8 saat | ~24 GB | ~20 GB | 34 kayıt |
| 14,9 saat | ~45 GB | ~37 GB | 1 kayıt |

Makinede 62 GB RAM (~50 GB boş) var ve dağıtıcı 6 CPU işçisi çalıştırıyor;
dört saatlik iki kaydın aynı anda bölütlenmesi bile 24 GB demek, en uzun
kayıt tek başına RAM'i bitiriyor. Bir işçi OOM ile öldürülürse
`ProcessPoolExecutor` kırılır: kaynak işlerinde hata yakalanıp kayıt
"hatalı" işaretlendiği için koşu **sessizce** kalan bütün kayıtları
düşürerek devam edebilir. Üç günlük bir koşuda en kötü kusur budur.

Düzeltme yönü belli: zarf hesabı bloklara bölünecek (sonuç bit bazında aynı
kalmalı), yeniden örnekleme parça parça yapılacak, `always_2d` okumadaki
ikinci kopya kaldırılacak. **Tam koşu bu düzeltme ve en uzun kayıtla
yapılacak tek kayıtlık bir duman testi olmadan başlatılmaz.**

**Maliyet.** sample-25c'de 27 saat ham ses 39 dakikada işlendi, yani
**41,5× gerçek zaman**; 3.427,8 saat bu hızda **~83 saat (3,5 gün)** sürekli
koşu demek. Disk: ara ses 83 MB/saat, klipler 92 MB/saat ölçüldü →
**~555 GB** (283 GB ara ses + 272 GB klip), diskte 702 GB boş. Sığıyor ama
yayın paketi için ikinci bir kopyaya (önerilen alt küme ~270 GB) yer
kalmıyor; ara sesin koşu sonunda silinip silinmeyeceği ayrı bir karar.
Beklenen çıktı ölçeği: ~2.940 saat klip, ~1,73 milyon klip.

**Değişmeyenler.** Test takımı 122 geçiyor (1 atlanıyor: varsayılan yolda
manifest yok), `verify_columns.py` sample-25c'de sıfır hatayla geçiyor,
şema ile manifest birebir. İzlenen dosyalarda değişiklik yok, yani tam
koşunun kaydı temiz commit gösterecek.

**Makaleye:** §Korpus (envanter sayıları, kanal dağılımı), §Uygulama
(maliyet ve ölçek), §Sınırlar (kanal payı ve tavan kararı).

~~**Açık madde 14 — uzun kayıtta bellek.**~~ — *kapandı (30 Ağu 2026):
zarf bloklu, bölütleme ve hizalama diskten pencere okuyor; çıktı birebir
aynı, 14,92 saatlik kayıt uçtan uca koştu. Aşağıdaki kayda bakınız.*

## 2026-08-30 — Envanter: ham korpusun sınırları dosya dosya ölçüldü

Yukarıdaki hazırlık denetimi korpusu kabaca saymıştı; bu kayıt onun yerine
geçer. `scripts/inventory.py` ham kökteki **her** dosyayı ffprobe'dan
geçirir (uzantı listesinin dışındakileri de) ve künyesini
`work/inventory.jsonl`'e yazar: süre, kodek, örnekleme hızı, kanal sayısı,
bit hızı, boyut. Rapor bu dosyadan üretilir, yani ölçüm bir kez yapılır.

**Bulunan.** 2.700 dosya, **2.698 okunabilir ses**, **3.440,2 saat**,
200,1 GB, 27 kanal. Biri ffprobe ile açılamıyor
(`seslimakalem/NEDRET ERSANEL…m4a`), biri `README.md`. Konfigdeki uzantı
listesi dört `.m4aa` dosyasını dışarıda bırakıyor: **12,41 saat** sessizce
atlanıyor, yani hattın alacağı 2.694 dosya ve 3.427,8 saat.

**Kayıt uzunluğu — hattın bugüne kadar görmediği şey.** Medyan 41,4 dakika,
p75 90,9 dakika, p90 185,0, p95 257,5, **p99 517,7 dakika**, azami
**14,92 saat**. Dağılım saatlik bantlarda:

| kayıt uzunluğu | kayıt | saat | korpus payı |
|---|---|---|---|
| < 10 dk | 168 | 20,4 | %0,6 |
| 10–30 dk | 911 | 274,0 | %8,0 |
| 30–60 dk | 635 | 462,8 | %13,5 |
| 1–2 saat | 467 | 654,7 | %19,0 |
| 2–4 saat | 351 | 973,4 | %28,3 |
| **4–8 saat** | **131** | **700,5** | **%20,4** |
| **8 saat+** | **35** | **354,4** | **%10,3** |

Yani korpusun **%30,7'si dört saatten uzun tek parça kayıtlarda**; bütün
örnek koşular kayıt başına 20 dakikayla sınırlıydı ve bu kütleyi hiç
görmedi. Örnekten genelleme burada kırılıyor: 20 dakikalık kayıtta bedava
olan "kaydı belleğe al" adımı 14,9 saatlik kayıtta duvara çarpıyor
(aşağıdaki bellek kaydına bakınız).

**Biçim tekdüze.** 2.618 dosya AAC (3.379,7 saat), 80 dosya MP3 (60,5 saat);
**2.693 dosya 44,1 kHz**, beşi 48 kHz; 2.694 dosya iki kanallı, dördü mono.
Dosya boyutundan hesaplanan bit hızı p5 128 / medyan 129 / p95 130 kb/s —
korpus fiilen tek bir kodlama profilinde. (ffprobe'un akış düzeyi `bit_rate`
alanı bu m4a'larda anlamsız değerler veriyor; ölçü kapsayıcıdan ve dosya
boyutundan alınmalı.)

**Kaynağın gerçek bant genişliği.** 128 kb/s AAC bir alçak geçiren getirir;
hedef 24 kHz'in (Nyquist 12 kHz) kaynağı kesip kesmediği ölçülmeli. Kanal
başına bir kayıt, ortadan 60 saniye, 32k FFT: kesim frekansı **medyan
15,7 kHz**, en düşük 13,0 (`seskitap`), en yüksek 15,8. 12 kHz üstünde kalan
enerji payı medyan **%0,05**, azami %0,62 (`kitapdinle`). Yani 24 kHz hedef
kodeğin tavanının epey altında; yükseltmenin karşılığı yok, düşürmenin
gerekçesi de yok. İki kanal (13,0 ve 13,7 kHz) kaynağında zaten dar bantlı.

**Kanal dağılımı.** `seslikitaplarmavi` %19,5 (671,0 saat), `BirDinle`
%15,5 (534,4), `sess-Seslikitap` %7,4, `dinleyiniz` %7,4, `Peri_Mia` %7,0;
ilk iki kanalın payı **%35,2**, dokuz kanal 120 saatin üstünde. Konfigdeki
`export.max_hours_per_channel: 120` uygulansa korpus 3.440 → **1.849 saate**
inerdi. O tavanı okuyan kod yok; ya bağlanmalı ya konfigden çıkmalı, çünkü
şu hâliyle uygulanmayan bir kural ilan ediyor.

**Makaleye:** §Korpus (bütün bu sayılar), §Yöntem (24 kHz kararının kaynak
bant genişliğiyle gerekçesi), §Sınırlar (kanal payı, tek kodlama profili).

## 2026-08-30 — Alanın yerleşik yöntemi: kiraat neyi paylaşıyor, nerede ayrılıyor

Hattın kararları bugüne kadar kendi ölçümlerimizden çıktı. Bu kayıt, aynı
işi yapan yayımlanmış hatları okuyup kiraat'in her kararını onların yanına
koyar: hangisi yerleşik uygulamayla aynı, hangisi bilinçli bir ayrılık.
Makalede "farklı yapıyoruz" demenin bedeli, farkın nereden geçtiğini
göstermektir.

**Okunanlar.** Emilia / Emilia-Pipe (arXiv 2407.05361 ve 2501.15907),
LibriTTS (arXiv 1904.02882), Libriheavy (arXiv 2309.08105), GigaSpeech 2
(ACL 2025, arXiv 2406.11546), ManaTTS (NAACL 2025, arXiv 2409.07259) ve
hizalama araçlarının 2026 durum değerlendirmesi (arXiv 2606.18466).

**Ortaklaştığımız yerler.** LibriTTS kesimi sessizlikte değil **cümle
sınırında** yapar ve gerekçesi bizimkiyle aynıdır: cümle düzeyi bürün ancak
cümle bütünken öğrenilir; Libriheavy de kesimi cümle sınırına koyar ve
30 saniyeye kadar parça üretir. LibriTTS 16 kHz'i "yüksek kaliteli TTS için
çok düşük" bulup **24 kHz**'e geçer; Emilia da 24 kHz'de yayımlar — bizim
hedefimiz de 24 kHz ve yukarıdaki envanter bunu kaynağın bant genişliğiyle
ayrıca doğruluyor. LibriTTS hem ham hem normalize metni yayımlar ve büyük
harf/noktalama bilgisini korur; bizde bu üç alan olarak var (`text_raw`,
`text`, `text_spoken`). GigaSpeech 2, düşük kaynaklı diller için tam bizim
sıramızı kurar: Whisper ile yazıya çevir, **MMS ile zorlamalı hizala**,
sonra çok boyutlu süz.

**Ayrıldığımız yer — eşik.** Yerleşik hatların hepsi kalite ölçüsünü kapı
olarak kullanır: Emilia **DNSMOS OVRL ≥ 3,0** altındaki her klibi atar
(Emilia-Large'da eşik 2,4'e indirilmiş), LibriTTS "clean" altkümesinde
**SNR ≥ 20 dB** ister, ikisi de dil kimliği ve süre aykırılığıyla eler.
LibriTTS'in daha sıkı hattı LibriSpeech'in 982 saatini **585 saate** (%60)
indirir. kiraat hiçbir eşikle klip elemez; ölçümü sütun olarak yayımlar ve
kararı sürümlü `recommended_subset` politikasına bırakır. Bu ayrılığın
gerekçesi artık ölçülü: 30 Ağustos'ta iki standart kalite ölçüsü
(`clip_ratio`, `word_confidence`) makul eşiklerle kör dinlemede tutunamadı
ve elenen kliplerin neredeyse tamamı dinleyiciye göre eğitime uygundu.
Yerleşik yöntem yayımdan önce dinlenmediğinde ne kaybettirdiğini
göstermiyor; bizim katkımız tam olarak burası.

**Ayrıldığımız yer — sesin kendisine dokunmamak.** Emilia yayımladığı sesi
önce kaynak ayrıştırmasından geçirir (UVR-MDX-Net) ve **−20 dBFS**'e
normalize eder; yani yayımlanan dalga biçimi işlenmiş sestir. kiraat
ayrıştırmayı yalnızca **ölçmek** için koşturur (müzik/konuşma oranı) ve sesi
olduğu gibi bırakır, seviyeyi de sütun olarak verir. Gerekçe aynı değişmez:
aşama ölçer, karar vermez — normalizasyon ve müzik bastırma kullanıcının
tercihidir, korpusun dayatması değil.

**Süre bandı.** Emilia 3–30 s, LibriTTS/Libriheavy 30 s'ye kadar, alandaki
pratik kılavuzlar 2–12 s aralığını öneriyor. Bizde `min_sec 1,5` /
`target 7` / `max 15`; üretilen dağılım medyan 5,9 s, p95 11,1 s. Alt sınır
alandan düşük, üst sınır yüksek değil — kısa kliplerin `short` işaretiyle
yayımlanıp politikada dışlanması bu farkı zaten karşılıyor.

**Uzun kayıt konusunda literatür bize yol göstermiyor.** Emilia'nın
girdilerinin süresi **20,09–3.596,27 saniye** aralığında, yani en uzun
kaydı bir saat; YouTube videolarıyla çalışıyor. Libriheavy uzun formu kitap
metnine hizalayarak çözüyor, bizde referans metin yok. Bizim korpusumuzda
kayıtların %30,7'si dört saatin üstünde ve en uzunu 14,9 saat. Dolayısıyla
"çok saatlik tek parça kaydı sabit bellekle işlemek" bu hattın kendi
sorunu ve makalede yöntem olarak anlatılacak bir katkı — aşağıdaki bellek
kaydı bunun ölçülmüş hâli.

**Hizalama güveni.** 2026 değerlendirmesi hizalayıcı skorlarının "modelin
kendine güveni" olduğunu, doğrulukla karıştırılmaması ve örneklem alınıp
elle denetlenmesi gerektiğini söylüyor. Bu bizim `align_score` konusundaki
duruşumuzu destekliyor: sütun yayımlanır, kapı olmaz, sınırı (rakamlar
hizalanmaz; cümle başı kısa sözcüklerde çöp hizalama) belgelenir.

**Buradan çıkan yapılacaklar.** (1) LibriTTS'in ses–metin uyuşmazlığını
yakalamak için kullandığı "ortalama kelime süresi aykırı" ölçüsü bizde
zaten türetilebilir durumda: `duration / n_words` iki yayımlanan sütundan
çıkıyor. Yeni bir ölçüm gerekmiyor; yapılacak iş, bu oranın dağılımını
korpusta çıkarıp aykırıların gerçekten uyuşmazlık olup olmadığını kör
dinlemeyle sınamak — sonuç olumluysa sütun olarak açıkça yayımlanır,
yine kapı yapılmaz.
(2) Klip başına **dil kimliği** skoru (Emilia ≥0,8 eşiğiyle kapı yapıyor;
biz sütun olarak) Türkçe olmayan klipleri görünür kılar. (3) DNSMOS
konfigde `enabled: true` görünüyor ama aşama yok — ya bağlanmalı ya
konfigden çıkmalı. (4) Konuşmacı kümeleme (Emilia pyannote 3.1 kullanıyor)
hâlâ bağlı değil ve `dedupe` bu yüzden kanala düşüyor.

**Makaleye:** §İlgili çalışmalar (yukarıdaki karşılaştırma), §Yöntem (cümle
sınırı ve 24 kHz kararlarının alandaki karşılığı), §Katkı (eşiksiz yayım ve
çok saatlik kayıt işleme), §Sınırlar (süre bandı farkı).

## 2026-08-30 — Uzun kayıt: bellek duvarı kaldırıldı, 14,9 saatlik kayıt uçtan uca koştu

Envanter korpusun %30,7'sinin dört saatten uzun kayıtlarda olduğunu
gösterdi; hattın gördüğü en uzun kayıt ise 20 dakikalıktı. Bu kayıt o
boşluğun kapatılmasıdır: önce kaydın uzunluğuyla büyüyen üç allokasyon
kaldırıldı, sonra korpusun **en uzun kaydı** (14,92 saat, BirDinle,
"Cennette İki Yıl") uçtan uca koşturuldu.

**Kaldırılan üç allokasyon.**

1. `boundaries.envelope` kare dizinini tek seferde maddileştiriyordu
   (`arange(n)[:,None]*hop + arange(frame)`): örnek başına 16 baytlık int64
   dizin + 8 baytlık toplanmış kare, ölçülen **saat başına 2,73 GB**. Artık
   kareler 32 MB'lık bloklar hâlinde, bitişik kopyayla hesaplanıyor —
   `np.mean`'in toplama sırası korunsun diye kopya bilinçli.
2. `segment` kaydın tamamını belleğe alıp (`always_2d` ile iki kopya)
   dilimliyordu. Artık zarf diskten akıtılıyor (`envelope_of_file`) ve her
   klip yalnızca kendi aralığı okunarak yazılıyor.
3. `align` kaydın tamamını okuyup tek çağrıda 24→16 kHz yeniden
   örnekliyordu (**saat başına 2,19 GB**). Artık her parça için diskten
   pencere okunuyor, iki yanına 0,5 s pay verilip pay atılıyor.

**Çıktının değişmediği kanıtlandı.** Zarf, eski uygulamayla **birebir aynı**
diziyi veriyor (iki örnekleme hızı × yedi uzunluk). Pencere okuyucunun
verdiği örnekler tam dosyayı yeniden örnekleyip dilimlemekle **azami fark
0,000e+00**; aynı modelle hizalanınca iki yoldan 745 kelimenin damgası ve
skoru aynı. Bölütlemede eski ve yeni aşama üç kaynakta yan yana koşturuldu:
**532 klibin manifest satırları aynı ve FLAC dosyaları SHA-256 düzeyinde
aynı**. Yani bu bir yeniden yazım değil, aynı hesabın sabit bellekli hâli.

**Ölçülen bellek.** 10 dakikalık sentetik kayıtta bölütleme zirvesi
**520 MB → 64 MB altı**; zarf 30 dakikada **1.210 MB → 35 MB**. Dört yeni
test bu sınırları bekçiye bağladı ve **eski koda dönülünce dördü de
düşüyor** (denendi).

**Duman testi — 14,92 saat, tek kayıt, `work/long-smoke`.**

| aşama | süre | gerçek zamana oran |
|---|---|---|
| prepare (ffmpeg → 24 kHz mono FLAC) | 151 s | 355× |
| asr (faster-whisper large-v3, toplu) | 733 s | 73× |
| align (MMS_FA, 30 s parçalar) | 261 s | 206× |
| segment (7.170 klip) | 209 s | 257× |
| clip_qc + music (7.170 klip) | ~200 s | — |
| **toplam** | **25 dk 58 s** | **34,5×** |

Zirve bellek: süreç ağacında **12,0 GB**, `time -v`'nin gördüğü tek süreç
azamisi 14,1 GB — ikisi de **ASR işçisi**. Bölütleme ve hizalama artık
kayıt uzunluğundan bağımsız; **kalan tek uzunluğa bağlı tüketici ASR**,
çünkü faster-whisper kaydı bütün olarak çözüyor (kabaca ses saati başına
0,8 GB). 62 GB'lık makinede bir ya da iki GPU işçisiyle bu sorun değil,
ama üçe çıkarmanın sınırı budur.

Çıktı: **7.170 klip, 13,46 saat** (kaynağın %90,2'si), önerilen **6.393
(%89,2), 11,52 saat**; süre medyanı 6,2 s, p95 13,0 s. İşaretler:
`forced_split` %7,0, `oversize` %1,0, `short` %0,9, `gap_split` %0,6,
`background_music` %0,3. 93.784 kelimenin 198'i (%0,21) hizalanamadı
(rakamlar). Disk: 2,2 GB, yani kaynak saati başına 147 MB — tam koşu
tahminiyle (156 MB/saat) uyumlu.

**Denetim bir FAIL verdi ve gerçek bir şeydi — ama ölçümde değil, yuvarlamada.**
`src00001-06029`: üç kelimenin üçü de 0,9995 olasılıklı; `word_confidence`
(min) doğrudan yuvarlanıp **1,0**, `word_confidence_mean` kayan nokta
toplamında 0,9994999…'e düşüp **0,999** oldu ve "min ≤ mean" denetimi
düştü. Ölçüm doğru, iki sütun da üç ondalığa yuvarlandığı için son
basamakta ters görünüyor. Denetime bir yuvarlama birimi tolerans kondu ve
gerekçesi oraya yazıldı. 7.170 klipte bir kez; 13.637 kliplik örnek koşuda
hiç görülmemişti — uzun kayıt yalnızca belleği değil, seyrek sayısal
durumları da açığa çıkarıyor.

**Açık madde 14 kapandı.** Doğrulayıcı `work/long-smoke` üzerinde
`HATA YOK` diyor; `work/sample-25c` de yeni kodla temiz kalıyor.

**Makaleye:** §Uygulama (çok saatlik kaydı sabit bellekle işleme; alanda
karşılığı yok — Emilia'nın en uzun girdisi bir saat), §Ölçek (aşama
süreleri ve bellek).

## 2026-08-30 — Karar: ham veri azaltılmaz; uzantı listesi genişledi, kanal tavanı kalktı

İki açık soruyu kullanıcı aynı ilkeyle kapattı: **kalite ve doğruluktan
ödün verilmez, ama veri miktarı azaltılmaz; mevcut bütün ham kayıtlardan
yararlanılır.** İkisi de konfige işlendi.

**Uzantı listesi.** `sources.extensions` altı uzantıdan ibaretti ve dört
`.m4aa` dosyasını (12,41 saat) sessizce dışarıda bırakıyordu. Liste artık
ffmpeg'in ses akışı çıkarabildiği bütün kapsayıcıları içeriyor; video
kapsayıcıları da listede, çünkü `prepare` zaten yalnızca ses akışını çözer.
Kuru koşuyla doğrulandı: hat artık **2.699 kaynak / 3.440,16 saat**
alıyor, envanterde uzantı yüzünden dışarıda kalan dosya **sıfır**.

Bu bir daha sessizce olmasın diye denetim `scripts/inventory.py`'de:
envanter konfigin listesinden geniş tarar ve "uzantı listesi dışında kalan
N dosya, X saat" satırını her koşuda basar.

**Kanal başına saat tavanı kaldırıldı.** `export.max_hours_per_channel: 120`
konfigde duruyordu ama onu okuyan kod yoktu — yani konfig uygulanmayan bir
kural ilan ediyordu. Uygulansaydı korpus 3.440 saatten **1.849 saate**
inecekti. Karar: tavan yok, anahtar konfigden çıkarıldı ve yerine ölçülen
dağılım yazıldı. Kanal dengesizliği gizlenmiyor, **yayımlanıyor**: her klip
`channel` ve `duration` taşıdığı için kullanıcı istediği tavanı kendisi
kesebilir. Bu, deponun "aşama ölçer, karar vermez" değişmezinin dışa
aktarımdaki karşılığı; dengelemeyi korpus dayatmaz, veri kartı anlatır.
Ölçülen dağılım: `seslikitaplarmavi` %19,5, `BirDinle` %15,5, ilk iki
kanal %35,2, dokuz kanal 120 saatin üstünde.

**Kaybedilen tek dosya kurtarılamıyor.** Ham kökte ffprobe'un açamadığı
dosya (`seslimakalem/NEDRET ERSANEL…m4a`) **0 bayt** — başarısız bir
indirme, içinde ses yok. Yani hattın dışında kalan hiçbir ses yok:
2.698 okunabilir kayıt, 3.440,2 saat, tamamı alınıyor.

**Bulunan kusur — kuru koşu bozuk dosyada çöküyordu.** Uzantı listesi
genişleyince ilk `--dry-run` `CalledProcessError` ile düştü: `dry_run`
kendi `duration_of`'unu veriyor ve o ffprobe hatasını yakalamıyordu
(`discover_sources`'ın kendi sarmalayıcısı yakalıyor). Düzeltildi: okunamayan
dosya süre 0 sayılır, koşu sürer ve dosya adıyla raporlanır — koşudaki
davranışın aynısı (`prepare` kaydı `error` ile işaretler). Testi var ve
düzeltme geri alınınca düşüyor.

**Etkisi.** Tam koşu beklentisi 3.427,8 → **3.440,2 saat**; süre ve disk
tahminleri pratik olarak değişmiyor (~83 saat, ~557 GB).

**Makaleye:** §Korpus (kapsam kararı: hiçbir kayıt kapsam dışı bırakılmadı),
§Sınırlar (kanal dengesizliği tavanla değil, sütunla ele alınıyor).

## 2026-08-30 — Ölü kalıntı taraması: on üç konfig anahtarı, üç ölü işlev, eskimiş yöntem belgesi

`export.max_hours_per_channel`'in "konfigde var, kodda yok" hâli tek başına
mı, yoksa bir örüntünün örneği miydi? Depo bu soruyla taranınca örüntü
olduğu çıktı.

**Konfigde okunmayan on üç anahtar.** Hiçbir kodun okumadığı anahtarlar:
`runtime.max_clips`, `prepare.target_lufs`, `clip_qc.enabled`,
`dnsmos.enabled`, `speaker.model`, `speaker.cluster_cosine`,
`events.model`, `events.gate_synthetic`, `music.audioset_labels`,
`music.separator`, `music.external_gate`, `export.sample_rate`,
`export.shard_rows` (ve daha önce kaldırılan `export.max_hours_per_channel`).

Bu yalnızca dağınıklık değil, iki somut zarar veriyordu:

1. **Konfig, kodun yaptığından başka bir şey ilan ediyordu.** En keskin
   örnek `music.audioset_labels`: müzik sayılan AudioSet etiketleri koda
   gömülüydü (`AUDIOSET_MUSIC_LABELS`), konfigdeki liste süstü. Deponun ilk
   değişmezi "hiçbir eşik koda gömülmez" diyor; bu onun ihlaliydi. Aynı
   şekilde `music.separator` yazıyordu ama ayrıştırıcı koda sabitti.
2. **Okunmayan bir anahtarı değiştirmek korpusu yeniden koşturuyordu.**
   Aşama sürümü kendi konfig bölümünün özetini içerdiği için
   `audioset_labels` listesine dokunmak müzik aşamasının sürümünü
   değiştirir, 3.440 saat yeniden ölçülür ve **hiçbir sayı değişmez**.

**Yapılan.** Gerçekten parametre olması gerekenler bağlandı:
`music.audioset_labels` ve `music.separator` artık konfigden okunuyor;
bilinmeyen bir ayrıştırıcı adı sessizce yok sayılmak yerine hata veriyor.
Gerisi çıkarıldı. Bağlanmamış üç bölüm (`dnsmos`, `speaker`, `events`) de
konfigden çıkarıldı: `dnsmos.enabled: true` aşama yokken "açık" görünüyordu
ve politikadaki ölü `dnsmos_ovrl` kuralının (v4'te kaldırıldı) zeminiydi.
Planlar defterde durur, konfig yalnızca uygulananı ilan eder.

Değişiklik ölçümü değiştirmiyor: 12 klipte (müzikli, sınırda ve müziksiz)
`music_score_audioset`, `music_to_speech_db` ve `background_music` işareti
eskisiyle **birebir aynı** çıktı.

**Kodda çürütülmüş varsayılan.** `INAUDIBLE_DB` modül varsayılanı **−30 dB**
kalmıştı; oysa 28 Ağustos kör dinlemesi bu değeri çürütüp konfigi −40'a
çekmişti. Konfigde anahtar unutulsaydı hat, dinlemenin reddettiği eşiği
sessizce kullanacaktı. Üstelik bir test bunu `assert INAUDIBLE_DB == -30.0`
diye **sabitliyordu** — yani eskimiş değeri koruyan bir bekçi vardı. Test
tersine çevrildi: artık koddaki varsayılanların konfigle aynı olmasını
şart koşuyor (`inaudible_db`, `audioset_min`, `separator_screen`,
`audioset_labels`).

**Üç ölü işlev silindi.** `text.turkish.last_vowel` (ünlü uyumu; hiçbir
normalizasyon kuralı kullanmıyor), `text.sentences.split_sentences` (düz
metin sarmalayıcısı; bölütleyici `sentence_spans` kullanıyor),
`base.stage_names`, ayrıca `MusicMeasurer`'ın iki kullanılmayan ince
sarmalayıcısı. Şemada hayalet sütun yok (37 sütun, manifestle birebir).

**Yöntem belgesi eskimişti.** `docs/FEATURES.md` politikayı hâlâ **v4**
olarak anlatıyor, `clip_ratio ≤ 0,002` ve `word_confidence ≥ 0,60`
kurallarını yürürlükteymiş gibi listeliyor ve ikincisi için "şu an inceleme
altındadır" diyordu — oysa ikisi de 30 Ağustos'ta kör dinlemeyle
kaldırılmıştı. Makale bu belgeden beslenmeyecek olsa da politika tarihçesi
oradan okunuyor; v3–v6 zinciri gerekçeleriyle yazıldı. `DESIGN.md`'deki
`events.gate_synthetic` göndermesi de düzeltildi.

**Bekçi.** `tests/test_config.py::test_konfigde_okunmayan_anahtar_yok`
konfigdeki her anahtarın `kiraat/` içinde okunduğunu sınıyor. Denendi:
`export.max_hours_per_channel` geri konunca düşüyor.

**Kütüphane tarafında eskimiş kullanım yok.** Test takımı
`-W always::DeprecationWarning -W always::FutureWarning` ile koşturuldu,
tek bir uyarı çıkmadı. Gerçek koşuda çıkan tek uyarı torchaudio'nun kendi
kaynak ayrıştırıcısından geliyor (`torch.load(weights_only=False)`); bizim
kodumuz değil, ve `requirements.txt` torch/torchaudio'yu 2.5.1'de
sabitlediği için koşuyu etkilemiyor. Torch yükseltilirse önce bu yol
sınanmalı — sabitlemenin koruduğu şey tam da bu.

**Makaleye:** doğrudan malzeme değil; §Yeniden üretilebilirlik bölümünde
"konfig uygulananın tamamını ve yalnızca onu ilan eder" ifadesinin
dayanağı.

## 2026-08-31 — Defter temizliği: geçersiz sayılar damgalandı, geçerlilik dizini eklendi

Defter makalenin tek kaynağı olduğu için içindeki her sayının ya güncel ya
da açıkça "geçersiz" damgalı olması gerekiyor. Bugün baştan sona tarandı.
Kayıtlar silinmedi — bir günlük, o gün ölçüleni olduğu gibi tutar — ama
eskimiş ya da bu depoda üretilmemiş her sayının yanına ne olduğu yazıldı.

**Dışarıdan gelmiş sayılar çıkarıldı.** Korpus büyüklüğü ilk kayıttan beri
bu depoda ölçülmemiş bir rakamla anılıyordu ("2.370 kayıt, 2.942 saat") ve
üç ayrı yerde hız/maliyet tahmininin tabanı olmuştu. Defterin kendi kuralı
bunu yasaklıyor: makaleye giren her sayı burada üretilmiş olmalı. Rakam
çıkarıldı, yerine ölçülen envanter kondu (2.698 kayıt, 3.440,2 saat);
tahminler de bugünkü ölçülmüş hızla (41,5×) yeniden yazıldı. Aynı şekilde
"kanalların medyan kaydı 0,2–2,2 saat" dışarıdan okunmuştu; artık burada
ölçülü (medyan 41,4 dk).

**Önceki veri kümesine göndermeler kaldırıldı.** Üç yerde bir ders "önceki
hatta da böyle olmuştu" diye anlatılıyordu. Dersin kendisi bu deponun kendi
kanıtıyla ayakta duruyor — doğrulanmamış bir ölçü kapı yapılınca elediği
şey "kötü klip" değil "o kanal" oluyor; iki kör dinleme turu bunu burada
gösterdi. Gönderme cümleleri, kanıtı zayıflatmadan çıkarıldı.

**Eskimiş koşular damgalandı.** `sample-25` ve `sample-25b` kayıtlarının
başına, o sayıların hangi hattı anlattığı ve geçerli koşunun `sample-25c`
olduğu yazıldı. Bu önemliydi, çünkü en görünür yerde duran klip sayıları
(12.958 klip, önerilen %78,1) tepe sınırlayıcı kalkmadan ve politika v5–v6
düzeltmeleri yapılmadan önceki hattındı.

**Geçerli örnek koşunun toplu kaydı yokmuş.** `sample-25c`'nin sayıları üç
ayrı kayda dağılmıştı; makalenin §Örneklem bölümü tek yerden okunabilsin
diye toplandı (yukarıdaki kayıt). Toplarken bir şey görüldü ve **açık madde
15** olarak yazıldı: müzik işareti kanallara yığılıyor — `Peri_Mia`
kliplerinin %92,7'si işaretli ve önerilen alt kümesi %6,6'ya düşüyor. Bu,
`clip_ratio` ve `word_confidence` turlarında düşen örüntünün aynısı; müzik
eşiği kör dinlemeden geçmiş tek sinyal olsa da o dinleme bu kanalları
içermiyordu.

**Deney listesi sadeleştirildi.** Kapanmış üç madde tam metinleriyle
duruyordu ve açık işmiş gibi okunuyordu; tek satırlık kapanış notuna
indirildi. Numaralandırma bozuktu (1–9, sonra 11, 12, sonra 10) ve
entrylerin içinde kalmış üç madde (13, 14, 15) listede yoktu. Liste
yeniden yazıldı: on bir açık madde, yerleşmiş bir yöntem (kör dinleme
protokolü, beş tur), dört kapanmış madde.

**Üstte bir geçerlilik dizini var artık.** "Hangi sayı geçerli" başlığı,
makaleye girecek her ölçümü kaynağıyla listeliyor ve geçersizleri ayrıca
sayıyor: bu depoda üretilmemiş sayılar, eskimiş koşular, politikadan düşmüş
üç kural, hiç uygulanmamış ayarlar, dağıtıcı öncesi hız tahminleri.

**Makaleye:** doğrudan malzeme değil; makaleyi yazarken ilk okunacak yer
bu dizindir.

## 2026-08-31 — Literatür taraması genişletildi: katmanlama pratiği, nihai kanıt standardı, venue haritası

30 Ağustos'taki "Alanın yerleşik yöntemi" kaydı altı işin okumasına
dayanıyordu; bugün tarama genişletildi (WenetSpeech4TTS, Hi-Fi TTS,
AutoPrep, MLS/YODAS/SPGISpeech, kalite ölçüleri, metin normalizasyonu,
KazakhTTS/KazakhTTS2, BibleTTS, eşik–çeşitlilik karşılaştırması
arXiv:2510.03111) ve hatla madde madde karşılaştırıldı. Tam rapor ve
künyeler [`docs/LITERATURE.md`](LITERATURE.md) dosyasında; doğrulanamayan
künyeler orada işaretli ve makaleye girmeden tek tek açılacak.

**Ayrılığımız sanıldığından küçük.** 30 Ağustos kaydı "yerleşik hatların
hepsi kalite ölçüsünü kapı yapar" diyordu; bu, kendi modelini beslemek
için veri üretenler (Emilia, AutoPrep, Hi-Fi TTS) için doğru. Paylaşılan
korpus yayımlayan işlerin yerleşik biçimi ise bizimkine yakın:
WenetSpeech4TTS DNSMOS'la Premium/Standard/Basic katmanlarını üçü birden
yayımlar, LibriTTS clean/other'ı etiketli katman olarak sunar, LibriTTS-R
eleme yerine onarım yapar. Bizim katkımız eşiksizlik değil, eşiğin kör
dinlemeyle gerekçelendirilip sürümlü politika olarak ilan edilmesi —
katkı cümlesi böyle kurulacak.

**Nihai kanıt standardı.** Veri makalelerinde kalitenin kanıtı nesnel skor
dağılımı değil, o veriyle TTS eğitip çıktıyı ölçmek: WenetSpeech4TTS her
katmanla ayrı model eğitip CER/SECS/NMOS/SMOS raporlar; ManaTTS ve
KazakhTTS2 MOS verir. Deney listemizde bu yoktu; 12. madde olarak eklendi.
Hangi ölçümlerin üretileceğini geriye doğru belirlediği için düzeneği tam
koşudan önce tasarlanmalı.

**Zamanlama uyarısı: ara ses silinmeden konuşmacı kararı.** Diarization
kayıt düzeyidir ve `work/audio` üzerinde koşar. Tam koşu sonrası ara sesin
silinmesi gündemde; o karar, konuşmacı kümelemenin hatta girip
girmeyeceği kararından önce verilmemeli — silinirse konuşmacı aşaması
için 283 GB'lık prepare yeniden koşar.

**Boşluk sıralaması literatüre göre.** (1) Algısal kalite/SNR sütunları
(açık madde 11; Brouhaha tek geçişte VAD+SNR+C50 verir, tek aşamayla üç
sütun olabilir); (2) konuşmacı bilgisi — standart tabloda konuşmacı sayısı
ve cinsiyet dengesi var, bizde `speaker_id` yok ve `dedupe` kanala
düşüyor; (3) held-out test (deney 5); (4) LUFS — ilkeye uygun asgari adım
normalizasyon değil klip başına ölçüm sütunu. Kanal dengesizliği ise
literatürde eleme sebebi değil; raporlanır, elenmez.

**Emsal ve venue.** En yakın emsaller KazakhTTS2 (LREC 2022) ve ManaTTS
(NAACL 2025); ikisi de "veri kümesi + tarif + eğitilmiş modelle kanıt"
formatında. Venue ailesi Interspeech / LREC / ICASSP-SLT-ASRU / *ACL.

**Makaleye:** §İlgili çalışmalar `docs/LITERATURE.md`'den kurulur (künyeler
doğrulandıktan sonra); katkı cümleleri: gerekçelendirilmiş sürümlü politika,
çok saatlik kaydın sabit bellekle işlenmesi, ayrıştırma tabanlı müzik
ölçümü.

## 2026-08-31 — Uygulanabilir maddeler kapatıldı: eşikler konfige, metin kuralları, LUFS ve DNSMOS sütunları; `sample-25d`

Literatür karşılaştırmasından çıkan boşlukların "şimdi, bu depoda, kulak
gerektirmeden kapanabilir" olanları tek turda kapatıldı; her biri kod +
test, sonra 2 kaynaklık duman koşusu, sonra denetim örnekleminin yeniden
koşusu ile doğrulandı. Commit `75d4607` (kod), `afe1109` (analiz betiği);
`sample-25d` bu temiz commit'ten üretildi.

**Gömülü eşikler konfige taşındı, değerler değişmedi.** Sınır
iyileştirmenin yedi eşiği (`RefineConfig`) yeni `boundaries` bölümüne,
`asr.beam_size` (5) ve müzik AST penceresi (`window_sec` 10,24 /
`hop_sec` 5,0) kendi bölümlerine geçti; `SegmentStage` `boundaries`
bölümünü sürümüne katıyor. "Koddaki varsayılan = konfig" bekçileri
(`tests/test_config.py`) eklendi. Konfigin `SECTIONS` listesindeki dört ölü
bölüm adı (`speaker`, `events`, `export`, eski `dnsmos`) çıktı;
`run_boilerplate`ın konfigden sapmış mükerrer varsayılanları (kodda 3/12,
konfigde 2/24) kalktı, tek kaynak `mine` imzası. Koda gömülü BIRAKILANLAR
ve gerekçesi: `INTERNAL_BREAKS`, `ABBREVIATIONS`, `ORDINAL_FOLLOWERS` dil
verisidir, eşik değil; dağıtıcı öncelikleri ve 32 MB zarf bloğu başarım
ayarıdır, çıktıyı değiştirmez (test altında).

**Metin kuralları (açık madde 7/9).** Harf+rakam belirteçleri TDK harf
adlarıyla okunuşa çevriliyor: "3G" → "üç ge", "F-16" → "fe on altı",
"MI6" → "me ı altı" (ASCII I'nın adı "ı"). Kural bilinçli olarak dar —
yalnızca BÜYÜK harfli, en çok 4 harf + 4 basamak; "mp3", "cm2" gibi küçük
harfli karışımlara dokunulmaz, İngilizce okunan markalar Türkçe harf
adıyla yaklaşıklanır (ASR metninden gerçek okunuş bilinemez, sözleşme bu).
İkinci kural: 1–3 basamaklı sayı + nokta cümle sonu sayılmaz ("1. Naip",
"3. Selim", "100. Yıl"); 4 basamaklı yıllar sınır olarak kalır.
`to_spoken` da özel isim önündeki sıra sayısını okur ("birinci Naip").
`segment` v9. `sentences.py` ve `normalize.py` için doğrudan test dosyaları
yazıldı (daha önce yalnızca `test_segment` üzerinden dolaylıydı).

**Yeni sütunlar.** `clip_qc` v3 klip başına `loudness_lufs` (BS.1770,
pyloudnorm) üretiyor — DESIGN #9'un ölçüm yarısı; sese dokunulmuyor,
normalizasyon kullanıcının. Yeni `dnsmos` aşaması (v1) P.835 SIG/BAK/OVRL
üretiyor; hesap Microsoft'un `dnsmos_local.py` referansıyla birebir (9,01 s
pencere, 1 s adım, kısa klip kendi üstüne yinelenir, ikinci derece polinom
eşleme, pencere ortalaması). Model dosyası depoda (`models/dnsmos/`),
sha256'sı konfigde ve kuruluşta doğrulanıyor; yol sürüme girmiyor, özet
giriyor. **Politika kuralı konmadı** — kanıt yükü kapıdadır.

**`sample-25d`: denetim örneklemi yeni hatla.** Aynı tarif (27 kanal × 3
kayıt × ≤20 dk, 81 kaynak): **13.628 klip / 23,18 saat**, önerilen
**11.285 (%82,8) / 18,97 saat**, politika v6. `verify_columns` HATA YOK
(300 ses örneği). Koşu PC yeniden başlayınca yarıda kaldı ve `done`
kayıtlarından kaldığı yerden sürdü (ASR tekrarlanmadı); bu yüzden bu
koşudan hız ölçümü alınmadı, geçerli hız hâlâ `sample-25c`'nin 41,5×'i.

*Belirlenimcilik.* `beam_size` koda gömülüyken de 5'ti; 81 kaydın ASR
kelime dosyası `sample-25c` ile **bayt bayt aynı** (81/81). Kliplerin
%91,4'ünün `text_raw`ı aynı; farkın tamamı cümle kuralının kaydırdığı klip
sınırlarından.

*Cümle kuralının etkisi (25c → 25d).* Tek belirteçlik "N." klipleri 5 → 0;
0,5 s altı klip 3 → 1; `short` 165 → 158; klip sayısı 13.637 → 13.628.
`text_spoken`da rakam kalan klip 5 → 4 — kalanlar "9x12", "cm2", "cm3"
(küçük harfli birim üstleri, kuralın bilinçli dışında). Harf+rakam
belirteci bu örneklemde hiç geçmedi; kural testle sınandı, veriyle henüz
değil.

*Müzik ölçümünün tekrarı (deney 2, kapandı).* Ayrıştırıcının koştuğu
3.097 klipte Spearman(AudioSet, dB) = **+0,479**. 28 Ağustos'taki +0,799
v1 kliplerinde ve beş banda yayılmış 70 klipte ölçülmüştü; burada evren
eleme eşiğini (0,05) geçen kliplerle sınırlı olduğundan aralık daralması
korelasyonu düşürür. Geçerli sayı budur; v1 sayısı makaleye girmez.
`background_music` 1.774 klip (%13,0).

*Madde 15'in girdisi.* İşaret kanala yığılıyor: `Peri_Mia` kliplerinin
%92,6'sı (önerilen %6,6), `SESLİKİTAPEVİ` %68,4, `sesli-kitaplar` %58,8,
`Pandoramedyaseslikitap` %43,8, `SesliKitaPodcast` %34,7, `kitaplar`
%30,2; on beş kanalda %0–1. Kör dinleme sayfası hazır:
`work/sample-25d/listen-music/index.html`, 36 klip (üç kanal × dört dB
bandı × üç), kanal ve skor gizli, anahtar `key.json`. Karar dinlemeyi
bekliyor.

*`duration / n_words`.* Kelime başına süre medyan 0,506 s, p1 0,349,
p99 0,820, azami 1,495. Kuyruk uyuşmazlık değil başlık/tek kelime
("Shakespeare", "Bölüm 2 Göz Yaşı Havuzu"); hızlı uçta 0,28 s/kelime.
Dağılım dar; LibriTTS'in bu sinyali kapı yaptığı türden bir kuyruk
görünmüyor, dinleme sınaması düşük öncelik.

*LUFS.* n 13.627, medyan −21,5, p5 −29,1, p95 −14,0 (klip düzeyi yayılım
15,1 LU); **kanal medyanları −33,4 … −12,3 LUFS, aralık 21,1 LU** — v1'de
18,4 LU idi. DESIGN #9'un teşhisi bu depoda doğrulandı; sütun artık
yayımlanıyor, seviye kararı alıcının.

*DNSMOS.* SIG medyan 3,56 (p5 3,25 – p95 3,70), BAK 4,10 (3,19 – 4,21),
OVRL **3,28** (2,67 – 3,48). What-if: `dnsmos_ovrl ≥ 3,0` kuralı önerilen
11.285 klipten 962'sini (%8,5) dışlardı ve dışlananlar kanala yığılıyor
(`SESLİKİTAPEVİ` 157, `kitaplar` 99, `ses-arşiv` 95, `OkumaSaati` 87) —
`clip_ratio` ve `word_confidence` turlarında düşen örüntünün aynısı. Kural
konmadı; konacaksa önce bantlara dengeli kör dinleme. WenetSpeech4TTS
katman eşikleri (≥4,0 / ≥3,8 / ≥3,6) burada anlamsız kalıyor: 3,6 üstü
yalnızca 22 klip — o katmanlar P.808 MOS ölçeğinde, bizim OVRL P.835;
doğrudan karşılaştırılmaz, makalede bu ayrım yazılır.

*Maliyet.* Logdan: `dnsmos` **2,07 çekirdek-s/klip**, `clip_qc` 0,10,
`music` 0,11 (GPU). Tam koşuda 1,73 milyon klip ≈ 1.000 çekirdek-saat,
altı işçiyle ~bir hafta. Aşama klip düzeyi olduğu için tam koşuyu
bekletmez ama bu hâliyle tam koşuya girmemeli; deney listesine düştü.

**Makaleye:** §Veri (LUFS ve DNSMOS dağılımları, kanal medyanları
aralığı), §Yöntem (metin normalizasyonu sözleşmesi; eşiklerin tamamının
konfigde ve koşu kaydında olması), §Sınırlar (DNSMOS'un P.835 olduğu ve
katman eşiklerinin taşınamayacağı; harf+rakam kuralının darlığı).

## 2026-08-31 — DNSMOS GPU'ya taşındı (v2): 2,07 s/klip → 13 ms/klip, sayılar üç ondalıkta sabit

Aynı gün açılan madde 13 kapandı: `dnsmos` aşaması onnxruntime'ın CUDA
sağlayıcısına taşındı (`onnxruntime` → `onnxruntime-gpu` 1.23.2). `cuda`
istenip sağlayıcı yoksa aşama HATA verir — sessizce CPU'ya düşmek 160
katlık yavaşlamayı gizlerdi.

**İki bellek çukuru ölçülerek bulundu.** 256 ve 128 pencerelik toplu girdi
cuDNN Conv'da doğrudan reddedildi; 64'lük dilim ise koşunun ortasında
(443. klip) OOM ile düştü — modelin Conv katmanları pencere başına ~73 MB
ara bellek istiyor (64 pencerede tek tampon 4,7 GB) ve değişken dilim
şekilleri BFC arenasını parçalıyor. Çözüm **sabit şekilli dilim**: her
`run` çağrısı tam 16 pencere alır, son dilim sıfırla doldurulur ve çıktısı
atılır — tek şekil, tek tahsis, parçalanma yok. 200 çağrılık değişken yük
sınavı kararlı (2,6–3,6 ms/pencere); arena `kSameAsRequested` ile ~6 GB'da
kalıyor. Tek GPU işçisiyle Whisper/HDemucs yanında sorunsuz; iki GPU
işçisi kararı verilecekse bu 6 GB hesaba katılır.

**Cihaz sıralaması tuzağı.** nvidia-smi'nin PCI sırasında 0 numaralı kart
GTX 1650; CUDA'nın "en hızlı önce" sırasında 0 numara RTX 3090. torch ve
onnxruntime aynı CUDA sırasını kullanıyor — `runtime.device: cuda:0` bu
makinede 3090'dır; her ikisinin de aynı karta indiği bellek artışı
izlenerek doğrulandı.

**Sayısal denklik.** 13.628 klipte CPU (v1) ile GPU (v2) karşılaştırıldı:
azami fark 0,020, kliplerin ~%70'inde tam sıfır, 0,005'i aşan 21–53 klip
(sütuna göre); `recommended` hiçbir klipte değişmedi. Paketleme ölçümü
değiştirmez: dilim sınırı klip ortasından geçerken bile skorlar tek tek
hesaplananla aynı (test altında). Düşen 64'lük koşudan 443 klip "bitti"
kaldı ve yeniden ölçülmedi — dilim boyutu değeri değiştirmiyor.

**Hız.** 13.628 klip, dağıtıcıyla 172 s duvar saati ≈ **13 ms/klip**; tam
koşu kestirimi ~1.000 çekirdek-saatten **~6 GPU-saate** indi. DNSMOS'un
tam koşu engeli kalktı. `verify_columns` HATA YOK; manifest temiz
commit'ten yeniden yazıldı.

**Makaleye:** altyapı ayrıntısı makale malzemesi değil; §Yöntem'e yalnızca
"DNSMOS P.835, referans uygulamayla birebir" cümlesi.

## 2026-08-31 — Kör dinleme: müzik işareti kanal tınısı değil, gerçekten müzik yakalıyor; eşik −40 dB kalır (madde 15 kapandı)

Altıncı dinleme turu: işaretin yığıldığı üç kanaldan (`Peri_Mia`,
`SESLİKİTAPEVİ`, `sesli-kitaplar`) dört dB bandına dengelenmiş 36 klip,
kanal ve skor gizli (`work/sample-25d/listen-music/`). Soru, `clip_ratio`
ve `word_confidence` kurallarını düşüren örüntünün burada da olup olmadığı
idi — değilmiş.

**İşaret ↔ kulak (36 klip).** İşaretli 22 klipte: 12 belirgin + 2 baskın,
7 hafif, yalnız 3 "yok" — işaretlilerin %86'sında kulak da bir şey
duyuyor. İşaretsiz 14 klipte: 11 "yok", 2 hafif, 1 belirgin (kaçan tek
klip dB = −43,6, eşiğin hemen altında). dB bantları kulakla monoton:
−40 altı bantta 7/9 "yok", −40 üstünde müzik oranı bantla artıyor. Sinyal
kanal tınısı değil; işaretin kanala yığılması o kanallardaki müziğin
gerçekten sürekli olmasından.

**Eşik taraması** (kulak-pozitif = belirgin+baskın): −40 dB 13 pozitifin
12'sini yakalıyor, −45 hepsini yakalıyor ama yanlış pozitif eklemeden
değil (korpus genelinde −45…−40 bandını da işaretlerdi); −35 ve üstü
kaçırmaya başlıyor. **Karar: eşik −40 dB'de kalır, kural değişmez** —
politika sürümü aynı (v6).

**Sınırları.** Yanlış pozitif payı %14 (3/22) ve üçü de yüksek AudioSet
skorlu (0,54–0,66); ikisi `SESLİKİTAPEVİ`den — o kanalda dinleyici 12
klibin 8'ine "yok" dedi, işaret payının en şüpheli olduğu kanal bu.
Dinleyici notu: bazı kliplerde ayrımı güçleştiren şey müzik değil
mikrofon/oda ekosu ("mikrofondan kaynaklı eko var, müzik değil").
Kayıt kalitesi artık ayrı sütunlarda görünüyor: üç kanalın `dnsmos_bak`
medyanları korpus medyanının (4,10) altında; eko/oda şüphesi müzik
eşiğinin değil algısal kalite sütunlarının işi. "Hafif" verilen 9 klip
gri bölgedir: işaret onları dışlıyor ve TTS eğitimi için temkinli taraf
budur; sütunlar yayımlandığından kullanıcı −40 yerine kendi eşiğini her
zaman kesebilir.

**Makaleye:** kör dinleme protokolünün altıncı turu; işaretin duyulur
müzikle doğrulanması ve eşiğin dinlemeyle seçilmiş olması §Yöntem'e,
yanlış pozitif payı ve kanal yoğunlaşması §Sınırlar'a.

## 2026-08-31 — Tam koşu öncesi kod incelemesi (2. tur): yedi doğruluk düzeltmesi, muafiyetler belgelendi

Günün bütün değişiklikleri (a437ea7..HEAD) sekiz açıdan incelendi
(satır satır tarama, kaldırılan davranış, çapraz dosya izleme, yeniden
kullanım, sadeleştirme, verimlilik, mimari, CLAUDE.md uyumu). Doğrulanan
ve düzeltilen bulgular:

1. **`boilerplate.min_ratio: null` çökmesi.** Sabahki temizlik
   `float(opts["min_ratio"])` yazmıştı; null (oran eşiğini kapatmanın
   meşru yolu) TypeError veriyordu. Null artık `mine`a olduğu gibi geçer
   (`_mine_kwargs`, test altında).
2. **Doğrulayıcı sınır payını konfigden okumuyordu.** `boundaries`
   bölümü sabahki değişiklikle canlı konfig olunca `verify_columns`ın
   `RefineConfig()` varsayılanından türettiği oversize toleransı ve
   `probe_segment`in varsayılanla iyileştirmesi hattan ayrışabilir olmuştu;
   ikisi de `cfg.refine_config()` okuyor artık.
3. **"Bölüm 5. Ali..." yanlış okuması.** Yeni sıra sayısı kuralı, sayaç
   sözcüğünden sonraki sayıyı da sıra sayısına çevirip cümleyi
   birleştiriyordu ("Bölüm beşinci Ali"). `NUMBER_LABELS` istisnası
   (bölüm, madde, sayfa, …) iki modüle de kondu; basamak sınırı ortak
   sabit oldu (`ORDINAL_MAX_DIGITS`), iki paralel 3 sabiti kalktı.
   Korpusta ölçülen etki şimdilik 0 klip; sınıf olarak gerçekti.
4. **`dnsmos_*` şemada yanlışlıkla zorunluydu.** Okunamayan klipte boş
   kalırlar; `loudness_lufs` gibi isteğe bağlı ilan edildi.
5. **Doğrulayıcının harf+rakam muafiyeti bayattı.** Eski muafiyet bütün
   belirteçleri kapsıyor ve yeni okunuş kuralını denetimsiz bırakıyordu;
   muafiyet artık kuralın kendisiyle (`spell_alphanumeric` None mı)
   hesaplanıyor — doğrulayıcı ile hat tanım gereği ayrışamaz.
6. **Analiz betiği eski manifestte çöküyordu** (`loudness_lufs` yok →
   None biçimleme) ve **dinleme bantlarının üst ucu 0,1 dB'de kapalıydı**
   — müzik konuşmadan gürse klip hiçbir banda düşmüyordu. Üst bant açık
   uçlu yapıldı. Altıncı turda üç kanalda bant dışı kalan yalnızca 2/1.529
   klipti; turun sonucu etkilenmez, gelecek turlar tam kapsar.
7. **Küçük sadeleşmeler.** `Config._dataclass_section` (segment/boundaries
   tek yardımcıda), pyloudnorm ölçeri `lru_cache`, dnsmos'ta ölü pencere
   dalları ve gereksiz kopya kalktı, `dnsmos.model_path` koda gömülü
   mükerrer varsayılanını kaybetti (konfig zorunlu).

**Bilinçli koda gömülü kalanlar (muafiyet listesi genişledi).**
`INPUT_SEC = 9.01` ve 1 s adım DNSMOS **referans uygulama sözleşmesidir** —
konfige almak referanstan sapmaya davet olurdu; harf+rakam kuralının
4 harf / 4 basamak sınırı ile `ORDINAL_MAX_DIGITS = 3` dil kuralı
sabitleridir (INTERNAL_BREAKS/ABBREVIATIONS ailesi). Eşik-konfig ilkesi
ölçüm eşikleri içindir; bu üçü o sınıfta değildir.

**Ertelenen bulgular (mühendislik borcu, davranışı bugün etkilemiyor).**
(a) Aşama listeleri altı yerde elle (CLIP_STAGES, iki import satırı,
PRIORITY, __main__ yardım metni, browse_ui) — kayıt defterinden türetilmeli;
konuşmacı aşaması eklenirken yapılacak. (b) "Klibi çöz+mono+16k" üç
aşamada üç kopya ve okunamayan seste üç farklı davranış (clip_qc işaretler,
dnsmos boş bırakır, music HATA verip koşuyu durdurur) — ortak yardımcı ve
tek sözleşme gerek; music'in davranışı bugünden beri değil, kayda geçti.
(c) dnsmos'ta çözme ile GPU çıkarımı örtüşmüyor (music'teki desen); tam
koşuda ~1–2 GPU-saat, dnsmos zaten ~6 GPU-saat olduğu için ertelendi.
(d) `spearman`/`q` yardımcıları scripts altında kopya. (e) Büyük harf
sınıfı `[A-ZÇĞİÖŞÜ]` inceltmeli harfleri (Â) kapsamıyor — nadir, kayda
geçti. Tamamı 14. madde olarak listede.

**Makaleye:** girmez; inceleme süreci §Yöntem'de tek cümle
("her değişiklik testli, her koşu temiz commit'ten") olarak zaten var.

## 2026-08-31 — Karar: ara ses (`work/audio`) HF yayınına kadar saklanacak

31 Ağustos'taki zamanlama uyarısı ("ara ses silinmeden konuşmacı kararı")
kullanıcı kararıyla kapandı: tam koşunun `work/audio` çıktısı (~283 GB,
prepare'in 24 kHz mono dönüşümleri) **veri kümesi Hugging Face'e
yüklenene kadar silinmez**; silme ancak yayından sonra gündeme gelir.
Böylece konuşmacı kümeleme aşaması (deney 4) eklenmeye karar verilirse
girdisi hazır durur, prepare yeniden koşmaz. Deney 4'ün kendisi (aşamanın
yazılıp yazılmayacağı) hâlâ açık; bu karar yalnızca sıralama riskini
ortadan kaldırır. Disk planına etkisi: koşu sonrası ~283 GB geri
alınmayacak, boş alan hesabı buna göre (bkz. tam koşu öncesi hazırlık).

**Makaleye:** girmez; işletme kararı.

## 2026-08-31 — `music` okunamayan seste koşuyu durdurmaz (v4); tam koşu öncesi son engel kapandı

31 Ağustos incelemesinin ertelenen (b) maddesinin tam koşuyu ilgilendiren
yarısı öne alındı: `music` aşaması okunamayan klipte `sf.read` hatasını
yakalamıyordu ve tek bozuk dosya bütün koşuyu düşürüyordu. 3.440 saatlik
koşuda bu kabul edilemez bir kırılganlık olduğu için sözleşme `dnsmos` ile
eşitlendi: okunamayan (ya da boş) klipte ölçümler boş kalır, işaret
verilmez — `unreadable_audio` işaretinin sahibi `clip_qc` — ve koşu sürer.
`music` v4; şemada üç müzik sütunu (`music_score_audioset`,
`music_to_speech_db`, `music_db_separated`) dnsmos emsalindeki gibi isteğe
bağlı ilan edildi. Test: bozuk bayt dizisi + sağlam klip birlikte işlenir;
düzeltme geri alınınca test LibsndfileError ile düşüyor (teşhis doğru).
Sürüm zinciri gereği tam koşuda `music` zaten sıfırdan koşacağı için ek
maliyet yok. Maddenin kalan yarısı (ortak klip çözücü, üç aşamada tek
davranış) 14. maddede mühendislik borcu olarak duruyor.

**Makaleye:** girmez.

## 2026-08-31 — TAM KOŞU başlatıldı (`work/full-1`)

Kullanıcı onayı alındı ("final koşu için engel yoksa koş"). Koşu öncesi
son durum: music v4 düzeltmesi bu commit'te, bütün testler geçiyor
(1 atlanan), `gpu_stage_concurrency: 1` (dnsmos'un ~6 GB arenası nedeniyle
tek GPU işçisi güvenli taraf), disk 696 GB boş (~283 GB prepare + klipler
sığar; `work/audio` HF yayınına kadar saklanacak, yukarıdaki karar).

Kuru koşu doğrulaması (`--dry-run`): **2.699 kaynak, 27 kanal, 3.440,16
saat** — envanterin ölçülmüş sınırlarıyla birebir. Okunamayan 1 dosya
(seslimakalem, bozuk m4a) koşuda `error` işaretiyle kayda düşecek.

Komut (bu kaydı içeren temiz commit'ten):

    python -m kiraat run --max-sources 0 --work-root work/full-1

Günlük `work/full-1.log`, pid `work/full-1.pid`. Beklenti: sample-25c'nin
41,5× hızıyla ~83 saat duvar saati (≈3,5 gün); dnsmos GPU'da ~6 GPU-saat
ekler. Kesintide `done` kayıtlarından kaldığı yerden sürer (sample-25d'de
doğrulandı). Tam koşudan sonra sırada bekleyenler değişmedi: TTS
değerlendirme düzeneği (deney 12), bölütleme ablasyonu (deney 1),
konuşmacı kararı (deney 4), yayın paketi (deney 6).

**Makaleye:** §Veri sayıları bu koşunun manifestinden gelecek; koşu
bitince toplu kayıt buraya düşülecek.

## 2026-09-03 — TAM KOŞU kullanıcı kararıyla durduruldu (`work/full-1`, 19:22)

Durdurma anında hat: align 811/2391, segment 804/2395, clip_qc
356.268/516.619, music ve dnsmos henüz başlamadı; veritabanında 746.108
klip, bütünlük denetimi temiz. Ana sürece SIGINT gönderildi; işçiler yetim
kaldığı için pid listesiyle tek tek kapatıldı (desenle öldürme yok), GPU
boşaldı, pid dosyası silindi. `done` kayıtları duruyor, koşu kaldığı
yerden sürdürülebilir.

Sebep, aynı gün ölçülen iki bölütleme bulgusu: (1) Whisper yedek
damgalarının geriye atlaması dört uzun kaydı (20,1 saat) çökertiyor —
hizalanmayan rakamlar kabul edilmiş sınırdır, romanizasyona dokunulmayacak,
düzeltme `segment`'e monotonluk kelepçesi ve boş dilim korumasıdır; (2)
künye kesimi cümle ortasında biten/başlayan işaretsiz parçalar bırakıyor
(699 bin klipte 209, %0,03). İkisi de yalnızca `segment` sürümünü taşır;
`align` kayıtları korunur. Bu düzeltmeler ve testleri yazıldıktan sonra koşu
sürdürüldü (aşağıdaki kayıt). Bölütleme tüm kaynaklarda yeniden
üretilmedi: kullanıcı kararıyla `segment` sürümü 9'da bırakıldı ve
yalnızca sınırı gerçekten değişen 30 kaynak yeniden bölütlendi.

## 2026-09-03 — Bölütleme: bozuk kelime damgası artık kaydın tamamını düşürmüyor (iki düzeltme, dört kayıt geri kazanıldı)

Tam koşu 20,1 saat kaybetmişti. Dört kayıt bölütlemede çöküyordu ve ikisi
birbirinden ayrı görünen iki hata mesajı veriyordu; kökleri aynı çıktı.

**Kök.** Rakamlar hizalanmaz — bu 30 Ağustos'ta karara bağlanmış, kabul
edilmiş bir sınırdır ve hizalamayı okunuş metni üzerinden kurmak açıkça
reddedilmiştir (kelime aralığı ile `text_raw` arasındaki birebir karşılık
bozulur, damgalar normalizasyonun doğruluğuna bağlanır). Bu kararın
dokunulmadığı yerde kalan sonuç şudur: hizalanmayan kelimenin damgası
Whisper yedeğine düşer ve Whisper'ın rakam damgaları **geriye atlayabilir**.
1.107 hizalanmış kaynakta ölçüldü: 9.328.387 kelimenin 31.068'i (%0,333)
hizalanmamış ve hepsi sayısal belirteç ("13", "-4", "%100"); geriye atlayan
kelime 644 (%0,0069) ve bunlar **307 kaynağa (%27,7) yayılmış**. Atlamanın
medyanı 0,03 s, p90 0,43 s, en büyüğü 18,4 s.

**İki çökme noktası.**

1. `segment` klibin uçlarını ilk ve son kelimeden okuyordu. Aradaki bir
   kelime geriye atladığında klip ters uzunluk alıyordu ve muhafız
   `sifir/eksi sureli klip` hatası veriyordu. En küçük gerçek örüntü iki
   kelime: `Anna` 15736,19'da başlıyor, `13` 15734,81'de bitiyor →
   `Clip(start=15736.04, end=15735.06)`. Düşen kayıtlar src00249, src00558.
2. `boundaries.find_boundary_ex` bağlam penceresini `t_next + 1.0` ile
   kuruyordu. `t_next` önceki klibin bitişinden önce olduğunda `ctx_hi <
   ctx_lo` olup dilim boşalıyor ve `np.percentile` "index -1 is out of
   bounds for axis 0 with size 0" veriyordu. Düşen kayıtlar src00613,
   src00891. İlginç olan şu: aynı fonksiyonun bir üst satırı (`hi`) bu
   durumu `max(t_next, t_end)` ile zaten hesaba katıyordu, bağlam penceresi
   atlanmıştı.

**Düzeltme.** `segment.py`'de yeni `_extent(words, a, b)` yardımcısı klip ve
cümle uçlarını kelime aralığının tamamından alıyor (en küçük başlangıç, en
büyük bitiş); sıralı girdide davranış birebir aynı. `boundaries.py`'de
bağlam penceresi de `hi` gibi `max(t_next, t_end)`e dayanıyor ve dilimin boş
kalmaması güvenceye alındı. Rakam sözleşmesine, hizalamaya ve eşiklere
dokunulmadı.

**Testler (`tests/test_nonmonotonic_words.py`).** İlk yazdığım bölütleme
testi düzeltme geri alındığında **düşmedi**, yani senaryoyu üretmiyordu;
28 Ağustos'ta öğrenilen kural burada bir kez daha işe yaradı (düzeltmenin
testi geri alınca düşmüyorsa teşhis kanıtlanmamıştır). Test, gerçek veriden
çıkarılan iki kelimelik en küçük örüntüyle yeniden yazıldı. Son durum:
`_extent` geri alınınca bölütleme testi düşüyor, bağlam penceresi düzeltmesi
geri alınınca sınır testi `IndexError` ile düşüyor. Tüm takım 160 geçti.

**Gerçek veride doğrulama.** Çöken dört kayıt düzeltmeli kodla temiz
bölütleniyor ve sınır düzeltmesinden geçiyor: 2.094 + 3.124 + 3.003 + 3.121
= **11.342 klip geri geliyor**. Sağlam veride düzeltme etkisiz: yayımlanmış
11 kaynak (2.292 klip) birebir aynı üretildi. Korpus geneli: 746.108
yayımlanmış klipten yalnızca **41'inin sınırı değişiyor**, 30 kaynakta
(%0,006). O 41 klipte bir kelimenin sesi klip penceresinin dışında kalmış,
metni içindeydi.

**Sürüm kararı.** `segment` sürümü 9'da bırakıldı ve bunun yerine etkilenen
30 kaynağın `segment` 'bitti' kaydı silindi; sürüm yükseltmek 1.107 kaynağı
ve 746 bin klibi yeniden ölçtürürdü, bu yol aynı veri durumunu 55.749 klip
yeniden ölçümüyle (%7,5) veriyor. `replace_clips` eski klip kimliklerinin
'bitti' kayıtlarını kendisi sildiği için bayat ölçüm riski yok (kod bu
tuzağı zaten belgeliyor). Çöken dört kaydın `error` alanı temizlendi; bozuk
m4a dosyası (src01754) dokunulmadan `error` ile kaldı.

**Yeniden başlatma (19:41).** Veritabanının yedeği alındıktan sonra koşu
aynı komutla ve iki GPU işçisiyle sürdürüldü. Devam doğru: `prepare` ve
`asr` "yapılacak kaynak yok", `align` 1.579 kaynak (2.698 − 1.119),
`segment` 1.621 kaynak (2.698 − 1.077, içinde geri kazanılan 4 ve yeniden
bölütlenecek 30). Aşama sürüm dizgeleri değişmedi (`segment=9+d7dc4baa`),
yani hiçbir biten iş eskimedi.

**Beklenen kazanç.** Çökme yalnızca uzun kayıtlarda görülüyordu: 3,9 saatten
uzun 174 kaydın bölütlenen 73'ünde 4 çökme (%5,5). Kalan 105 uzun kayıtta
aynı oranla ≈6 çökme ve ≈35 saat kayıp bekleniyordu; düzeltme bunu kesiyor.

### Aynı gün ölçülen, henüz kapanmayan iki madde

**Açık madde 16 — künye kesimi işaretsiz parça bırakıyor.**
`_cut_at_boilerplate` künye aralığı bir cümlenin içine düştüğünde cümleyi
üçe bölüyor; yalnızca ortadaki parça `boilerplate` işareti alıyor, baş ve
kuyruk parçaları işaretsiz kalıyor ve `recommended_subset`'in işaret
kuralından geçiyor. Politikayı geçen 699.334 klipte ölçüldü: küçük harfle
başlayan 75 kuyruk parçası ve cümle sonu noktalaması olmayıp ardından künye
klibi gelen 134 baş parçası, toplam **209 klip (%0,03)**; tam korpusta ~550
beklenir. Karşılaştırma: `forced_split` işaretli 11.220 klip de küçük harfle
başlıyor ama politika onları eliyor, o muafiyet belgeli. v1'in aynı kusuru
%9,4'tü. `tests/test_segment.py` bunu yakalayamıyor, çünkü dosyada künyeli
yol hiç kurulmuyor ve sınama yalnız klip BAŞINA bakıyor — cümle ortasında
BİTEN klipler sınamanın kör noktası. Düzeltme önerisi: künye kesiminden
doğan parçalara ayrı bir işaret (ör. `boilerplate_split`) ve politikanın
`flag_absent` listesine eklenmesi; `segment` sürümünü taşır.

**Açık madde 13 hâlâ açık ve ölçeklendi — cümle başı çöp hizalama.**
Tam koşuda `align_score_min < 0,01` olan klip 16.590 (%2,24) ve bunların
15.684'ü önerilen alt kümede. Ölçülen sonucu var: bu kliplerin %17,2'sinde
baş sessizliği 0,5 s'yi aşıyor (2.061 klip), normal kliplerde bu oran
%0,30 — yani sınır gerçekten kayıyor, 57 kat zenginleşme. Sebep hâlâ
bilinmiyor; rakamlarla ilgisi yok (defterdeki ölçümde çöp hizalamaların
yalnız %4'ü parça başındaydı).

### Rakam sınırının yayımlanan veriye etkisi (ölçüldü, sorun değil)

Rakamın ucunda olduğu klip, politikayı geçenlerin %0,72'si (5.083 klip).
İlk kelimesi rakam olan klipte baş sessizliği medyanı 0,220 s (normal
0,060), p99 2,556 s (normal 0,380); son kelimesi rakam olanlarda son
sessizlik p90 0,336 s (normal 0,000) ve `speech_ratio` medyanı 0,889
(normal 0,980). Yani sınır kesilmiyor, gevşiyor: zarf düzeltmesi kaymanın
çoğunu emiyor, kalan aykırılıkları `speech_ratio ≥ 0,60` kuralı yakalıyor.
Yayımlanmış veride üst üste binen klip 0, `end <= start` klip 0 — muhafız
klip üretmek yerine koşuyu kestiği için bozuk klip dışarı çıkmamıştı.

## 2026-09-03 — Dağıtıcı: ikinci GPU işçisi ve align'ın işçi içi darboğazı

Tam koşuda align darboğazdı. Tek GPU işçisiyle ölçüm (kesintiden önceki
3 saat): 69 kaynak/saat, **94 ses-saati/saat**, işçi %100 dolu. İkinci GPU
işçisiyle (`--gpu-workers 2`): 8 saatlik pencerede **91 ses-saati/saat**,
yani kazanç ~1,3×, beklenen 1,8× değil. Sebep nvidia-smi örneklemesinde
görünüyor: iki işçiyle GPU kullanımı 20 örnekte ortalama ~%25.

Darboğaz işçi içi. Bir kaynakta (src00003, 19 dk, işçi ayarıyla OMP 3)
ölçülen dağılım: model ileri geçişi %56, **`F.merge_tokens` %28**,
`forced_align` %10, pencere okuma+yeniden örnekleme %5. `merge_tokens`
skor tensörü GPU'da kaldığı için her belirteç aralığında ayrı senkron
yapıyor; skorları önce CPU'ya alınca aynı kaynak 109× yerine **188× gerçek
zamanda** hizalanıyor ve aralık/skor çıktısı özdeş çıkıyor. Bu düzeltme
uygulanmadı (koşu ortasında kod değişikliği yapılmadı, deney listesine
yazıldı); uygulanırsa `align` sürümü değişmez, çünkü çıktı aynıdır.

İkinci gözlem: iki align işçisinin tuttuğu GPU belleği 10,5 saatte işçi
başına ~7 GB'dan ~9,7 GB'a tırmandı (toplam 19,5 GB / 24 GB). Yeniden
başlatma bunu sıfırladı (11,1 GB). Klip aşamaları (demucs + DNSMOS) aynı
işçilerde başlayınca 24 GB'a sığmaması olası; klip işi hatası dağıtıcıda
koşuyu durdurduğu için o noktada `--gpu-workers 1`e dönmek gerekebilir.

Disk: ham veri NTFS üzerinde bir SATA SSD'de ve %90 doluluğu geçmişti;
I/O bekleme %27 ölçüldü ama bekleyenler CPU işçileri (segment, clip_qc),
GPU işçileri değil. 3 Eylül'de kök diskte 138 GB (Docker yapı önbelleği,
kullanılmayan imajlar, altı conda ortamı, HF önbelleği) boşaltıldı.

## 2026-09-04 — Tam koşu: kaynak aşamaları bitti, klip aşamaları koştu; ölçülen hızlar ve disk

Kaynak tarafı 4 Eylül 22:11'de kapandı: `align` 1579/1579, `segment`
1621/1621, veritabanında **1.840.404 klip** (2.699 kaynak, 3.431 ses-saati).
Yeniden başlatmadan (3 Eyl 19:41) bu yana tek hata satırı yok; 3 Eylül'de
yazılan monotonluk kelepçesi ve boş dilim koruması, daha önce dört uzun
kaydı düşüren durumu tekrarlatmadı.

Klip aşamalarının ilk ölçülen hızları (22:11–23:31 penceresi, 12 CPU + 2 GPU
işçisi):

| aşama | havuz | hız | 1,84 M klip için |
|---|---|---|---|
| `clip_qc` | CPU | 153 bin klip/saat | ~7 sa (kalan 1,05 M) |
| `music` | GPU | 88 bin klip/saat (24,5 klip/s) | ~18 sa |
| `dnsmos` | GPU | 284 bin klip/saat (v2 ölçümünden) | ~6,5 sa |

`music` ve `dnsmos` aynı GPU kuyruğunda seri gittiği için klip tarafının
GPU kolu ~25 saat; CPU kolu ondan önce boşalır. `music` v4'ün iki GPU
işçisiyle hızı, tek işçili `sample-25d` ölçümünden (9,3 klip/s) beklenenin
üstünde çıktı.

3 Eylül kaydındaki iki endişe ölçülerek kapandı. (1) GPU belleği: klip
aşamaları align işçileriyle aynı süreçlerde başladı ve toplam **22,9 / 24,6
GB**'da durdu — `--gpu-workers 1`e dönmek gerekmedi, ama pay dar. (2) Disk:
bölütlemenin son partisi 32 GB yazdı (168 → 136 GB boş), tahminle birebir.
`work/full-1` şimdi 535 GB: ara ses 284, klipler 246 (1,64 M klipte ortalama
159 KB), align 2,7, asr 1,5, veritabanı 1,4 GB. Kalan üç aşama ses yazmıyor,
`export` de yalnızca manifest yazıyor; koşunun geri kalanı diskte birkaç GB
tutar.

Bütünlük denetimi: `done` tablosunda öksüz satır yok, `clip_qc` ve `music`
için "bitti" işaretli her klibin metriği yerinde (sırasıyla 797.488 ve
237.155 satır, eşleşmeyen sıfır). Aşama sürümleri üç oturumda da aynı
kaldı, dolayısıyla kesintiler hiçbir klibi yeniden ölçtürmedi.

## 2026-09-05 — `dnsmos` 17 s'den uzun klipte düşüyordu: pencere diliminde kayan nokta

Tam koşuda `dnsmos` aşaması `ValueError: all input arrays must have the same
shape` ile durdu. Sebep pencerelemedeki dilim sonu: referans uygulamadan
alınan `int((i + 9,01) * SR)` ifadesi, 9,01 ikilik tabanda tam durmadığı
için `i = 7`'den başlayarak yirmi bir indiste bir örnek aşağı yuvarlanıyor
ve 144.160 yerine 144.159 örneklik bir pencere üretiyor; `np.stack` de
farklı boydaki pencereleri yığamıyor. Sekizinci pencere ancak 17 s'den uzun
kliplerde çıktığı için hata daha önce görünmedi: `sample-25d` örneklemi de
`tests/test_dnsmos.py`'nin 2/12 saniyelik durumları da eşiğin altındaydı.
Depodaki 1.840.404 klibin **3.876'sı (%0,21)** 17 s'den uzun, en uzunu
159,2 s; ilkine denk gelene kadar koşu ilerledi ve orada düştü.

Düzeltme, dilimi `audio[i * SR : i * SR + need]` ile almak. Referans
uygulama bu kısa pencereleri sessizce atıyordu (`continue`); burada tam
boy alınıp ölçüme giriyorlar. 17 s'den kısa klipte iki yol örnek örnek
özdeş olduğu için daha önce yazılmış hiçbir dnsmos sütunu değişmez —
zaten `done` tablosunda `dnsmos` satırı yok, aşama hiç klip
tamamlamamıştı — ve aşama sürümü 2'de kalır.

Gerileme testi `test_uzun_klipte_pencereler_tam_boy`: 17, 30, 60 ve 121
saniyelik seste pencere sayısı 1 s adımını izlemeli ve her pencere tam
144.160 örnek olmalı. Eski dilimleme geri konduğunda test tam da koşudaki
hatayla düşüyor.

## 2026-09-05 — Tam koşu sağlık denetimi (music %43'te): iki ölçüm kusuru

Koşu `work/full-1` 05:18'de yeniden başlatıldıktan sonra hattın durumu ve
o ana kadar üretilen veri denetlendi. Depoda 2.699 kaynaktan 1.840.404 klip
(3.105,7 saat) var; `prepare`/`asr`/`align`/`segment` 2.698 kaynakta,
`clip_qc` 1.840.404 klibin hepsinde bitti, `music` 790.911 klipte (%43,0)
koşuyor, `dnsmos` henüz başlamadı — dağıtıcı klip işlerini aşama-öncelikli
sıraya koyduğu için bütün `music` işleri `dnsmos`tan önce gidiyor. Son bir
saatlik ölçülen hız 22,4 klip/s; kalan `music` ~13 saat, ardından `dnsmos`
13 ms/klip ile ~3,3 saat. Diskte 136 GB boş, 162 test geçiyor.

**Müzik ölçümü kanal düzeyinde doğru davranıyor.** Ayrıştırıcı ve işaret
oranları kanala göre beklendiği gibi ayrışıyor: müziksiz kanallarda
(dinleyiniz 102.418 klip, kitapdinle, OkumaSaati) işaret %0,0; müzikli
kanallarda Peri_Mia %59,6, SESLİKİTAPEVİ %56,4, Pandoramedyaseslikitap
%49,0. Madde 15'te yanlış pozitif üreten MuratKaraOfficial2021'de kliplerin
%16,1'i ayrıştırıcıya girmiş ama yalnızca %1,0'ı işaretlenmiş — AudioSet
eşiği (0,3) tam da konması istenen işi yapıyor. Biten 784.393 klibin
hepsinde `background_music` işareti yayımlanan iki sütundan yeniden
hesaplandı, sıfır tutarsızlık. Biten kısımda işaret oranı %11,55.

**Kusur 1 — `music`in AudioSet penceresi klibin kuyruğunu ölçmüyor.**
`MusicMeasurer.prepare` pencereleri `range(0, len - window + 1, hop)` ile
üretiyor; `window = 10,24 s`, `hop = 5 s`. 15 s'lik bir klipte bu tek bir
pencere veriyor (76.161 < 80.000), yani son 4,76 s hiç ölçülmüyor ve skor
pencereler üzerinden azami alındığı için yalnızca kuyrukta duyulan müzik
görünmez oluyor. Depoda 121.049 klip (%6,6) pencereden uzun; ölçülmeyen
kuyruk etkilenen kliplerde ortanca 1,64 s, p90 4,01 s, en çok 5,0 s —
toplam 62,9 saat (korpusun %2,02'si). 10,3 s'den uzun 300 kliplik
örneklemde son pencereyi ekleyip ölçtüm: skor 16 klipte (%5,3) 0,05'ten
fazla yükseliyor, en çok +0,304; `background_music` işareti 1 klipte
(0,233 → 0,444) dönüyor. Uzun kliplere oranlanınca ~400 klipte işaret
değişimi demek. Bu, 5 Eyl'de `dnsmos`ta kapatılan pencere kusurunun aynı
sınıfı; `music` payı daha büyük çünkü adım 1 s değil 5 s. Düzeltme
`prepare`e son pencereyi (`len - window`) eklemek; ölçüm değişeceği için
aşama sürümü 4 → 5 olmalı, bu da biten 790 bin klibin yeniden koşması
demek (~23 saat). Karar kullanıcının.

**Kusur 2 — `trailing_silence_sec` yapısal olarak sıfır.** Sütun
kliplerin %99,7'sinde 0,000. Sebep VAD ayarı: `min_silence_duration_ms`
300 ms, oysa bölütlemenin kuyruk payı `trail_pad_sec` 250 ms. Silero son
konuşma bölgesini kapatacak kadar uzun bir sessizlik bulamayınca bölgeyi
sesin sonuna kadar uzatıyor, `duration - segments[-1]["end"]` de sıfır
çıkıyor. Sessizlik gerçekte orada: 15 kliplik örneklemde çerçeve
enerjisiyle ölçülen kuyruk sessizliği 0,14–0,24 s (ortanca 0,20 s), ve
`min_silence_duration_ms=100` ile koşulan VAD 0,044–0,080 s buluyor
(pay çıkınca kalan). `leading_silence_sec` de 100 ms'lik `speech_pad_ms`
kadar eksik ölçüyor (ortanca 0,06 s; enerjiyle 0,12 s) ama sıfıra
çökmüyor. Sütun politikada kural değil, yalnızca yayımlanıyor — yine de
yayımlandığı hâliyle yanlış. `clip_qc` CPU aşaması olduğu için yeniden
koşması ucuz.

**Bilinen açık madde doğrulandı:** künye kesiminin bıraktığı işaretsiz
cümle-ortası parçalar tam depoda 137 klip (küçük harfle başlayan 27.483
klibin geri kalanı `forced_split`/`gap_split`/`boilerplate` işaretli,
yani önerilen alt kümenin dışında). 116'sı Peri_Mia kanalında.

**Kayıp kaynaklar:** `prepare` 1 kaydı ffprobe hatasıyla (seslimakalem),
`segment` 4 kaydı düşürdü — ikisi boş kelime dizisi, ikisi sıfır/eksi
süreli klip. 2.699 kaynağın 5'i, %0,19.

## 2026-09-05 — İki ölçüm kusuru kapatıldı: `music` v5, `clip_qc` v4; koşu 06:53'te durduruldu, göçle sürdü

Sabahki sağlık denetiminin bulduğu iki kusur da düzeltildi. Koşu 06:53'te
`SIGINT` ile durduruldu (`music` 796.583 klipte), düzeltmeler yazıldı,
sürüm göçü uygulandı ve koşu yeniden başlatıldı.

**`music` v4 → v5: AST penceresi klibin kuyruğunu da ölçüyor.**
`MusicMeasurer.prepare` pencereleri `range(0, n - window + 1, hop)` ile
üretiyordu (`window` 10,24 s, `hop` 5 s). 15 s'lik bir klipte bu tek
pencere veriyor (76.161 < 80.000) ve son 4,76 s hiç ölçülmüyordu; skor
pencereler üzerinden azami alındığı için yalnızca kuyrukta duyulan müzik
görünmez oluyordu. Dilim seçimi `window_starts` yardımcısına taşındı ve
son pencere sesin sonuna yaslanarak ekleniyor.

Ölçülen etki (aynı gün, 10,3 s'den uzun 300 klip, iki dilimleme yan yana):
skor 16 klipte (%5,3) 0,05'ten fazla yükseliyor, en çok +0,304;
`background_music` işareti 1 klipte (0,233 → 0,444) dönüyor. Depodaki
121.049 uzun klibe oranlanınca ~400 klipte işaret değişimi.

**Sürüm göçü, çünkü kliplerin %93,4'ünde ölçüm değişmiyor.** Klip
penceresinden kısaysa iki uygulama da tek ve aynı pencereyi üretiyor
(`range(0, 1, hop) == [0]`, son pencere koşulu tutmuyor). Bu, dnsmos
kaydındaki muhakemenin aynısı; ama orada olduğu gibi iddiaya güvenilmedi,
ölçüldü: 200 kısa klip yeni kodla yeniden ölçüldü, `music_score_audioset`,
`music_to_speech_db` ve `music_db_separated` **200/200 birebir aynı**
çıktı. `scripts/migrate_music_v5.py` bunun üzerine süresi 10,19 s'den kısa
(pencere − 0,05 s güvenlik payı) 743.696 klibin `done` satırını v5'e
taşıdı; yeniden ölçülecek 52.887 klip kaldı — 22,4 klip/s'de ~40 dakika,
tam yeniden koşunun ~23 saati yerine.

**`clip_qc` v3 → v4: uç sessizlikler kendi paysız VAD geçişinden.**
`trailing_silence_sec` kliplerin %99,7'sinde 0,000 çıkıyordu. Sebep
sütunun kendisinde değil, hangi VAD geçişinden okunduğundaydı: politika
geçişi `speech_pad_ms: 100` ile bölgeleri iki yandan uzatıyor ve
`min_silence_duration_ms: 300`, bölütlemenin kuyruk payından
(`segment.trail_pad_sec: 0,25`) uzun olduğu için silero son konuşma
bölgesini kapatacak sessizliği hiç bulamayıp bölgeyi sesin sonuna kadar
uzatıyordu. Sessizlik gerçekte oradaydı: 15 kliplik örneklemde çerçeve
enerjisiyle (20 ms çerçeve, tepe − 35 dB) ölçülen kuyruk sessizliği
0,14–0,24 s.

`vad` bölümüne dokunulmadı — o bölümü `prepare` ve `asr` de okuyor,
eşiğini oynatmak ASR bölgelerini değiştirir ve bütün kaynak aşamalarının
sürümünü eskitirdi. Bunun yerine uç sessizlikler `clip_qc` bölümündeki
`edge_speech_pad_ms: 0` ve `edge_min_silence_duration_ms: 50` ile koşulan
ikinci bir geçişten okunuyor. Aynı 15 klipte yeni sütunlar: baş 0,032–0,512
(enerjiyle 0,00–0,50), son 0,096–0,180 (enerjiyle 0,14–0,24). `speech_ratio`
ve `internal_silence_sec` politikada kapı olduğu için eski geçişten
gelmeye devam ediyor; 15 klibin 15'inde ikisi de bit-bit aynı kaldı.
Maliyet ikinci VAD geçişi, yani `clip_qc`in 1.840.404 klipte yeniden
koşması (50,8 klip/s, ~16 CPU-saat) — CPU havuzu `music`/`dnsmos` GPU
işiyle paralel çalıştığı için duvar saatine yansıması küçük.

**Gerileme testleri.** `test_pencereler_klibin_kuyrugunu_da_olcer` altı
klip boyunda son pencerenin sesin sonuna dayanmasını,
`test_pencereden_kisa_klipte_dizi_degismedi` kısa klipte dizinin eski
uygulamayla özdeş kaldığını (göçün dayanağı),
`test_uc_sessizlik_gecisi_kuyruk_payini_olcebilir` konfigde uç geçişin
paysız ve eşiğinin kuyruk payından kısa olmasını sınıyor. Üçü de
düzeltmeler geri konduğunda düşüyor; bütün paket (165 test) geçiyor.

**CPU'lu ve GPU'lu klip aşamaları aynı anda koşmamalı (12 çekirdekte).**
Düzeltmelerden sonra koşu üç aşamayı birden açtı ve ikisi de yavaşladı:
`clip_qc` yalnızken 50,8 klip/s, `music` yalnızken 23,2 klip/s, birlikte
28,9 ve 8,1 (yük ortalaması 28, çekirdek 12). Sebep `music`in GPU'yu
besleyen ön-yükleme iş parçacıklarının (çözme, yeniden örnekleme, log-mel)
`clip_qc` işçileriyle aynı çekirdekleri paylaşması. Birlikte tahmini
duvar saati ~38 saat, sıralı ~24 saat; koşu `--stages music dnsmos` ile
yeniden başlatıldı, `clip_qc` onlar bitince ayrı koşacak. Dağıtıcı
aşamaları CPU/GPU havuzlarına ayırıyor ama havuzların çekirdek rekabetini
modellemiyor — sample-25'te görünmemişti, çünkü orada `clip_qc` `music`
başlamadan bitiyordu.

**GPU işçileri aşama modellerini bırakmıyor; `dnsmos` aynı koşuda
`music`in ardına konmamalı.** `scheduler._STAGES` aşama nesnesini işçi
başına bir kez kuruyor ve hiç yıkmıyor (model yüklemesi pahalı olduğu
için); `music` koştukça iki GPU işçisi 3090'ın 24.576 MiB'ının 23.969'unu
tutar hâle geldi (3,4 saat sonra ölçüldü, çoğu torch'un ayırıcı havuzu).
`dnsmos`un ONNX arenası (~6 GB, 31 Ağu kaydı) torch'un havuzunun dışında
ayrıldığı için `music` bitip sıra `dnsmos`a geldiğinde aynı işçilerde
bellek yetmezdi. Koşu bu yüzden `--stages music` ile yeniden başlatıldı
(taze işçilerde 5.481 MiB); `dnsmos` bitişinde ayrı koşacak. Aşamaların
`teardown`'ı dağıtıcı yolunda hiç çağrılmıyor — madde 14'ün (mühendislik
borcu) altına giriyor.

**Açık kalan.** Künye kesiminin bıraktığı 137 işaretsiz cümle-ortası klip
düzeltilmedi: kesimi onarmak `segment`i ve 2.698 kaynağın hepsini yeniden
koşturur, 137 klip için orantısız. Karar, dışa aktarım yazılırken metni
küçük harfle başlayan kliplere `mid_sentence` işareti koymak ve işareti
politikanın `flag_absent` listesine eklemek — tespit metinden yapılıyor,
yeniden üretim gerektirmiyor ve gelecekteki kesim kusurlarına karşı da ağ
oluyor.

## 2026-09-06 — Klip aşamaları kapandı: `clip_qc`, `music`, `dnsmos` 1.840.404 klipte tam

Tam koşunun klip tarafı bitti. Üç aşamanın da `done` sayısı 1.840.404 ve
veritabanındaki klip sayısına eşit; `dnsmos` metriği olmayan tek klip yok.
`music` 5 Eylül 19:11'de (8,5 saat, ortalama 28 klip/s), `dnsmos` 6 Eylül
04:20'de (6,30 saat, **81,1 klip/s = 292 bin klip/saat**) kapandı. dnsmos'un
ölçülen hızı 31 Ağustos'ta sample-25d'den kestirilen 284 bin/saat ile
birebir; koşuda tek hata satırı yok.

5 Eylül'de düzeltilen pencereleme çökmesi üretimde doğrulandı: 17 s'den
uzun 3.876 klibin 3.876'sı skorlandı, en uzunu (159,2 s) dahil
(`sig 3,479 / bak 3,669 / ovrl 2,991`).

Korpus genelinde DNSMOS P.835 dağılımı — makalenin ilk depo-içi kalite
sayıları:

| ölçüt | ortalama | p05 | p50 | p95 | en düşük | en yüksek |
|---|---|---|---|---|---|---|
| `dnsmos_sig` | 3,528 | 3,24 | 3,56 | 3,71 | 0,76 | 3,90 |
| `dnsmos_bak` | 3,968 | 3,24 | 4,09 | 4,21 | 0,89 | 4,31 |
| `dnsmos_ovrl` | 3,208 | 2,69 | 3,27 | 3,49 | 0,96 | 3,74 |

Kliplerin **%83,57'si** `dnsmos_ovrl ≥ 3,0`. Bu bir kapı DEĞİL: sayı
yalnızca sütun olarak duruyor, `recommended_subset` politikası v6'da
dnsmos kuralı yok ve kör dinleme denetiminden geçmeden konmayacak. Alanın
yerleşik eşiğinin bu korpusta neyi eleyeceğini göstermesi bakımından
kaydediliyor.

Koşu koşulu olarak not: `dnsmos` 280 W güç kapağı altında koştu. Kart
(RTX 3090) geçmişte kısa devre görmüş olduğu için 5 Eylül 22:31'de
`nvidia-smi -pl 280` uygulandı; ölçülen etki 318 → 270 W, fan %96 → %73,
sıcaklık 74,5 → 72,8 °C, iş çıkarma kaybı %6 (82,5 → 77,5 klip/s).
Anlık 450 W'lık tepe güçler kayboldu.

Sırada `export`: hattın son aşaması ve ses yazmıyor, yalnızca manifest ile
koşu kaydı üretiyor.

## 2026-09-06 — TAM KOŞU BİTTİ: manifest yazıldı (`work/full-1/manifests`)

`export` 06:23'te tamamlandı ve hattın tamamı kapandı. Manifest
`clips.jsonl` 2,5 GB, yanında `run.json` koşu kaydı: commit `aa5f410`,
çalışma ağacı temiz, izlenmeyen dosya yok — bu manifest commit'ten yeniden
üretilebilir.

Koşunun sayıları:

| | |
|---|---|
| kaynak | 2.699 (1'i okunamadı: seslimakalem, bozuk m4a) |
| kanal | 27 |
| klip | 1.840.404 / **3.105,70 saat** |
| önerilen alt küme (politika v6) | 1.486.240 klip / **2.480,51 saat** |

Önerilen alt küme kliplerin %80,8'i, saatlerin %79,9'u. Kaynak envanteri
3.440 ses-saatiydi; bölütlemeden 3.105,7 saat çıkması (%90,3) sessizlik,
künye kesimi ve cümle sınırı dışında kalan artıkların payıdır.

Dışlama sebepleri (klip başına birden çok işaret olabildiği için sebep
kümesi olarak sayıldı; %0,1'in üstündekiler):

| sebep | klip | pay |
|---|---|---|
| `background_music` | 194.246 | %10,55 |
| `duplicate` | 62.508 | %3,40 |
| `forced_split` | 44.983 | %2,44 |
| `short` | 15.137 | %0,82 |
| `internal_silence_sec>1.0` | 12.757 | %0,69 |
| `background_music,duplicate` | 5.127 | %0,28 |
| `oversize` | 4.229 | %0,23 |
| `speech_ratio<0.6` | 2.412 | %0,13 |
| `gap_split` | 2.446 | %0,13 |

Yani havuzu asıl daraltan tek başına müzik işareti; onun ardından
yinelenen metin geliyor. Kopya kararı şimdilik kanal anahtarıyla verildi —
`speaker_id` yok, konuşmacı aşaması (deney 4) bağlanınca yeniden koşacak
ve `duplicate` payı değişebilir.

Önerilen alt kümedeki ilk kanallar: seslikitaplarmavi 539,0 sa,
BirDinle 438,5 sa, dinleyiniz 223,0 sa, ses-arşiv 142,1 sa,
sess-Seslikitap 141,1 sa, ZubeyirSener 137,7 sa. 27 kanalın hepsi alt
kümede temsil ediliyor — v1'de doğrulanmamış bir sınıflandırıcının kanal
çeşitliliğini silmesi tam olarak burada tekrarlanmadı.

**Makaleye:** §Veri sayıları artık bu koşunun `run.json`'ından gelir;
"yeniden koşulmalı" işaretli hiçbir sayı kalmadı.

## 2026-09-06 — Yineleme kuralı ölçüldü ve keskinleştirildi: aynı metnin ayrı okuması yineleme değildir

Kullanıcı kuralı netleştirdi: aynı metin farklı bir okumayla geçiyorsa
prozodi çeşitliliğidir ve tutulur; yineleme, metnin aynı **ve** ölçülen
değerlerin aynı olmasıdır. Karar vermeden önce manifest üzerinde ölçüldü
(`scripts/probe_dedupe.py`, 1.840.404 klip):

| tanım | yineleme sayılan klip |
|---|---|
| eski anahtar (metin + kanal) | 72.839 |
| ölçülen **bütün** değerler birebir aynı (kuralın harfi) | **0** |
| ses ölçümleri birebir aynı (süre+LUFS+RMS+tepe), kanal içinde | 592 |
| ses ölçümleri birebir aynı, kanal fark etmeksizin | 598 |
| süre 0,1 s / LUFS 0,1 dB'ye yuvarlanmış | 15.752 |

İkinci satır kuralın harfiyen uygulanamayacağını gösteriyor: kanalların
her bölüme koyduğu jenerik cümle (`bizimkütüphane`, "Kitapların büyüsü
kumaşlarda hayat buluyor.") üç bölümde de aynı ses — süre 3,12 s, LUFS
−12,88, RMS −12,67, tepe −0,05 birebir — ama `word_confidence` 0,98 /
0,96 / 0,981 ve `leading_silence_sec` 0,128 / 0,028 farklı, çünkü bunlar
sesin değil klibin çevresinin ölçümü. Son satır ise fazla gevşek:
"Hayır."ın 0,70 ve 0,74 saniyelik iki ayrı okuması aynı kovaya düşüyor,
yani korunması istenen şeyi eliyor.

Kullanıcı kararı: **ses ölçümleri birebir aynı, kanal fark etmeksizin.**
Kanal anahtardan çıktı, çünkü ölçümler tutuyorsa aynı kaydın kopyasıdır ve
hangi kanalda durduğu bunu değiştirmez. `dedupe` artık `speaker_id`
sütununu da beklemiyor; konuşmacı aşaması (deney 4) bu kararın önkoşulu
olmaktan çıktı.

Manifestteki etkisi: yineleme işareti **72.839 → 576 klip**, önerilen alt
küme **1.486.240 → 1.547.494 klip** (+61.254) ve **2.480,51 → 2.575,22
saat** (+94,71). Kalan 576 kopyanın 453'ü tek kanalda (`seslimakalem`)
toplanıyor — o kanalın bölüm jeneriği. 150 klibin ses kimliği eksik
(okunamayan ses); onlar yineleme aranmadan geçiliyor ve kayıtta
sayılıyorlar.

Manifest bu kuralla yeniden üretildi: `run.json` commit `11278f2`, temiz
ağaç. Politika sürümü değişmedi (v6) — değişen `duplicate` işaretinin
tanımı, alt küme kuralı değil.

## 2026-09-06 — BÖLÜTLEME ABLASYONU (madde 1): cümle hizalı kesim, sessizlik hizalı kesime karşı

Makalenin ana sonucu bu depoda ölçüldü. Aynı kayıtlar, aynı kelime zaman
damgaları, aynı süre ayarları; değişen tek şey kesimin nerede yapıldığı.
Cümle kolu tam koşunun ürettiği kliplerdir (veritabanından okundu); taban
kol `kiraat/segment_vad.py` ile üretildi — silero VAD'ın konuşma bölgeleri
aradaki sessizliklerde kesilir, tavanı aşan tek bölge tavanda sert kesilir.
Örneklem kanal dengeli: 27 kanaldan 206 kayıt, **240,5 saat**
(`scripts/ablate_segmentation.py --per-channel 8`).

| ölçüm | cümle hizalı | sessizlik hizalı |
|---|---|---|
| klip | 141.379 | 76.466 |
| saat | 240,54 | 254,18 |
| cümle ortasından başlayan | 1.967 (**%1,39**) | 10.943 (**%14,31**) |
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
kullanıcı onları ayırt edemez, çünkü sessizlikte kesen bir hattın elinde
kırığı gösterecek bir sinyal yoktur.

Kusur kanala göre değişiyor ve hiçbir kanalda kaybolmuyor: taban kolda
kırık başlangıç oranı **%7,0 ile %35,0** arasında (en kötüsü `seslimakalem`,
en iyisi `OkumaSaati`), cümle kolunda **%0,00 ile %5,02** arasında.

İki yan bulgu. (1) Sessizlik hizalı kesim daha çok saat üretiyor (254,2 ve
240,5) ama neredeyse yarısı kadar klip (76,5 bin ve 141,4 bin): klipler iki
kat uzun ve %14,7'si süre tavanına dayanıyor — yani tavan, cümle değil,
kesim noktasını belirliyor. (2) Ortalama hizalama güveni iki kolda aynı
(0,944 ve 0,946), ama klip başına **en düşük** kelime güveninin ortalaması
cümle kolunda belirgin yüksek (0,732 ve 0,647): sessizlikte kesilen klipler
kenarlarında daha çok kötü hizalanmış kelime taşıyor, ki kesimin kelimenin
ortasına düşmesinin beklenen sonucu bu.

**Makaleye:** §Bölütleme'nin ana tablosu budur ve tamamı bu depoda üretildi.
Ölçüm dosyası `work/full-1/ablation/segmentation.json` (kaynak başına
döküm dâhil).

## 2026-09-06 — Değerlendirme bölmesi kuruldu (madde 5): kayıt düzeyi, kanal dengeli, sızıntı sıfır

Korpusun train/dev/test bölmesi yoktu; kuruldu (`kiraat/split.py`,
`scripts/make_splits.py`) ve sızıntı denetimiyle birlikte manifestin yanına
yazıldı.

Bölme **kayıt düzeyindedir**: bir kaydın klipleri tek bölmeye girer, yani
değerlendirme modelin hiç duymadığı bir kayıt üzerinde yapılır. `test` ve
`dev` **kanal dengelidir** (kanal başına eşit süre hedefi), çünkü korpusun
kanal payları çok dengesiz ve değerlendirme kümesi o dengesizliği taşırsa
raporlanan sayı iki kanalın sayısı olur.

Kurarken iki kusur ölçülüp düzeltildi. (1) Kayıtlar saatlerce sürdüğü için
bütün olarak alınınca 10 saatlik hedef **26 saate** çıkıyordu; dev/test
artık kanal başına saat hedefine indiriliyor ve hedefi aşan klipler
`train`'e GEÇMİYOR (geçseydi aynı kaydın klipleri iki bölmeye düşer, bölmenin
tek garantisi giderdi), kullanılmadan bırakılıyor. (2) Üç kayıtlık iki kanal
(`bizimkütüphane`, `KitaplarinKedisi`) eğitimden **tamamen düşüyordu**;
artık kanalın klipli kayıtlarından en az biri `train`'de kalıyor ve kotası
en açık bölme sıradaki kaydı alıyor (önce test'i doldurmak, küçük kanalın
dev'de hiç görünmemesi demekti).

Sonuç (önerilen alt küme üzerinden, politika v6):

| bölme | klip | saat | kayıt | kanal |
|---|---|---|---|---|
| train | 1.512.448 | 2.517,08 | 2.579 | 27 |
| dev | 5.750 | 9,54 | 40 | 27 |
| test | 5.473 | 9,30 | 45 | 27 |

Sızıntı denetimi: kayıt sızıntısı **0** (kurulum gereği, yine de sınanıyor),
metin sızıntısı temizlik öncesi test 2.263 / dev 2.723 klip — bunlar
`train` ile birebir aynı cümleyi taşıyordu ve değerlendirme kümesinden
düşürüldü; temizlik sonrası kalan sızıntı **0**. `train` dokunulmadı.

Eksik kalan: test kümesinin elle doğrulanması. Kullanıcı makineye fiziksel
erişemediği için (PC Ordu'da) dinleme turu şimdilik yapılamıyor; küme
kurulu ve denetimi temiz, ama "elle doğrulanmış" sıfatını hak etmesi için
o tur gerekiyor.

## 2026-09-06 — Konuşmacı kümeleme (madde 4): eşik veriden çıktı, kanal ≠ konuşmacı ölçüldü

v1 küme sayısını 64'te sabitlemiş ve tavan dolmuştu. Burada önce eşiğin
nereden geleceği ölçüldü (`scripts/probe_speaker.py`, ECAPA-TDNN
`speechbrain/spkrec-ecapa-voxceleb`): 27 kanaldan 105 kayıt, kayıt başına
8 klip (≥3 s, işaretsiz), klip gömmeleri kosinüsle karşılaştırıldı.

| dağılım | çift | p05 | p50 | p95 |
|---|---|---|---|---|
| kayıt içi (klip–klip) | 2.940 | 0,560 | 0,742 | 0,853 |
| aynı kanal (kayıt–kayıt) | 153 | 0,131 | 0,872 | 0,940 |
| farklı kanal (kayıt–kayıt) | 5.307 | 0,053 | 0,179 | 0,420 |

İki dağılım temiz ayrışıyor: eşit hata noktası **0,483** ve oradaki hata
**%1,9**. Küme sayısı verilmeden, bu eşikle ortalama bağlantılı birleştirme
(`scripts/cluster_speakers.py`): 105 kayıt → **31 küme**, en büyüğü 8 kayıt,
6 küme tek kayıtlık, kenar payı medyanı 0,507 ve **negatif kenar paylı kayıt
yok**.

İki bulgu doğrudan tasarıma dokunuyor. Birincisi, aynı kanal dağılımının
p05'i 0,131: **kanal konuşmacı değildir** — 27 kanalın 8'i birden çok
konuşmacı barındırıyor. Bu, yineleme anahtarından kanalı çıkarma kararını
(aynı gün) bağımsız olarak destekliyor. İkincisi, 31 kümenin 9'u birden
çok kanala yayılıyor: aynı seslendiren birden çok kanalda yayımlıyor,
dolayısıyla kanal dengesi konuşmacı dengesi değildir ve bölmenin konuşmacı
sızıntısı ancak bu sütun bağlanınca denetlenebilir.

Ölçüm 105 kayıtlık bir örneklemdir; tam korpusta (2.699 kayıt) tekrarlanıp
sütun olarak bağlanması sırada. Toplu çıkarımın tek tek çıkarımla farkı da
ölçüldü: kosinüs benzerliği en kötü 0,99981, en büyük bileşen farkı 0,0043
— küme kararına etkisiz, ama gömme yayımlanırsa kayda geçmeli.

## Koşulacak deneyler

Makalenin dayanacağı ölçümlerden henüz yapılmamış olanlar. Her biri
tamamlandığında yukarıya tarihli bir kayıt olarak taşınır ve buradan düşer.
Kapanmış maddelerin gerekçesi kendi tarihli kaydındadır; burada yalnızca
tek satırlık kapanış notu durur.

**Açık.**

1. **Bölütleme ablasyonu** — aynı ham kayıtlar üzerinde VAD tabanlı kesim ile
   cümle hizalı kesim; cümle bütünlüğü, süre dağılımı, hizalama güveni.
   Makalenin ana sonucu.
2. ~~Müzik ölçümünün ölçekli tekrarı~~ — 31 Ağu 2026, kapandı (aşağıda).
3. **Hizalama güveni geçerlemesi** — kelime başına hizalama olasılığının
   transcript doğruluğuyla ilişkisi; insan referanslı küçük bir örneklemde
   CER ile karşılaştırma.
4. **Konuşmacı kümeleme** — aşama yazılacak; küme sayısının veriden çıkması,
   kayıt-içi tutarlılık ve küme kenar payının raporlanması. `dedupe` bunu
   bekliyor (şimdilik kanal anahtarına düşüyor).
5. **Değerlendirme bölümü** — kayıtları eğitimle paylaşmayan, metin örtüşmesi
   sıfırlanmış, kanal dengeli ve elle doğrulanmış bir test kümesinin
   kurulması ve betimlenmesi. Bölme (train/dev/test) ve sızıntı denetimi
   henüz hiç yok.
6. **Kelime düzeyi damga ve kaynak tablosunun yayımı** — `words` sütunu
   (asr + align damgaları) ve kaynak düzeyi ölçümler; yayın paketiyle.
7. ~~Metin normalizasyonu: harf+rakam belirteçleri~~ — 31 Ağu 2026,
   kapandı (aşağıda).
8. **Şablon künye madenciliği** — kelimesi kelimesine n-gram, "<yazar>'ın
   <kitap> adlı kitabından" gibi değişken yuvalı kalıpları bulamıyor. Sabit
   iskelet + yuva madenciliği ya da künye sözlüğüyle cümle düzeyinde işaret;
   kör dinlemeyle doğrulama.
9. **Açık madde 13 — cümle başı kısa sözcüklerde çöp hizalama.** 245 kelime,
   289 klip (%2,12); sebep bilinmiyor, parça sınırı hipotezi elendi.
   `align_score` yayımlanacağı için ya açıklanmalı ya sınırı belgelenmeli.
10. ~~Açık madde 15 — müzik işaretinin kanal yığılması~~ — 31 Ağu 2026,
    kapandı (aşağıda): işaret gerçek müziği yakalıyor, eşik −40 kalır.
11. **Literatürden gelen sütunlar — kalanı.** DNSMOS ve LUFS sütunları
    31 Ağu'da bağlandı. Kalan: klip başına dil kimliği (model seçimi
    ister); `dnsmos_ovrl`in bantlara dengeli kör dinlemesi (what-if: ≥3,0
    kuralı önerilenin %8,5'ini, kanala yığılarak dışlardı — kural ancak bu
    dinlemeden sonra); `duration / n_words` dinlemesi düşük öncelik
    (dağılım dar, kuyruk başlıklardan).
12. **Korpusla TTS eğitip değerlendirme — nihai kanıt.** Alanın standardı
    (31 Ağu kaydı): önerilen alt küme ve bütün korpusla ayrı ayrı model
    eğitip MOS/CMOS, CER/WER ve konuşmacı benzerliği raporlamak; politika
    ve katmanlamanın kanıtı aynı deneyden çıkar. Düzenek tam koşudan önce
    tasarlanmalı.
13. ~~DNSMOS maliyeti~~ — 31 Ağu 2026, kapandı (GPU'ya taşındı, aşağıda).
14. **İnceleme artıkları (mühendislik borcu)** — 31 Ağu inceleme kaydındaki
    ertelenenler: aşama listelerinin kayıt defterinden türetilmesi
    (konuşmacı aşamasıyla birlikte), ortak klip çözücü (okunamayan ses
    sözleşmesi 31 Ağu'da eşitlendi: üç aşama da işaretle/boş bırak-geç,
    music v4 artık koşuyu durdurmuyor; ortak çözücü yardımcısı hâlâ yok),
    dnsmos önyükleme örtüşmesi, scripts'teki kopya yardımcılar. Ölçüm üretmez, deney değil;
    sıradaki aşama eklenirken kapatılır.

**Yöntem olarak yerleşmiş.**

- **Kör dinleme protokolü** — kanalı ve skoru gizleyen dinleme sınaması
  kuruldu ve altı tur koşuldu (müzik eşiği ×2, sınır kesimi ×2,
  `clip_ratio`, `word_confidence`). Politikaya girecek her yeni sinyal
  için tekrarlanır; kanıt yükü kapıdadır, veride değil.

**Kapandı.**

- ~~Müzik işaretinin kanal yığılması (madde 15)~~ — 31 Ağu 2026; 36 kliplik
  kör dinlemede işaretlilerin %86'sında kulak da müzik duydu, işaretsizlerin
  11/14'ü temiz; eşik −40 dB'de kaldı, politika v6 değişmedi.
- ~~DNSMOS maliyeti~~ — 31 Ağu 2026; GPU'da sabit şekilli 16'lık dilim,
  13 ms/klip, sayılar üç ondalıkta CPU ile aynı, tam koşu kestirimi
  ~6 GPU-saat.
- ~~Müzik ölçümünün ölçekli tekrarı~~ — 31 Ağu 2026; 3.097 depo klibinde
  Spearman +0,479, v1 sayısı (+0,799) geçersiz.
- ~~Metin normalizasyonu: harf+rakam ve tek başına sıra sayısı~~ — 31 Ağu
  2026; TDK harf adlarıyla okunuş, 1–3 basamaklı sayı+nokta cümle sonu
  değil; "N." klipleri 5 → 0.
- ~~`word_confidence` kuralı için dinleme denetimi~~ — 30 Ağu 2026, politika
  v6; 30 klipte 29 metin birebir doğru, kural kaldırıldı.
- ~~`clip_ratio` eşiği~~ — 30 Ağu 2026, politika v5; kör dinlemede 25/25
  "eğitime girsin", kural kaldırıldı.
- ~~Künye kesiminin cümle artığı ve kayıt başı büyük harf~~ — 30 Ağu 2026,
  kullanıcı kararı; küçük harfle başlamak kesim kusuru değil, doğrulayıcıda
  bilgi satırı.
- ~~Açık madde 14, uzun kayıtta bellek~~ — 30 Ağu 2026; zarf bloklu,
  bölütleme ve hizalama diskten okuyor, 14,92 saatlik kayıt uçtan uca koştu.
