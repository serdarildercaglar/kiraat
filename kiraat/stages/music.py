"""Arka plan müziği ölçümü.

Sorulan soru "bu klip konuşma mı müzik mi" değil, "**konuşmanın altında**
müzik var mı" sorusudur ve ikisi aynı soru değildir. İkili, birbirini dışlayan
bir konuşma/müzik sınıflandırıcısı, altında müzik olan bir anlatıma
neredeyse her zaman "konuşma" der; çünkü karışık durum onun eğitim
dağılımında yoktur.

Bu yüzden üç ayrı sütun üretilir ve üçü de yayımlanır:

  music_score_audioset  AudioSet AST'nin müzik etiketleri üzerinden azami skor.
                        Çok etiketli olduğu için konuşmayla birlikte var
                        olabilir — doğru ailedeki ucuz sinyal budur.
  music_to_speech_db    Kaynak ayrıştırmasından gelen fiziksel ölçü: eşlik
                        (accompaniment) enerjisinin konuşma enerjisine oranı,
                        dB. -30 dB "duyulmaz", -10 dB "belirgin müzik".
  music_prob_external   İsteğe bağlı, dış bir sınıflandırıcının olasılığı.
                        Doğrulanmadan politikada kural olamaz.

Hiçbiri kapı değildir. `background_music` işareti yalnızca yayımlanan
`music_to_speech_db` sütunundan, konfigdeki eşikle türetilir; yani kullanıcı
eşiği beğenmezse veriyi yeniden üretmeden kendi eşiğini kesebilir.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from ..base import ClipStage, register

#: Konuşmanın altındaki müziğin duyulmaz sayıldığı sınır (dB). Bu değerin
#: altındaki klipler işaretlenmez.
INAUDIBLE_DB = -30.0


def rms(samples: Sequence[float]) -> float:
    if len(samples) == 0:
        return 0.0
    return math.sqrt(sum(float(s) * float(s) for s in samples) / len(samples))


def music_to_speech_db(
    speech: Sequence[float], accompaniment: Sequence[float], *, floor_db: float = -80.0
) -> float:
    """Eşlik enerjisinin konuşma enerjisine oranı, dB.

    Negatif değer müziğin konuşmanın altında olduğunu söyler. Konuşma
    sessizse (sıfır enerji) ölçüm tanımsızdır ve `floor_db` yerine `inf`
    dönmez — çağıran, `speech_rms == 0` durumunu ayrı ele almalıdır; burada
    tavan olarak 0 dB verilir çünkü müzik baskın demektir.
    """
    speech_rms = rms(speech)
    music_rms = rms(accompaniment)
    if music_rms <= 0.0:
        return floor_db
    if speech_rms <= 0.0:
        return 0.0
    ratio = 20.0 * math.log10(music_rms / speech_rms)
    return max(ratio, floor_db)


def has_background_music(db: float | None, threshold_db: float = INAUDIBLE_DB) -> bool:
    """Yayımlanan sütundan türetilen ikili yanıt — 'var mı yok mu'."""
    return db is not None and db > threshold_db


@register
class MusicStage(ClipStage):
    """Klip başına müzik ölçümlerini üretir. Karar vermez."""

    name = "music"
    gpu = True
    depends_on = ("events",)

    def process_clips(self, clips: Sequence[Mapping[str, Any]]) -> Sequence[Mapping[str, Any]]:
        threshold = float(self.opts.get("inaudible_db", INAUDIBLE_DB))
        rows: list[dict[str, Any]] = []
        for clip in clips:
            metrics = self.measure(clip)
            flags = []
            if has_background_music(metrics.get("music_to_speech_db"), threshold):
                flags.append("background_music")
            rows.append({"id": clip["id"], "metrics": metrics, "flags": flags})
        self.validate_output(rows)
        return rows

    def measure(self, clip: Mapping[str, Any]) -> dict[str, Any]:
        """Ayrıştırıcı ve sınıflandırıcı bağlandığında burası doldurulur."""
        raise NotImplementedError("ayristirici henuz baglanmadi")
