"""Zorlamalı hizalama: ASR kelimelerine CTC tabanlı zaman damgası ve güven.

Whisper'ın kelime damgaları çapraz-dikkat tahminidir ve bitişleri
sistematik olarak erkendir (kör dinlemede görüldü). MMS_FA (torchaudio,
1.100+ dil, uroman/romanize edilmiş karakter sözlüğü) her kelimeyi CTC
zorlamalı hizalamasıyla sese oturtur ve kare olasılıklarından bir güven
üretir. v1'in "iki geçiş CER'i" yerine geçen sinyal budur (hata #12).

Uzun kayıt tek parçada hizalanamaz (kafes T×N); Whisper'ın kaba damgaları
kılavuz alınarak ~30 s'lik parçalara bölünür, her parça kendi ses
penceresinde hizalanır ve zamanlar kayıt eksenine taşınır. Çıktı, ASR
kelime dosyasıyla satır satır aynı sırada bir kelime dosyasıdır; ek
alanlar `align_start`, `align_end`, `align_score`.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from ..base import SourceStage, register
from .asr import load_words


@dataclass(frozen=True)
class Chunk:
    a: int          # kelime dizini [a, b)
    b: int
    start: float    # ses penceresi (s)
    end: float


def make_chunks(words: Sequence[Mapping[str, Any]], *, target_sec: float = 30.0,
                max_sec: float = 60.0, min_gap_sec: float = 0.3, pad_sec: float = 0.5,
                total_sec: float | None = None) -> list[Chunk]:
    """Kelimeleri, hedef süreyi aşınca ilk uygun boşlukta kesip parçalara böl.

    Hedef aşıldıktan sonraki ilk `min_gap_sec` üstü boşlukta kesilir; `max_sec`
    aşılırsa en büyük boşlukta zorla kesilir. Pencere iki yana `pad_sec` taşar.
    """
    chunks: list[Chunk] = []
    if not words:
        return chunks
    a = 0
    while a < len(words):
        b = a + 1
        best_gap, best_at = -1.0, None
        while b < len(words):
            dur = words[b - 1]["end"] - words[a]["start"]
            gap = words[b]["start"] - words[b - 1]["end"]
            if gap > best_gap:
                best_gap, best_at = gap, b
            if dur >= target_sec and gap >= min_gap_sec:
                break
            if dur >= max_sec:
                b = best_at if best_at is not None else b
                break
            b += 1
        start = max(words[a]["start"] - pad_sec, 0.0)
        end = words[b - 1]["end"] + pad_sec
        if total_sec is not None:
            end = min(end, total_sec)
        chunks.append(Chunk(a, b, start, end))
        a = b
    return chunks


class WindowReader:
    """Kaydın bir aralığını hizalayıcının örnekleme hızında döndürür.

    Kaydın tamamını okuyup tek seferde yeniden örneklemek 24→16 kHz'de saat
    başına ~2,2 GB tutuyordu ve korpusta 14,9 saatlik kayıtlar var. Burada
    yalnızca parçanın aralığı okunur, iki yanına `margin_sec` pay eklenir ve
    pay atılır: süzgeç çekirdeği (birkaç on örnek) payın çok içinde kaldığı
    için iç bölge, tam dosyayı yeniden örneklemekle aynı çıkar.

    Pencerenin başı kaynak tarafında `su` katına yaslanır (`su/tu`, hızların
    sadeleşmiş oranı); böylece pencerenin ilk örneği hedef eksende tam bir
    örneğe denk gelir ve faz kaymaz.
    """

    def __init__(self, path: str, target_sr: int, margin_sec: float = 0.5) -> None:
        import soundfile as sf

        info = sf.info(path)
        if info.channels != 1:
            raise ValueError(f"tek kanal bekleniyordu, {info.channels} kanal: {path}")
        self.path = path
        self.src_sr = info.samplerate
        self.frames = info.frames
        self.target_sr = target_sr
        g = math.gcd(self.src_sr, target_sr)
        self.su, self.tu = self.src_sr // g, target_sr // g
        self.margin = int(math.ceil(margin_sec * self.src_sr / self.su)) * self.su

    def window(self, a0: int, a1: int) -> np.ndarray:
        import soundfile as sf

        a0, a1 = max(a0, 0), max(a1, 0)
        if self.src_sr == self.target_sr:
            data, _ = sf.read(self.path, start=a0, stop=min(a1, self.frames),
                              dtype="float32", always_2d=False)
            return data
        import torchaudio

        p0 = max((a0 * self.su // self.tu - self.margin) // self.su * self.su, 0)
        p1 = min(-(-a1 * self.su // self.tu) + self.margin, self.frames)
        if p1 <= p0:
            return np.zeros(0, dtype=np.float32)
        block, _ = sf.read(self.path, start=p0, stop=p1, dtype="float32", always_2d=False)
        import torch

        out = torchaudio.functional.resample(torch.from_numpy(block), self.src_sr,
                                             self.target_sr).numpy()
        o0 = p0 * self.tu // self.su
        return out[a0 - o0:a1 - o0]


def romanize(tokens: Sequence[str], language: str = "tur") -> list[str | None]:
    """Her belirteç için romanize karakter dizisi ('f e r m a n'); boş kalanlar None."""
    from ctc_forced_aligner import get_uroman_tokens, text_normalize

    out: list[str | None] = []
    for tok in tokens:
        norm = text_normalize(tok.strip(), language)
        rom = get_uroman_tokens([norm], language)[0] if norm else ""
        out.append(rom if rom.strip() else None)
    return out


@register
class AlignStage(SourceStage):
    name = "align"
    version = "3"   # v3: kare adımı modelden ölçülüyor (parça sonunda +20 ms sapma); v2: log_softmax
    gpu = True
    depends_on = ("asr",)
    # `confidence_source` bu aşamada okunmuyor, `segment` kullanıyor; burada
    # sürüme girseydi tercih değişince 3.400 saat yeniden hizalanırdı.
    version_ignore = ("confidence_source",)

    def setup(self) -> None:
        import torch
        import torchaudio

        self.device = str(self.cfg.get("runtime.device", "cuda:0"))
        bundle = torchaudio.pipelines.MMS_FA
        self.model = bundle.get_model(with_star=True).to(self.device).eval()
        self.dictionary = bundle.get_dict(star="<star>")
        self.sr = bundle.sample_rate
        self.torch = torch
        self.sec_per_frame = self._probe_frame_stride()

    def _probe_frame_stride(self) -> float:
        """Modelin kare adımını (s) iki ileri geçişle çöz.

        Kare süresini `(len(audio)/sr)/T` diye hesaplamak sistematik olarak
        sapıyordu: evrişim yığınının alıcı alanı (400 örnek) yüzünden T,
        uzunluğun adıma tam bölümünden bir eksik ve oran adımı biraz büyük
        çıkarıyor. Sapma parça sonunda tam +20 ms'ye ulaşıp her parça başında
        sıfırlanıyordu — gürültü değil, kelimenin parça içindeki konumuyla
        orantılı bir eğim. Adım burada ölçülür ki sabit sayı olmasın ve
        bundle değişirse kendiliğinden doğru kalsın.
        """
        torch = self.torch
        lengths = (self.sr * 10, self.sr * 20)
        frames = []
        with torch.inference_mode():
            for n in lengths:
                em, _ = self.model(torch.zeros(1, n, device=self.device))
                frames.append(em.shape[1])
        stride = (lengths[1] - lengths[0]) / (frames[1] - frames[0]) / self.sr
        if not 0.005 < stride < 0.1:
            raise RuntimeError(f"hizalayici kare adimi beklenmedik: {stride:.6f} s")
        return stride

    def teardown(self) -> None:
        self.model = None

    # ------------------------------------------------------------------
    def _align_chunk(self, audio: np.ndarray, words: Sequence[Mapping[str, Any]],
                     roman: Sequence[str | None], chunk: Chunk) -> list[dict[str, Any] | None]:
        """Parça için kelime başına (start, end, score) ya da None."""
        import torchaudio.functional as F

        torch = self.torch
        if len(audio) < self.sr // 2:
            return [None] * (chunk.b - chunk.a)
        ids: list[int] = []
        spans_per_word: list[int] = []
        for i in range(chunk.a, chunk.b):
            r = roman[i]
            toks = [self.dictionary["<star>"]] + ([self.dictionary[c] for c in r.split(" ") if c in self.dictionary] if r else [])
            ids += toks
            spans_per_word.append(len(toks))
        with torch.inference_mode():
            # MMS_FA çıktısı zaten log-olasılıktır ve `with_star=True` sonuna
            # 0 değerli (olasılık 1,0) bir `<star>` sütunu ekler — kasıtlı
            # olarak normalize edilmemiş. Buraya bir `log_softmax` daha
            # koymak toplamı 2'ye böler: star tam 0,5'e oturur, gerçek
            # belirteçlerin hepsi yarıya iner ve skor tavanı 0,5 olur.
            # Kayma her karede tekdüze olduğu için CTC yolu ve damgalar
            # değişmez, yalnızca yayımlanan skor yanlış çıkar; sample-25'te
            # 12.938 klibin 11.362'si 0,5 kovasındaydı. Normalize etme.
            em, _ = self.model(torch.from_numpy(audio).unsqueeze(0).to(self.device))
        T = em.shape[1]
        if T < len(ids) + 2:
            return [None] * (chunk.b - chunk.a)
        targets = torch.tensor([ids], dtype=torch.int32, device=self.device)
        try:
            aligned, scores = F.forced_align(em, targets, blank=0)
        except Exception:
            return [None] * (chunk.b - chunk.a)
        spans = F.merge_tokens(aligned[0], scores[0].exp())
        sec_per_frame = self.sec_per_frame
        out: list[dict[str, Any] | None] = []
        k = 0
        for n in spans_per_word:
            seg = spans[k:k + n]
            k += n
            body = seg[1:]  # ilk belirteç <star>
            if not body:
                out.append(None)
                continue
            out.append({
                "align_start": round(chunk.start + body[0].start * sec_per_frame, 3),
                "align_end": round(chunk.start + body[-1].end * sec_per_frame, 3),
                "align_score": round(float(np.mean([s.score for s in body])), 4),
            })
        return out

    def process_source(self, source: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
        import soundfile as sf

        words = load_words(source["words"])
        out_path = Path(self.cfg.get("paths.work_root")) / "align" / f"src{source['id']:05d}.jsonl"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if not words:
            out_path.write_text("", encoding="utf-8")
            return [{"aligned": str(out_path), "n_aligned": 0}]

        info = sf.info(source["audio"])
        total = info.frames / info.samplerate
        reader = WindowReader(source["audio"], self.sr)

        roman = romanize([w["text"] for w in words], self.opts.get("language", "tur"))
        chunks = make_chunks(words, target_sec=float(self.opts.get("chunk_sec", 30.0)),
                             max_sec=float(self.opts.get("max_chunk_sec", 60.0)),
                             min_gap_sec=float(self.opts.get("chunk_gap_sec", 0.3)),
                             pad_sec=float(self.opts.get("pad_sec", 0.5)), total_sec=total)
        results: list[dict[str, Any] | None] = []
        for ch in chunks:
            audio = reader.window(int(ch.start * self.sr), int(ch.end * self.sr))
            results.extend(self._align_chunk(audio, words, roman, ch))
        assert len(results) == len(words)

        n_ok = 0
        with out_path.open("w", encoding="utf-8") as fh:
            for w, r in zip(words, results):
                row = dict(w)
                if r is not None:
                    row.update(r)
                    n_ok += 1
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        scores = [r["align_score"] for r in results if r]
        return [{"aligned": str(out_path), "n_aligned": n_ok, "n_chunks": len(chunks),
                 "align_score_median": round(float(np.median(scores)), 4) if scores else None}]
