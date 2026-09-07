# Metrik veritabanları

Hattın ürettiği ölçümler `work/<koşu>/db/state.sqlite` içinde tutulur;
`work/` sürüm denetiminde değildir. Başka bir makinede analiz ya da makale
istatistiği koşturmak için veritabanları burada sıkıştırılmış olarak
bulunur — dosyalar `VACUUM INTO` ile alınmış temiz kopyalardır, WAL
artığı taşımazlar.

| koşu | sıkıştırılmış | açılmış | nerede |
|---|---|---|---|
| `sample-25d` | 2,2 MB | 19,2 MB | bu dizinde |
| `full-1` | 291,9 MB | 2.578 MB | GitHub Release `db-2026-09-07` |

`full-1` git'e konulamıyor: GitHub tek dosyada 100 MB sınırı koyuyor.
Sürüm varlığı olarak yükleniyor, böylece depo geçmişi şişmiyor.

## Açma

```bash
# depoda duran örneklem
zstd -d data/db/sample-25d.sqlite.zst -o work/sample-25d/db/state.sqlite

# tam koşu
gh release download db-2026-09-07 -R serdarildercaglar/kiraat -p 'full-1.sqlite.zst'
zstd -d full-1.sqlite.zst -o work/full-1/db/state.sqlite
```

Hedef dizinin (`work/<koşu>/db/`) önceden açılmış olması gerekir. Hat bu
veritabanının yanına ses ve klip dosyalarını da bekler; yalnız veritabanıyla
aşama koşturulamaz, ölçüm okunur ve analiz edilir.

## Doğrulama

```
sha256  eac4ecdb1baed321d2bd30258609b9766fde2caca5d8ad801b734557b2318517  sample-25d.sqlite.zst
sha256  443f33ec8bb8fb8fbe2d5bd762407bc3bde6d0a4265cc317f69c9feb3cdb9dca  full-1.sqlite.zst
```
