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
10. **Şablon künye madenciliği** — kelimesi kelimesine n-gram, "<yazar>'ın
    <kitap> adlı kitabından" gibi değişken yuvalı kalıpları bulamıyor
    (sample-15'te 5 kanalda 0 ifade). Sabit iskelet + yuva madenciliği ya da
    künye sözcük sözlüğüyle cümle düzeyinde işaret; kör dinlemeyle doğrulama.