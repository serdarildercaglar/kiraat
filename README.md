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

Aşamalar tek sırada gitmez: `kiraat/scheduler.py` CPU işlerini (prepare,
segment, clip_qc) ve GPU işlerini (asr, align, music) ayrı süreç
havuzlarında üst üste bindirir; bir kaynağın bölütlemesi, kanalının bütün
kayıtlarının ASR'si bitmeden başlamaz (künye madenciliği kanalın tamamını
görsün diye) ve depoya yalnızca ana süreç yazar. `--serial` tek süreçli
sıralı yolu koşturur; ikisi aynı manifestoyu üretir
(`scripts/compare_manifests.py` ile sınanır). İşçi sayıları
`runtime.source_workers` / `runtime.gpu_stage_concurrency` (CLI:
`--cpu-workers`, `--gpu-workers`).

Her koşu, manifestonun yanına bir **koşu kaydı** yazar
(`work/<koşu>/manifests/run.json`): git commit'i ve çalışma ağacının temiz
olup olmadığı, bütün aşamaların sürüm dizgeleri, politika sürümü, konfigin
tamamı, model ağırlıklarının kimlikleri (HF revizyonu ya da onu sabitleyen
paket) ve paket sürümleri. Koşudan sonra yeniden kurulamayan tek şey budur;
`scripts/verify_columns.py` kaydın depodaki 'bitti' sürümleriyle
uyuştuğunu ayrıca sınar. Bağımlılıklar `requirements.txt` içinde tam
sürümle sabitlenmiştir — aralık kullanılmaz, çünkü yukarı akıştaki bir
yükseltme çıktıyı sessizce değiştirir.

## Yapı

```
kiraat/
  pipeline.py       orkestratör: kaynak keşfi (kanal-dönüşümlü), aşama sırası, dışa aktarım
  scheduler.py      bağımlılık çizelgeli dağıtıcı: CPU/GPU havuzları, kanal bariyeri, tek yazıcı
  store.py          sqlite durum deposu (sources, clips, done)
  segment.py        cümle hizalı bölütleyici — hattın çekirdeği
  boundaries.py     sınırı ASR damgasından sessizliğe çekme
  boilerplate.py    kanal düzeyinde künye/anons madenciliği
  scoring.py        skor tabanlı çıktı sözleşmesi (kapı değil, skor)
  dedupe.py         (metin, konuşmacı) çiftinde yineleme işaretleme
  config.py         tek YAML'dan doğrulanmış konfig
  base.py           SourceStage / ClipStage sözleşmeleri
  provenance.py     koşu kaydı: commit, aşama sürümleri, konfig, ağırlıklar, paketler
  stages/           prepare, asr, segmentation, clip_qc, music
  text/             turkish (I/ı), sentences, normalize
scripts/            inventory, probe_segment, probe_boilerplate, probe_music, listen_ui, report, compare_manifests, exp_parallel
configs/default.yaml
docs/NOTEBOOK.md    araştırma defteri — makale bundan yazılacak
docs/DESIGN.md      iç belge: mühendislik gerekçeleri
tests/
```

## Durum

Hat uçtan uca çalışıyor: 27 kanalı kapsayan 25 saatlik denetim örneğinde
13.637 klip (`work/sample-25c`), üç kör dinleme turu, sütun doğrulaması
hatasız. Zorlamalı hizalama bağlı ve kendi skorunu yayımlıyor
(`word_confidence`ın kaynağı konfigden seçilir, şimdilik ASR olasılığı).

Ham korpus dosya dosya ölçüldü (`scripts/inventory.py` →
`work/inventory.jsonl`): 3.440,2 saat, 2.698 kayıt, 27 kanal, tamamına
yakını 44,1 kHz 128 kb/s AAC. Kayıtların **%30,7'si dört saatten uzun**,
en uzunu 14,92 saat; bu yüzden bölütleme ve hizalama kaydı belleğe almaz,
zarfı bloklar hâlinde ölçüp parçaları diskten okur (korpusun en uzun
kaydı uçtan uca koşturulmuştur).

**Hiçbir kayıt kapsam dışı bırakılmaz.** `sources.extensions` ffmpeg'in
ses çıkarabildiği bütün kapsayıcıları içerir ve kanal başına saat tavanı
yoktur; kuru koşu 2.699 kaynak / 3.440,16 saat seçiyor. Kanal
dengesizliği (`seslikitaplarmavi` %19,5, ilk iki kanal %35,2) tavanla
değil, `channel` + `duration` sütunlarıyla yayımlanır — tavanı kesmek
kullanıcının tercihidir.

Henüz bağlanmayanlar: konuşmacı kümeleme, ses seviyesi normalizasyonu
(LUFS yalnızca ölçülüp sütun olarak yayımlanır), bölme (train/dev/test) ve
yayın paketi. DNSMOS P.835 sütunları 31 Ağu 2026'dan beri üretiliyor ama
politikada kural değil. Tam korpus koşusu açık onay ister.
