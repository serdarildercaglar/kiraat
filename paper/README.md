# Makale ve arXiv hazırlığı

İngilizce LaTeX kaynağı `main_en.tex`, önbölümü `preamble.tex`, kaynakçası
`refs.bib`, derlenmiş çıktısı `main_en.pdf` dosyasıdır. Bilimsel inceleme ve
kalan işler `review/REVIEW_TR.md` içindedir. Masaüstündeki eserler (dinleme
etiketleri, ablasyonun kaynak başına çıktısı, konuşmacı gömmeleri) bu yayında
olmadığından makalede sınırlama olarak yazılır.

**Durum: önemli eksikler var.** Derlenebilir bir dosya ve hazırlanmış kaynak
arşivi, bilimsel kanıtların veya veri haklarının tamamlandığı anlamına gelmez.
Makale yalnızca bu korpusu anlatır; önceki kendi yayın/veri kümesiyle
karşılaştırma içermez. Araştırma sonuçlarının kaynağı `docs/NOTEBOOK.md` ve
bu depoda üretilmiş ölçüm veritabanıdır.

## Yerel derleme

Depo kökünden:

```bash
tectonic -X compile --keep-intermediates --keep-logs paper/main_en.tex
```

Tectonic'in BibTeX değişiklik kontrolü altı geçiş sınırı uyarısı verebilir.
Bu uyarı tek başına başarı ölçütü değildir: derleme çıkış kodu, `.bbl`,
çözülmemiş atıflar, eksik karakterler ve PDF sayfaları kontrol edilir.
`paper/review/compile.txt` son derleme kaydını tutar.

arXiv'in yerel doğrulamada kullanılan Tectonic'i çalıştırdığı varsayılmaz.
12 Ekim 2026'da kontrol edilen resmî yönergeler TeX Live 2025'i varsayılan,
2023'ü alternatif olarak sunuyor; `pdflatex` ve `xelatex` destekleniyor.
Bu kaynak `iftex` kullanır ve Tectonic ile derlenmiştir; önerilen gönderim
motoru **XeLaTeX**. Yerel tam TeX Live/XeLaTeX ve arXiv sunucusunda derleme
henüz doğrulanmış değildir; yükleme önizlemesi ayrıca kontrol edilmelidir.

## Kaynak arşivi

`arxiv-source.zip` yalnızca şu dosyaları içerir; hepsi arşiv kökündedir:

- `main_en.tex`
- `preamble.tex`
- `refs.bib`
- `main_en.bbl`

Ana dosya `main_en.tex` seçilir. Kaynakla üretilmiş PDF, `.aux`, `.log`,
bu inceleme raporu, veri tabanı ve kullanılmayan görseller arşive konulmaz.
Metinde şekil yoktur; altı tablo LaTeX içinde üretilir. İleride şekil
kullanılırsa ilgili PDF/PNG/JPEG dosyası da arşivde bulunmalıdır.

**Güncel düzeltme:** arXiv'in yeni gönderim sistemi BibTeX/Biber çalıştırabilir.
`.bib` dosyası desteklenir; önceden üretilmiş `.bbl` de kullanılabilir ve adı
ana `.tex` ile eşleşmelidir. Bu pakette ikisi de vardır.
[Resmî TeX yönergesi](https://info.arxiv.org/help/submit_tex.html).

`review/arxiv_metadata.json` başlık, özet ve önerilen kategorileri tutar.
Özet arXiv'in 1.920 karakter sınırıyla kontrol edilir; gönderim formuna
LaTeX font komutları eklenmeden aktarılır. Yazar adı, kurum, ORCID ve makale
lisansı son gönderimden önce yazar tarafından doğrulanmalıdır.

## Kanıt doğrulaması

`review/verify_card.txt`: 150 veri kartı denetiminin çıktısı.
`review/audit_database.py`: yalnızca mevcut DB'yi okuyan ek makale denetimi.
`review/database_audit.json`: cümle-proxy sayıları, kaynak/metin örtüşmesi,
kanal süreleri, hazırlanmış örnekleme hızı ve müzik ölçümü kapsamı.

```bash
python scripts/verify_card.py --db work/full-1/db/state.sqlite
python paper/review/audit_database.py
```

Bu incelemede belgelenen `main` conda ortamı bulunamadığı için analizler,
Codex'in paketli Python'u temel alınarak `/tmp/kiraat-paper-review-env`
içinde ayrı bir ortamda koşuldu. NumPy 2.3.5 ve PyYAML 6.0.3 kullanıldı;
model çıkarımı veya tam korpus üretimi yapılmadı. Paket sürümü
`review/environment.json` ile kaydedilir; makalede özgün model ortamıyla
özdeş yeniden üretim iddiası edilmez.

Dinleme etiketleri, özgün `run.json`, envanter, konuşmacı gömmeleri/küme
atamaları ve ablasyonun kaynak başına çıktısı bu çalışma dizininde yoktur.
Veritabanı denetimi bunların yerine geçmez.
