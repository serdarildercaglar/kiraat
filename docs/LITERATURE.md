# TTS veri hazırlama literatürü ve kiraat'ın durumu

> İÇ BELGE — makale malzemesi değildir. Buradaki künyeler ilgili çalışmalar
> bölümüne kaynaklık eder ama makaleye girmeden her biri birincil kaynaktan
> tek tek doğrulanır; "doğrulanamadı" işaretli olanlar özellikle. Bu depoda
> üretilmemiş hiçbir sayı buradan makaleye taşınmaz.
>
> 31 Ağustos 2026'da yapılan literatür taramasının ve hat analizinin tam
> hâli. Defterdeki 30 Ağustos "Alanın yerleşik yöntemi" kaydının devamıdır;
> o kayıttaki karşılaştırmaları tekrarlamaz, genişletir.

## 1. Alanın yerleşik şablonu

"Found data"dan (sesli kitap, podcast, web sesi) TTS korpusu üreten hatların
güncel iskeleti Emilia-Pipe'ta (arXiv:2407.05361; genişletilmiş sürüm
Emilia-Large, arXiv:2501.15907) somutlaşıyor: standardization → source
separation → speaker diarization → VAD ile bölütleme (3–30 s) → ASR →
kalite filtreleme. Resmî uygulamadaki araçlar: UVR-MDX-NET-Inst_HQ_3
(ayrıştırma), pyannote 3.1 (diarization), Silero (VAD),
WhisperX/faster-whisper (ASR), DNSMOS P.835 (kalite).

TTS'e özgü hatlar bu şablondan iki yerde ayrılır. Birincisi segmentasyon:
LibriTTS (Zen vd., Interspeech 2019, arXiv:1904.02882), GigaSpeech
(arXiv:2106.06909) ve ManaTTS (NAACL 2025, arXiv:2409.07259) sessizlikte
değil cümle sınırında keser; saf VAD kesimi ASR kökenli hatların mirasıdır
ve Emilia bunun kusurunu süre bandı ve birleştirme kurallarıyla yamar.
WenetSpeech4TTS (Ma vd., Interspeech 2024, arXiv:2406.05763) ise ASR
korpusunu TTS'e çevirirken "kesik kelime" sorununu açıkça hedefler: aralığı
0,55 s'den dar ve konuşmacı benzerliği 0,65'ten yüksek komşu segmentleri
birleştirir, sınırları kelime kesmemek için 0,5 s'ye kadar genişletir.

İkincisi filtreleme: kendi modelini beslemek için veri üreten hatlar
(Emilia, AutoPrep — ICASSP 2024, arXiv:2309.13905 —, Hi-Fi TTS) boru hattı
içinde sabit eşikle eler; paylaşılan korpus yayımlayan işlerin yerleşik
biçimi ise skoru üretip veriyi katmanlamaktır. En net örnek
WenetSpeech4TTS'in DNSMOS P.808 katmanları: Premium (≥ 4,0; 945 saat),
Standard (≥ 3,8; 4.056 saat), Basic (≥ 3,6; 7.226 saat) — üçü de
yayımlanır. LibriTTS'in clean/other ayrımı ve LibriTTS-R'nin (Koizumi vd.,
Interspeech 2023, arXiv:2305.18802) "eleme yerine onarım" hamlesi (aynı
klipler Miipher ile temizlenir, hiçbiri atılmaz) aynı ailedendir.
Eşik–çeşitlilik dengesini doğrudan ölçen yeni bir karşılaştırma da var
(Di Bernardo vd., arXiv:2510.03111): eşik yükseldikçe veri azalıyor ve
homojenleşiyor; değerlendirme hem nesnel metriklerle hem eğitilmiş TTS
çıktısıyla yapılıyor.

## 2. Teknik yapı taşlarının künyeleri

