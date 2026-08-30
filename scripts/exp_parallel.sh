#!/usr/bin/env bash
# Dağıtıcı özdeşlik ve hız deneyi: aynı örneklem sıralı, paralel (gpu 1) ve
# paralel (gpu 2) koşulur; manifestolar sütun sütun karşılaştırılır, süreler
# basılır. Kullanım: scripts/exp_parallel.sh <work_kök> [ek kiraat run argümanları]
set -euo pipefail
PY=/home/serdar/miniconda3/envs/main/bin/python
ROOT=${1:?work kök}; shift
SEL=("$@")
run() {  # ad, ek argümanlar...
  local name=$1; shift
  local t0=$(date +%s)
  $PY -m kiraat run --work-root "$ROOT/$name" "${SEL[@]}" "$@" > "$ROOT/$name.log" 2>&1
  local t1=$(date +%s)
  echo "$name: $((t1 - t0)) s" | tee -a "$ROOT/times.txt"
}
mkdir -p "$ROOT"; : > "$ROOT/times.txt"
run serial --serial
run par1 --gpu-workers 1
run par2 --gpu-workers 2
echo "== serial ↔ par1"; $PY scripts/compare_manifests.py "$ROOT/serial/manifests/clips.jsonl" "$ROOT/par1/manifests/clips.jsonl" || true
echo "== serial ↔ par2"; $PY scripts/compare_manifests.py "$ROOT/serial/manifests/clips.jsonl" "$ROOT/par2/manifests/clips.jsonl" || true
cat "$ROOT/times.txt"
