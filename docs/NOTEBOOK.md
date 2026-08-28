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