**Segmentasyon ve hizalama.** Montreal Forced Aligner (McAuliffe vd.,
Interspeech 2017), CTC-segmentation (Kürzinger vd., SPECOM 2020), WhisperX
(Bain vd., arXiv:2303.00747 — Whisper damgaları güvenilmez, ayrı fonem
modeliyle zorlamalı hizala), torchaudio CTC forced alignment API
(TorchAudio 2.1, arXiv:2310.17864; MMS'in 1.100+ dilli hizalayıcısı).
Hizalayıcıların 2026 durum değerlendirmesi: arXiv:2606.18466 (defterdeki
30 Ağu kaydında özetlendi: hizalayıcı skoru modelin kendine güvenidir,
doğrulukla karıştırılmaz, örneklemle elle denetlenir).

**Kalite ölçüleri.** DNSMOS P.835 (Reddy vd., ICASSP 2022,
arXiv:2110.01763; SIG/BAK/OVRL), NISQA (Mittag vd., Interspeech 2021,
arXiv:2104.09494), SQuId (Sellam vd., arXiv:2210.06324; 65 locale'de
doğallık — venue doğrulanamadı), Brouhaha (Lavechin vd., ASRU 2023,
arXiv:2210.13248; tek geçişte VAD + SNR + C50 oda akustiği). Bant genişliği
bir seçim ölçütü olarak Hi-Fi TTS'te (Bakhturina vd., Interspeech 2021,
arXiv:2104.01497): sinyal bandı ≥ 13 kHz ve SNR ≥ 32 dB. Transcript
doğrulama ASR'la yeniden tanıyıp WER/CER veya güven skoru eşiklemektir:
GigaSpeech XL'de WER ≤ %4, küçük kümelerde %0; WenetSpeech4TTS
Paraformer-large güven skoru kullanır.

**Metin tarafı.** Sproat & Jaitly (2016) ve Zhang, Sproat vd.
(Computational Linguistics 45, 2019) normalizasyonun klasik hattı; üretimde
WFST/Pynini tabanlı NeMo (I)TN (Interspeech 2021, arXiv:2104.05055).
Noktalama/büyük harf geri kazanımı derlemesi: Păiș & Tufiș,
arXiv:2111.10746. SPGISpeech (arXiv:2104.02014) hedef etiketin en baştan
"fully formatted" (noktalamalı, biçimli) olmasını savunur; LibriTTS'in "hem
ham hem normalize metni dağıt" kararı normalizasyonun kayıplı ve
sürümlenebilir olduğunun kabulüdür.

**Ölçekli ASR kökenli öncüller.** MLS (Pratap vd., Interspeech 2020,
arXiv:2012.03411), GigaSpeech (Interspeech 2021), YODAS (Li vd., ASRU
2023, arXiv:2406.00899; CTC hizalamayla etiketli/etiketsiz katman).

**İngilizce dışı emsaller.** KazakhTTS (Interspeech 2021) ve KazakhTTS2
(Mussakhojayeva vd., LREC 2022, arXiv:2201.05771; 271 saat, 5 konuşmacı,
MOS 3,6–4,2; saatler kadın/erkek ayrı raporlanır) Türk dilleri için en
yakın emsal. ManaTTS (Fetrat vd., NAACL 2025) Farsça ~86–114 saat, CC-0;
cümle bölütleme + düşük kaynaklı diller için hizalama yöntemi + hizalama
ASR'ını sınamak için ayrı test kümesi; Tacotron2 eğitip MOS 3,76'yı doğal
sesin 4,01'iyle yan yana koyar — "veri kümesi + tarif" formatının iyi
örneği. BibleTTS (Meyer vd., Interspeech 2022, arXiv:2207.03546) 10 Afrika
dili, 48 kHz; hizalamaların bir alt kümesi elle denetlenir.

**Venue haritası.** Bu metodoloji makaleleri ağırlıkla Interspeech, LREC,
ICASSP/SLT/ASRU ve son yıllarda *ACL ana konferanslarında (ManaTTS'in
NAACL örneği) çıkıyor; TACL'de veri kümesi makalesi nadir.

**Raporlama standardı.** Veri makalelerinin yerleşik tablosu: toplam saat;
konuşmacı sayısı ve cinsiyet dengesi; klip süresi dağılımı; örnekleme
hızı/bant; kalite dağılımı (DNSMOS histogramı ya da SNR/bant eşikleri);
transcript doğruluğu (WER tavanı veya elle denetlenen alt küme); lisans.
Doğrulama yöntemi olarak elle/kör denetim ve dinleme testleri raporlanır.

