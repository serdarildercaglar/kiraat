"""Kaynak kaydı çöz: tek kanal, hedef örnekleme hızı, yüksek geçiren, tepe sınırı.

Kaynak hızı hedefin altındaysa yükseltme yapılmaz; gerçek hız
`source_sample_rate` olarak yayımlanır. Klip başına ses seviyesi
normalizasyonu yoktur (`prepare.target_lufs: null`); kaynak düzeyinde
LUFS ileride ayrı bir aşamadır.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence

from ..base import SourceStage, register


def ffprobe(path: str) -> dict[str, Any]:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
         "stream=sample_rate,channels:format=duration", "-of", "json", path],
        capture_output=True, text=True, check=True).stdout
    info = json.loads(out)
    stream = (info.get("streams") or [{}])[0]
    return {
        "sample_rate": int(stream.get("sample_rate") or 0),
        "channels": int(stream.get("channels") or 0),
        "duration": float((info.get("format") or {}).get("duration") or 0.0),
    }


def ffmpeg_filters(opts: Mapping[str, Any]) -> list[str]:
    """Yüksek geçiren + tepe sınırlayıcı. `alimiter`'ın varsayılan `level=true`
    seçeneği çıkışı otomatik tam ölçeğe yükseltir ve tavanı boşa çıkarır
    (5 kayıtlık örnekte bir kaynak 0,00 dBFS'e çıkıp kırpılmıştı); kapalı
    tutulur ki kaydın doğal seviyesi korunsun."""
    limit = 10 ** (float(opts.get("peak_ceiling_db", -1.0)) / 20)
    return [f"highpass=f={float(opts.get('highpass_hz', 40.0))}",
            f"alimiter=limit={limit:.4f}:level=false"]


@register
class PrepareStage(SourceStage):
    name = "prepare"
    version = "4"   # v4: `max_minutes` tavanı (ffmpeg -t); tavan altındaki kayıtlar v3 ile aynı

    def process_source(self, source: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
        work = Path(self.cfg.get("paths.work_root"))
        out = work / "audio" / f"src{source['id']:05d}.wav"
        out.parent.mkdir(parents=True, exist_ok=True)
        info = ffprobe(source["path"])
        target = int(self.opts.get("target_sr", 24000))
        sr = min(target, info["sample_rate"]) if info["sample_rate"] else target
        filters = ffmpeg_filters(self.opts)
        # Kayıt başına dakika tavanı (örnek koşularda kanal başına eşit saat
        # için): yalnızca ilk `max_minutes` çözülür. Kesilen kaydın kapsayıcı
        # süresi `container_duration` olarak kalır, tavan `cap_sec` olarak
        # yazılır; kesik-indirme işareti tavana göre değil, tavanla
        # kapsayıcının küçüğüne göre verilir.
        cap_sec = float(self.opts.get("max_minutes", 0) or 0) * 60.0
        cmd = ["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-threads",
               str(int(self.opts.get("ffmpeg_threads", 2))), "-i", source["path"],
               *(["-t", f"{cap_sec:.3f}"] if cap_sec else []),
               "-ac", "1", "-ar", str(sr), "-af", ",".join(filters), "-c:a", "pcm_s16le", str(out)]
        if subprocess.run(cmd).returncode != 0 or not out.exists():
            raise RuntimeError(f"ffmpeg basarisiz: {source['path']}")
        # Süre kapsayıcıdan değil çözülen sesten alınır: kesik dosyalarda
        # ffmpeg 0 döner ama ses kapsayıcının dediğinden çok kısadır
        # (örnekte 210 dk yerine 19 dk). Uyumsuzluk kayda işaret olarak düşer.
        decoded = decoded_duration(out)
        row: dict[str, Any] = {"audio": str(out), "duration": round(decoded, 3),
                               "container_duration": round(info["duration"], 3),
                               "source_sample_rate": info["sample_rate"], "prepared_sr": sr}
        expected = min(info["duration"], cap_sec) if cap_sec else info["duration"]
        if cap_sec:
            row["cap_sec"] = cap_sec
        if expected and decoded < float(self.opts.get("truncated_ratio", 0.95)) * expected:
            row["source_flags"] = ["truncated_source"]
        return [row]


def decoded_duration(path: Path) -> float:
    import soundfile as sf

    return float(sf.info(str(path)).duration)
