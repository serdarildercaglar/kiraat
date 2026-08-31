"""Kaynak kaydı çöz: tek kanal, hedef örnekleme hızı, yüksek geçiren, tepe sınırı.

Kaynak hızı hedefin altındaysa yükseltme yapılmaz; gerçek hız
`source_sample_rate` olarak yayımlanır. Ses seviyesi normalizasyonu yoktur:
seviye klip başına sütun olarak yayımlanır (`clip_qc`), normalizasyon
kullanıcının tercihidir.
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
    """Yüksek geçiren süzgeç; tepe sınırlayıcı yalnızca istenirse.

    Sınırlayıcı 30 Ağu 2026'da varsayılan olarak kapatıldı, çünkü ölçümü
    maskeliyordu: `clip_qc` tepeyi ve kırpılmayı sınırlanmış sesten kesilen
    klipte ölçüyor, dolayısıyla sütun kaynağın kırpılmasını değil hattın
    kendi tavanını gösteriyordu. Ölçüldü — %57,5'i sert kırpılmış bir sinüs
    zincirden geçirildiğinde çıkışta tepe tam −1,000 dBFS ve `clip_ratio`
    0,000000; `|x| ≥ 0,99` eşiği 0,8913 tavanının üstünde kaldığı için sütun
    sıfırdan başka değer alamıyordu ve politikadaki `clip_ratio` kuralı
    hiçbir klibi elemiyordu. Sınırlama zaten veriyi değiştiren tek aşamaydı;
    "aşamalar karar vermez, ölçer" değişmezine de aykırıydı.

    `peak_ceiling_db` verilirse sınırlayıcı geri gelir. O durumda `level`
    kapalı tutulmalı: `alimiter`'ın varsayılan `level=true` seçeneği çıkışı
    otomatik tam ölçeğe yükseltip tavanı boşa çıkarıyor (5 kayıtlık örnekte
    bir kaynak 0,00 dBFS'e çıkıp kırpılmıştı).
    """
    filters = [f"highpass=f={float(opts.get('highpass_hz', 40.0))}"]
    ceiling = opts.get("peak_ceiling_db")
    if ceiling is not None:
        filters.append(f"alimiter=limit={10 ** (float(ceiling) / 20):.4f}:level=false")
    return filters


@register
class PrepareStage(SourceStage):
    name = "prepare"
    version_ignore = ("ffmpeg_threads",)   # yalnızca başarım
    version = "6"   # v6: tepe sınırlayıcı varsayılan kapalı (ölçümü maskeliyordu); v5: FLAC

    def process_source(self, source: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
        work = Path(self.cfg.get("paths.work_root"))
        out = work / "audio" / f"src{source['id']:05d}.flac"
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
        # Ara ses kayıpsız FLAC: 24 kHz mono konuşmada PCM16'nın %48'i. Tam
        # korpusta (~2.100 saat) ara sesin 366 GB yerine ~160 GB tutması,
        # klipler ve ham kayıtlarla birlikte diske sığmasının şartı.
        # `-sample_fmt s16` zorunlu: ffmpeg'in FLAC kodlayıcısı varsayılan
        # olarak s32/24 bit seçiyor, o zaman hem örnekler PCM16 yolundakiyle
        # aynı olmuyor hem de dosya %93'e çıkıp sıkışmıyor. s16 ile
        # soundfile ve faster-whisper aynı örnekleri bit bazında okuyor.
        cmd = ["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-threads",
               str(int(self.opts.get("ffmpeg_threads", 2))), "-i", source["path"],
               *(["-t", f"{cap_sec:.3f}"] if cap_sec else []),
               "-ac", "1", "-ar", str(sr), "-af", ",".join(filters),
               "-c:a", "flac", "-sample_fmt", "s16", str(out)]
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
