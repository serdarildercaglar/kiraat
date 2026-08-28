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

---

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
