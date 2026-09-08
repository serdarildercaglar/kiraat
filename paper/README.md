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

Depoda LaTeX kurulu değildi; `tectonic` ayrı bir conda ortamına kuruldu ve
eksik paketleri kendisi indiriyor:

```bash
/home/serdar/miniconda3/envs/tex/bin/tectonic -X compile paper/main_en.tex
```

`pdflatex` ile de derlenir (`iftex` sayesinde `xelatex` de çalışır):

```bash
pdflatex main_en && bibtex main_en && pdflatex main_en && pdflatex main_en
```

arXiv BibTeX koşturmaz; gönderim paketine `main_en.bbl` konulmalıdır.

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