**Kalitenin nihai kanıtı.** Fiilî standart, o veriyle TTS modeli eğitip
çıktıyı ölçmek: WenetSpeech4TTS VALL-E ve NaturalSpeech 2 eğitip CER, SECS
(konuşmacı gömme benzerliği), NMOS ve SMOS'u katman katman raporlar;
ManaTTS ve KazakhTTS2 MOS verir; Emilia sesli kitap verisine karşı
"anlaşılırlık eşit + doğallık üstün" savını kullanır. Nesnel skor
dağılımları tamamlayıcıdır, kanıtın kendisi değil.

**Doğrulanamayanlar.** Emilia ve AutoPrep yazar listeleri, Emilia'nın
venue'sü (SLT 2024 olması muhtemel), SQuId'in venue'sü, MMS makalesinin
arXiv numarası, Emilia-Pipe'ın kesin DNSMOS/dil-güven eşikleri. Makaleye
girmeden birincil kaynaktan açılıp bakılacak.

## 3. Hattın literatürle örtüştüğü yerler

Kiraat'ın iki değişmezi alanın vardığı yerin kendisidir.

Cümle sınırında kesim, LibriTTS'in "speech is split at sentence breaks"
kararıyla aynı taraftadır ve v1'de ölçülen %9,4'lük kırık başlangıç,
literatürün VAD kesimine yönelttiği eleştirinin sayısal karşılığıdır.
`kiraat/segment.py`'deki uygulama literatürdeki çoğu hattan incelikli:
klitik birleştirme, kısaltma/sıra sayısı ayrımı, künye kesimi, enerji
zarfıyla sınır iyileştirme ve "hiçbir kelime kaybolmaz" test sözleşmesi.
WenetSpeech4TTS'in sınır genişletmeyle çözmeye çalıştığı "kesik kelime"
sorunu burada baştan üretilmiyor.

Ölçüm–karar ayrımı, paylaşılan korpuslardaki katmanlama pratiğinin en
disiplinli hâli. WenetSpeech4TTS katmanları yayımlar ama katman eşiklerinin
seçimini gerekçelendirmez; politika v5/v6 kararları (kör dinlemeyle 536
klibin geri kazanılması, `word_confidence` kuralının 30 kliplik dinlemeyle
kaldırılması) alanın önerdiğinin ötesinde, denetlenebilir bir süreçtir.
`ClipStage.validate_output`'un karar sütununu hata sayması,
arXiv:2510.03111'in nicelleştirdiği kalite–çeşitlilik dengesini yapısal
olarak alıcıya bırakır.

Diğer örtüşmeler: 24 kHz kararı LibriTTS'le aynı ve ölçülen 15,7 kHz bant
medyanı Hi-Fi TTS'in ≥ 13 kHz seçim ölçütünün üstünde. MMS_FA ile zorlamalı
hizalama, WhisperX'in "Whisper damgasına güvenme" dersinin doğru
uygulaması. Üç metin alanı LibriTTS'in iki-metin kararının genişletilmişi.
HDEMUCS ayrıştırmasıyla müzik dB ölçümü literatürde birebir karşılığı
olmayan, fiziksel karşılığı net bir katkı (Emilia ayrıştırmayı temizlik
için kullanır, ölçüm olarak yayımlamaz). `run.json` köken kaydı (model
revizyonları, politika sürümü, konfigin tamamı) veri makalelerinde nadiren
görülen bir titizlik. Kanal dengesizliği (ilk iki kanal %35,2) literatürde
eleme sebebi değildir; Emilia'nın ana savı çeşitliliği koruyan gevşek hattın
doğallıkta kazandığıdır — kanal tavanını kaldırma kararı literatürle
uyumlu, yapılacak tek şey dağılımı makale tablosunda raporlamak.

## 4. Literatüre göre boşluklar (önem sırasıyla)

1. **Algısal kalite ölçüsü ve SNR yok.** Modern hatların hepsi DNSMOS
   üretir; Hi-Fi TTS SNR'ı seçim ölçütü yapar. Kiraat'ta ikisi de yok
   (v4'te politikadan kaldırılan `dnsmos_ovrl` kuralının sebebi sütunun hiç
   üretilmemesiydi). Mimarîye tam oturan eksik: DNSMOS bir ölçüm
   aşamasıdır, kapı değil; `music` deseninde bir `ClipStage` olarak eklenir
   ve WenetSpeech4TTS tarzı katmanlı yayına + makaledeki kalite dağılımı
   histogramına zemin olur. Brouhaha tek geçişte VAD + SNR + C50 verir —
   tek aşamayla üç sütun. Klip düzeyi olduğundan tam koşudan sonra da
   koşturulabilir, koşuyu bekletmez. (Defter açık maddesi 11'in
   genişletilmişi.)
