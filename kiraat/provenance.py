"""Koşu kaydı: bir manifestoyu üreten kodu, konfigi ve ağırlıkları kimliklendirir.

Hattın merkezî iddiası ölçümün karardan ayrı durması ve politikanın sürümlü,
yeniden koşulabilir olması. Yayımlanan manifest o iddiayı ancak kendisini
üreten şeye bağlanabiliyorsa taşır: hangi commit, hangi aşama sürümleri,
hangi konfig, hangi model ağırlıkları, hangi paket sürümleri. Bunlar koşudan
sonra yeniden kurulamaz, o yüzden `export` sırasında `manifests/run.json`
olarak manifestonun yanına yazılır.

Paket sürümleri modülleri içe aktarmadan `importlib.metadata` ile okunur;
yalnız `--stages export` koşan bir çağrı torch yüklemek zorunda kalmasın.
"""

from __future__ import annotations

import datetime as _dt
import subprocess
from importlib import metadata
from pathlib import Path
from typing import Any, Mapping

#: Hattın çıktısını belirleyen paketler. torchaudio ayrıca iki model
#: ağırlığını da sabitler (pipelines.MMS_FA, pipelines.HDEMUCS_HIGH_MUSDB_PLUS);
#: silero-vad ağırlığı wheel'in içinde gelir.
PACKAGES = ("torch", "torchaudio", "faster-whisper", "ctranslate2", "transformers",
            "silero-vad", "ctc-forced-aligner", "soundfile", "numpy", "pyyaml")


def package_versions() -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for name in PACKAGES:
        try:
            out[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            out[name] = None
    return out


def git_state(root: Path | None = None) -> dict[str, Any]:
    """Commit, dal ve çalışma ağacının temiz olup olmadığı.

    `dirty` önemlidir: kirli bir ağaçtan üretilmiş manifest commit'e
    bakılarak yeniden üretilemez ve makalede öyle gösterilmemelidir.
    """
    root = root or Path(__file__).resolve().parent.parent
    def git(*args: str) -> str | None:
        try:
            return subprocess.run(("git", "-C", str(root), *args), capture_output=True,
                                  text=True, check=True).stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            return None
    commit = git("rev-parse", "HEAD")
    status = git("status", "--porcelain")
    return {"commit": commit,
            "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
            "dirty": None if status is None else bool(status),
            "describe": git("describe", "--always", "--dirty")}


def model_ids(cfg: Any) -> dict[str, Any]:
    """Ağırlık kimlikleri. torchaudio paketlerinin revizyonu yoktur; onları
    `packages.torchaudio` sabitler, bu yüzden burada sürümüyle anılırlar."""
    return {
        "asr": {"model": cfg.get("asr.model"), "revision": cfg.get("asr.revision")},
        "align": {"model": cfg.get("align.model"), "revision": None,
                  "pinned_by": "torchaudio"},
        "audioset": {"model": cfg.get("music.audioset_model"),
                     "revision": cfg.get("music.audioset_revision")},
        "separator": {"model": cfg.get("music.separator"), "revision": None,
                      "pinned_by": "torchaudio"},
        "vad": {"model": "silero-vad", "revision": None, "pinned_by": "silero-vad"},
    }


def run_record(cfg: Any, stage_versions: Mapping[str, str], counts: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "created": _dt.datetime.now().isoformat(timespec="seconds"),
        "git": git_state(),
        "stage_versions": dict(sorted(stage_versions.items())),
        "policy_version": str(cfg.get("recommended_subset.version", "")),
        "models": model_ids(cfg),
        "packages": package_versions(),
        "counts": dict(counts),
        # Konfigin tamamı: eşiklerin hiçbiri koda gömülü olmadığı için
        # manifestoyu yeniden üretmek isteyen bunu geri koyup koşabilir.
        # Yayımda `paths` yerel dizinleri taşır ve `source_path` gibi
        # redakte edilir.
        "config": cfg.data,
    }
