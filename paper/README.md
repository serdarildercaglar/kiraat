# Makale

arXiv ön baskısının kaynağı. Makale sıfırdan yazılır ve **önceki bir yayına
ya da önceki bir veri kümesine hiç değinmez**; buradaki her sayı bu depoda
üretilmiştir ve kaynağı [`docs/NOTEBOOK.md`](../docs/NOTEBOOK.md) içindeki
ilgili başlıktır.

| dosya | içerik |
|---|---|
| `main_en.tex` | İngilizce tam metin (arXiv birincil sürümü) |
| `preamble.tex` | ortak önbölüm |
| `refs.bib` | kaynakça |

## Derleme

`tectonic` ile derlenir; eksik LaTeX paketlerini kendisi indirdiği için
sisteme TeX kurmak ya da sudo gerekmez:

```bash
tectonic -X compile paper/main_en.tex
```

Kurulu değilse statik ikili yeter (sürüm sabit tutulur, çıktı yeniden
üretilebilsin diye):

```bash
V=0.15.0
curl -sL "https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%40$V/tectonic-$V-x86_64-unknown-linux-musl.tar.gz" \
  | tar xz -C /tmp
install -m 755 /tmp/tectonic ~/.local/bin/tectonic
```

Depodaki `main_en.pdf` bununla üretildi: tectonic 0.15.0, xdvipdfmx,
11 sayfa. Yeniden derleme içerikçe aynı PDF'i verir ama bayt bayt aynısını
vermez — PDF kimliği ve zaman damgaları her koşuda değişir, 97.036 baytın
67'si oynar. Karşılaştırma bu yüzden `cmp` ile değil metin dökümüyle
yapılır:

```bash
pdftotext eski.pdf - > eski.txt && pdftotext paper/main_en.pdf - > yeni.txt
diff eski.txt yeni.txt
```

Tectonic'in "TeX rerun seems needed, but stopping at 6 passes" uyarısı
beklenen bir çıktıdır ve atıflar çözülmüş olarak biter; kontrol için
derleme kaydında `Undefined` aranır.

`pdflatex` yolu da açık (`iftex` sayesinde `xelatex` de çalışır), ama
önbölümün istediği `booktabs`, `caption`, `microtype` ve `xcolor` taban
TeX Live kurulumunda bulunmaz:

```bash
sudo apt install texlive-latex-recommended texlive-latex-extra
pdflatex main_en && bibtex main_en && pdflatex main_en && pdflatex main_en
```

arXiv BibTeX koşturmaz; gönderim paketine `main_en.bbl` konulmalıdır.
Tectonic ara dosyaları varsayılan olarak siler, `.bbl` için
`--keep-intermediates` verilir.

## Taslakta eksik olanlar

Metinde `% TODO` olarak işaretli, kapatılmadan gönderilmemesi gerekenler:

1. **Alt akış TTS deneyi.** Defterin "Koşulacak deneyler" listesindeki ilk
   madde. Şu an §Limitations içinde açıkça "yapılmadı" diye duruyor; deney
   koşulunca hem orası hem §Results değişir. Makalenin en zayıf yeri budur.
2. **Türkçe okuma konuşması kaynakları tablosu.** İlgili çalışmalar
   bölümündeki saat sayıları birincil kaynaktan tek tek doğrulanmadan
   yazılmaz.
3. **Yayın bağlantıları.** §Availability boş: veri kümesi ve kod deposu
   bağlantıları, lisans satırı ve kanal künyesi şartı yayın anında konur.
4. **Şekiller.** Metin şu an tablolarla yürüyor. Ablasyonun süre dağılımı ve
   kalite sütunlarının dağılımı şekle değer; şekil betiği yazılmadı.
5. **Türkçe sürüm.** v1'de iki dilli gönderim yapılıyordu; `main_tr.tex`
   henüz yok.