2. **Konuşmacı bilgisi yok.** Emilia, AutoPrep ve WenetSpeech4TTS'in üçü de
   diarization/kümeleme içerir; standart tabloda konuşmacı sayısı ve
   cinsiyet dengesi vardır. `speaker_id` üretilmediği için `dedupe` kanala
   düşüyor (DESIGN #4 fiilen "farklı kanal korunur" çalışıyor; DESIGN #8
   açık). **Zamanlama uyarısı:** diarization kayıt düzeyidir, `work/audio`
   üzerinde koşar; tam koşu sonrası ara sesi silme kararı, diarization'ı
   hatta ekleme kararından önce verilmemeli — ara ses silinirse konuşmacı
   aşaması için 283 GB'lık prepare yeniden koşar.
3. **Nihai kanıt deneyi planda eksik.** Defterdeki koşulacak deneylerin
   hiçbiri "bu korpusla TTS eğit, MOS/CER/SECS raporla" değil; bölütleme
   ablasyonu en yakını ama değerlendirme düzeneği tanımsız. Alanın
   beklentisi WenetSpeech4TTS deseni: her katmanla ayrı model eğitip
   karşılaştırmak. Politika ve katmanlamanın kanıtı aynı deneyden çıkar;
   hangi ölçümlerin üretileceğini geriye doğru belirlediği için makale
   planına şimdiden yazılmalı.
4. **Held-out test yapılmadı** (DESIGN #6, defter açık maddesi 5).
   ManaTTS'in ayrı test kümesi iyi emsal; v1'deki %5,9 train–validation
   metin sızıntısı motivasyonu zaten veriyor.
5. **LUFS ölçümü yok** (DESIGN #9). İlkeye uygun asgari adım normalizasyon
   değil ölçüm: klip başına LUFS sütunu yayımla, seviye kararını alıcıya
   bırak. (LibriTTS-R'nin restoration yolu ayrı ve büyük bir iş.)
6. **Metin normalizasyonu boşlukları** (defter açık maddesi 7: "MI6",
   "3G", tek başına sıra sayısı). Referans hat NeMo'nun WFST yaklaşımı;
   Türkçe kural seti bize düşer ama "en uzun eşleşme + sözcük sınırı"
   mimarisi aynı ailede.
7. **İlkeyle küçük çelişkiler.** `boundaries.RefineConfig`'in yedi eşiği,
   `asr.beam_size=5`, `music.window_sec=10.24` ve `segment.INTERNAL_BREAKS`
   koda gömülü — "hiçbir eşik koda gömülmez" ilkesinin bekçisiz
   istisnaları. `config.py`'de `SECTIONS` kaldırılmış dört bölümü hâlâ
   izinli sayıyor; `pipeline.run_boilerplate` kod varsayılanları konfigle
   uyuşmuyor (pratikte etkisiz, bekçisi yok).

## 5. Makale için çıkarımlar

En yakın emsaller KazakhTTS2 (LREC 2022) ve ManaTTS (NAACL 2025); ikisi de
"veri kümesi + tarif + eğitilmiş modelle kanıt" formatında. Hedef venue
ailesi Interspeech / LREC / ICASSP-SLT-ASRU / *ACL. Standart raporlama
tablosunda kiraat'ın bugün dolduramadığı hücreler tam olarak yukarıdaki
1–2 numaralı boşluklar: kalite dağılımı ve konuşmacı/cinsiyet. Katkı
cümleleri literatür karşısında şöyle duruyor: (a) eşiksiz, kör dinlemeyle
gerekçelendirilmiş sürümlü alt küme politikası — katmanlamanın
denetlenebilir hâli; (b) çok saatlik tek parça kaydın sabit bellekle
işlenmesi — Emilia'nın girdileri bir saati geçmiyor, Libriheavy referans
metne yaslanıyor, bizde ikisi de yok; (c) ayrıştırma tabanlı, fiziksel
karşılığı olan müzik ölçümü.
