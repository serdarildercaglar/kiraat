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

## Çalıştırma

```bash
/home/serdar/miniconda3/envs/main/bin/python -m pytest
/home/serdar/miniconda3/envs/main/bin/python -m kiraat run            # runtime.max_sources kadar kaynak
/home/serdar/miniconda3/envs/main/bin/python scripts/report.py        # manifestonun özeti
```

`run`, `configs/default.yaml` içindeki hattı koşturur: `prepare → asr →
boilerplate → segment → clip_qc → music → export`. Durum `work/db/state.sqlite`
içinde sürümlü tutulur; yeniden koşuda biten iş atlanır. Çıktı
`work/manifests/clips.jsonl`, her klip her ölçümüyle ve `recommended` bayrağı
+ gerekçeleriyle.

## Yapı

```
kiraat/
  pipeline.py       orkestratör: kaynak keşfi (kanal-dönüşümlü), aşama sırası, dışa aktarım
  store.py          sqlite durum deposu (sources, clips, done)
  segment.py        cümle hizalı bölütleyici — hattın çekirdeği
  boundaries.py     sınırı ASR damgasından sessizliğe çekme
  boilerplate.py    kanal düzeyinde künye/anons madenciliği
  scoring.py        skor tabanlı çıktı sözleşmesi (kapı değil, skor)
  dedupe.py         (metin, konuşmacı) çiftinde yineleme işaretleme
  config.py         tek YAML'dan doğrulanmış konfig
  base.py           SourceStage / ClipStage sözleşmeleri
  stages/           prepare, asr, segmentation, clip_qc, music
  text/             turkish (I/ı), sentences, normalize
scripts/            probe_segment, probe_boilerplate, probe_music, listen_ui, report
configs/default.yaml
docs/NOTEBOOK.md    araştırma defteri — makale bundan yazılacak
docs/DESIGN.md      iç belge: mühendislik gerekçeleri
tests/
```

## Durum

Hat uçtan uca çalışıyor ve beş kaynaklık örnekte doğrulandı (2.649 klip,
üç kör dinleme turu). Henüz bağlanmayanlar: zorlamalı hizalama
(`word_confidence` şimdilik ASR olasılığı), konuşmacı kümeleme, DNSMOS,
kaynak düzeyi ses seviyesi, kanal başına saat tavanı ve yayın paketi.
Tam korpus koşusu açık onay ister.
