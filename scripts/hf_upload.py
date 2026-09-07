#!/usr/bin/env python
"""Korpusu Hugging Face Hub'a shard shard yükle.

`datasets.push_to_hub` bütün parçaları önce yükleyip en sonda tek commit
atar: 277 GB'lik bir yüklemede depo saatlerce boş görünür ve kesinti olursa
hiçbir şey kalmaz. Bu betik aynı parquet düzenini üretir
(`data/<bölme>-<i>-of-<n>.parquet`) ama **her parçayı tek başına commit
eder**: parçalar Hub'da tek tek görünür, kesintiden sonra aynı komut kaldığı
yerden devam eder (depoda zaten duran parça atlanır) ve her parçadan sonra
hız ile kalan süre günlüğe yazılır.

Ses parçaların içine gömülür (24 kHz FLAC); veri kümesini indiren ayrıca
ses dosyası çekmez.

    # yerel doğrulama, hiçbir şey yüklenmez
    python scripts/hf_upload.py --dry-run

    # gerçek yükleme (varsayılan private)
    HF_TOKEN=... python scripts/hf_upload.py --repo kullanici/kiraat
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kiraat.hf import SAMPLE_RATE, SPLITS, iter_split, storage_features  # noqa: E402

WRITER_BATCH = 100
MAX_ATTEMPTS = 6


def human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024 or unit == "TB":
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def clock(sec: float) -> str:
    sec = int(max(0, sec))
    return f"{sec // 3600} sa {sec % 3600 // 60} dk"


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def build(path: Path, split: str, cache: Path):
    """Bölmeyi Arrow'a yaz, sonra ses sütununu `Audio`ya çevir.

    Çevirme şart: `embed_table_storage` yalnızca `Audio` sütununu tanır ve
    dosyayı okuyup baytı gömer. Çevrilmezse parçalar yalnızca dosya yolu
    taşır ve 277 GB'lık korpus 1 MB'lık parquet olarak çıkar."""
    from datasets import Audio, Dataset

    ds = Dataset.from_generator(
        iter_split, gen_kwargs={"path": str(path), "split": split},
        features=storage_features(SAMPLE_RATE), writer_batch_size=WRITER_BATCH,
        cache_dir=str(cache / split))
    return ds.cast_column("audio", Audio(sampling_rate=SAMPLE_RATE))


def bytes_per_second(path: Path, sample: int = 200) -> float:
    """Klip dosyalarından saniye başına bayt; parça sayısı bundan çıkar.

    Arrow'un bildirdiği boyut sesi içermez (baytlar gömülmeden önce yalnızca
    yol vardır), bu yüzden hedef parça boyutu gerçek dosya boyutlarından
    kestirilir."""
    toplam_bayt = toplam_sn = 0.0
    with path.open(encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            if i >= sample:
                break
            row = json.loads(line)
            try:
                toplam_bayt += Path(row["audio"]).stat().st_size
            except OSError:
                continue
            toplam_sn += float(row["duration"])
    return toplam_bayt / toplam_sn if toplam_sn else 0.0


def shard_count(ds, path: Path, target_bytes: int) -> int:
    sure = sum(ds["duration"]) if len(ds) else 0.0
    tahmin = sure * bytes_per_second(path)
    n = max(1, round(tahmin / target_bytes)) if tahmin else 1
    return max(1, min(n, len(ds)))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", default="work/full-1")
    p.add_argument("--repo", help="örn: kullanici/kiraat")
    p.add_argument("--shard-size", default="400MB")
    p.add_argument("--public", action="store_true", help="varsayılan private")
    p.add_argument("--card", default="docs/DATASET_CARD.md")
    p.add_argument("--splits", nargs="+", default=list(SPLITS))
    p.add_argument("--dry-run", action="store_true", help="yerelde doğrula, yükleme")
    p.add_argument("--limit-shards", type=int, default=0, help="deneme için ilk N parça")
    args = p.parse_args()

    from datasets import Audio
    from datasets.table import embed_table_storage
    from datasets.utils.py_utils import convert_file_size_to_int

    work = Path(args.work_root)
    manifests = work / "manifests"
    cache = work / "hf-cache"
    target = convert_file_size_to_int(args.shard_size)

    api = repo = None
    mevcut: set[str] = set()
    if not args.dry_run:
        from huggingface_hub import HfApi
        if not args.repo:
            p.error("--repo yükleme için zorunlu; yerel kontrol için --dry-run")
        token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
        if not token:
            p.error("HF_TOKEN ortam değişkeni yok")
        api = HfApi(token=token)
        repo = args.repo
        api.create_repo(repo, repo_type="dataset", private=not args.public, exist_ok=True)
        mevcut = {f for f in api.list_repo_files(repo, repo_type="dataset")}
        log(f"depo {repo} (private={not args.public}) | mevcut dosya {len(mevcut)}")

    toplam_bayt = 0.0
    t0 = time.time()
    for split in args.splits:
        src = manifests / f"split-{split}.jsonl"
        if not src.exists():
            log(f"{split}: {src} yok, atlanıyor")
            continue
        ds = build(src, split, cache)
        n = shard_count(ds, src, target)
        if args.limit_shards:
            n = min(n, args.limit_shards)
        log(f"{split}: {len(ds)} klip, {n} parça (hedef {args.shard_size})")
        for i in range(n):
            ad = f"data/{split}-{i:05d}-of-{n:05d}.parquet"
            if ad in mevcut:
                continue
            parca = ds.shard(num_shards=n, index=i, contiguous=True)
            tablo = embed_table_storage(parca.with_format("arrow").data.table)
            with tempfile.NamedTemporaryFile(suffix=".parquet", delete=True) as tmp:
                import pyarrow.parquet as pq
                pq.write_table(tablo, tmp.name, compression="zstd")
                boyut = Path(tmp.name).stat().st_size
                toplam_bayt += boyut
                if args.dry_run:
                    log(f"  {ad}: {len(parca)} klip, {human(boyut)} (kuru koşu)")
                    if args.limit_shards and i + 1 >= args.limit_shards:
                        break
                    continue
                from huggingface_hub import CommitOperationAdd
                for deneme in range(1, MAX_ATTEMPTS + 1):
                    try:
                        api.create_commit(
                            repo_id=repo, repo_type="dataset",
                            operations=[CommitOperationAdd(path_in_repo=ad,
                                                           path_or_fileobj=tmp.name)],
                            commit_message=f"{ad}")
                        break
                    except Exception as exc:  # ağ hatası: geri çekilerek yeniden dene
                        if deneme == MAX_ATTEMPTS:
                            raise
                        bekle = 2 ** deneme
                        log(f"  {ad}: hata ({type(exc).__name__}), {bekle} s sonra yeniden")
                        time.sleep(bekle)
            gecen = time.time() - t0
            log(f"  {ad}: {len(parca)} klip, {human(boyut)} | toplam {human(toplam_bayt)} | "
                f"{human(toplam_bayt / gecen)}/s")

    if not args.dry_run and Path(args.card).exists():
        api.upload_file(repo_id=repo, repo_type="dataset",
                        path_or_fileobj=args.card, path_in_repo="README.md",
                        commit_message="veri kartı")
        log("kart yüklendi (README.md)")
    log(f"bitti: {human(toplam_bayt)}, {clock(time.time() - t0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
