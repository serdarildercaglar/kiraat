# kiraat

Türkçe okuma-konuşma (read-speech) korpusu üretim hattı. Adı, "sesli okuma"
anlamındaki *kıraat* sözcüğünden geliyor.

Bu hat, `turkish-tts-audiobooks` hattının (v1) yerine geçer. v1 çalıştı ve
2.724 saatlik bir korpus üretti, ama iki yapısal kararı yüzünden ürettiği
verinin önemli bir kısmı ya kusurlu ya da erişilemez kaldı. kiraat o iki
kararı tersine çevirir; gerekçeleri ve ölçümleri [`docs/DESIGN.md`](docs/DESIGN.md)
dosyasında.

## İki temel fark

**Kesim sessizlikte değil, cümlede yapılır.** v1 önce VAD ile kesip sonra
yazıya çeviriyordu; seslendiren virgülde nefes alıp cümle arasında almadığı
için yayımlanan temiz havuzun %9,4'ü cümle ortasından başlıyor, %14,2'si
cümle ortasında bitiyordu. kiraat önce uzun formda ASR + zorlamalı hizalama
yapar, cümle sınırlarını transcript üzerinde bulur ve kesimi oraya koyar.
Cümle ortasından başlayan klip üretmek yapısal olarak mümkün değildir.

**Eşikler klip elemez, yalnızca skorlar.** v1'in ACCEPT/REVIEW ikilisi,
doğrulanmamış bir sentetik-ses sınıflandırıcısı yüzünden 981 saati ve
korpusun kanal çeşitliliğinin neredeyse tamamını kullanılamaz hale getirdi;
sonradan yapılan kör dinleme denetiminde o sınıflandırıcı 131 işaretli klipte
sıfır doğru pozitif verdi. kiraat hiçbir klibi elemez: her klip her ölçümüyle
yayımlanır, yanına konfigden okunan sürümlü bir politikanın ürettiği
`recommended` bayrağı ve gerekçeleri konur. Politika değişince veri yeniden
üretilmez.

## Kurulum

```bash
pip install -r requirements.txt
pytest
```

## Yapı

```
kiraat/
  segment.py        cümle hizalı bölütleyici — hattın çekirdeği
  scoring.py        skor tabanlı çıktı sözleşmesi (kapı değil, skor)
  dedupe.py         (metin, konuşmacı) çiftinde yineleme işaretleme
  config.py         tek YAML'dan doğrulanmış konfig
  base.py           SourceStage / ClipStage sözleşmeleri
  text/
    turkish.py      Türkçeye özgü harf işlemleri (I/ı, i/İ)
    sentences.py    Türkçe cümle sınırı bulma
    normalize.py    okunuşa çevirme: sayılar, kısaltmalar, saat, para
configs/default.yaml
docs/NOTEBOOK.md    araştırma defteri — makale bundan yazılacak
docs/DESIGN.md      iç belge: mühendislik gerekçeleri
tests/
```

## Durum

İskelet aşamasında. Çekirdek algoritmalar (bölütleme, cümle bölme,
normalizasyon, yineleme, politika) yazıldı ve test edildi; model destekli
aşamalar (ASR, hizalama, DNSMOS, konuşmacı, olay) arayüzleriyle tanımlı ama
henüz bağlanmadı.
