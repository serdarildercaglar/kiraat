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

---

## 2026-08-28 — Korpusun adı ve kapsamı

Ad `kiraat`; "sesli okuma" anlamındaki *kıraat* sözcüğünden. Makalede KIRAAT,
depo `kiraat`, veri kümesi kimliği `kiraat-turkish-read-speech` olarak
planlandı. Ayırt edici adın makalede, tarif edici kimliğin arama
görünürlüğünde işe yaraması amaçlandı.

Ham malzeme, Türkçe sesli kitap, sesli edebiyat ve sesli makale yayınlayan
herkese açık YouTube kanallarından derlenmiş 2.370 kayıt, toplam 2.942 saat.
Kaynakların telif durumu temizlenmemiştir; yayın politikası ve kaldırma
yolu, veri kümesi kartında ayrıca ele alınacak.

**Makaleye:** §Korpus, §Etik ve lisans.

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
0,40 dk; toplam 5,5 dk → **10,9× gerçek zaman**, 2.942 saat için ≈ 11 gün.
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
Toplam 5,5 → 1,95 dk/saat. **Tam korpus 2.942 saat ≈ 4 gün** (önce 11).
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
P.835 (BAK; tasarımda zaten `dnsmos_ovrl` planlı), pyannote/brouhaha (SNR +
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
değişiyor (v1 tabanından okundu): tam kayıt alınsaydı "kanal başına 3
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

Koşu 13:31–14:26, **54 dakikada 24,7 saat ses ≈ 27× gerçek zaman**
(sample-5b'de 31× ölçülmüştü; fark müzik aşamasının payı — bu örneklemde
müzikli klip oranı yüksek). Aşama süreleri: prepare 5 dk (~290×), ASR
21 dk (~71×), hizalama 7 dk, bölütleme 6 dk, clip_qc 5 dk, müzik 11 dk.
Tam korpus (2.942 saat, v1 tabanı) bu hızla ≈ 110 saat ≈ 4,5 gün.

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
bölümlerinin başına "bağlanmadı" notu düşüldü; `speaker` yokluğunda dışa
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

## Koşulacak deneyler

Makalenin dayanacağı ölçümlerden henüz yapılmamış olanlar. Her biri
tamamlandığında yukarıya tarihli bir kayıt olarak taşınır.

1. **Bölütleme ablasyonu** — aynı ham kayıtlar üzerinde VAD tabanlı kesim ile
   cümle hizalı kesim; cümle bütünlüğü, süre dağılımı, hizalama güveni.
   Makalenin ana sonucu.
2. **Müzik ölçümü** — yukarıdaki deneyin bu depodaki klipler üzerinde
   tekrarı, daha büyük örneklemle.
3. **Hizalama güveni geçerlemesi** — kelime başına hizalama olasılığının
   transcript doğruluğuyla ilişkisi; insan referanslı küçük bir örneklemde
   CER ile karşılaştırma.
4. **Konuşmacı kümeleme geçerlemesi** — küme sayısının veriden çıkması,
   kayıt-içi tutarlılık ve küme kenar payının raporlanması.
5. **Kör dinleme protokolü** — politikaya girecek her sınıflandırıcı için,
   kanalı ve skoru gizleyen dinleme sınaması. Hiçbir sinyal bu sınamadan
   geçmeden kural olamaz.
6. **Değerlendirme bölümü** — kayıtları eğitimle paylaşmayan, metin örtüşmesi
   sıfırlanmış, kanal dengeli ve elle doğrulanmış bir test kümesinin
   kurulması ve betimlenmesi.

7. **`word_confidence` kuralı için dinleme denetimi** — `browse_ui.py` ile
   `word_confidence<0.35` süzgeci, en düşük 30 klip; transcript gerçekten
   yanlış mı? Sonuca göre kural kaldırılır ya da eşik indirilir (politika v3).
8. **Kelime düzeyi damga ve kaynak tablosunun yayımı** — `words` sütunu
   (asr + align damgaları) ve kaynak düzeyi ölçümler; HF export aşamasıyla.
9. **Metin normalizasyonu: harf+rakam belirteçleri** — "MI6", "M5", "3G"
   okunuşa çevrilmiyor (`to_spoken`); ve tek başına sıra sayısı ("… 1.
   Naip …") ayrı cümle sayılıp 0,1 s'lik klip oluyor. İkisi için kural ve test.
11. **Künye kesiminin cümle artığı ve kayıt başı büyük harf** — künye
    ifadesi cümle ortasında bitince kalan parça ("sizlerle …") küçük harfle
    başlayan klip oluyor (sample-25'te 3); Whisper kaydın ilk kelimesini
    büyük harfe çevirmiyor (1). İlkine işaret, ikincisine `to_spoken`
    öncesi ilk harf düzeltmesi; test.
12. **`clip_ratio` eşiği ölçülen büyüklüğe göre gevşek** — `clip_ratio max:
    0.002` kuralı hiçbir yapılandırmada tek bir klip elemedi (sample-25b
    0/12.958; limitleyicisiz koşu 0/102), çünkü gözlenen azami değer 7×10⁻⁵.
    Tepe sınırlayıcı kalktıktan sonra bile ölü. Kırpık kliplerin gerçekten
    hangi `clip_ratio` bandında olduğu dinlemeyle saptanıp eşik oraya
    konmalı, ya da kural kaldırılmalı.

10. **Şablon künye madenciliği** — kelimesi kelimesine n-gram, "<yazar>'ın
    <kitap> adlı kitabından" gibi değişken yuvalı kalıpları bulamıyor
    (sample-15'te 5 kanalda 0 ifade). Sabit iskelet + yuva madenciliği ya da
    künye sözcük sözlüğüyle cümle düzeyinde işaret; kör dinlemeyle doğrulama.