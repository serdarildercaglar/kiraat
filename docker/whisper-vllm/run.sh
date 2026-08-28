#!/usr/bin/env bash
# Kur ve başlat. Mevcut `whisper-vllm` (0.11, port 8000) konteynerine dokunmaz.
#   ./run.sh build          imajı kur (whisper-vllm:v0.27.1)
#   ./run.sh start [MODEL]  konteyneri başlat (varsayılan openai/whisper-large-v3, port 8001)
#   ./run.sh test  FILE     verbose_json ile istek at, ham yanıtı bas
set -euo pipefail
TAG=${VLLM_TAG:-v0.27.1}
IMAGE=whisper-vllm:${TAG}
NAME=whisper-vllm-ts
PORT=${PORT:-8001}
case "${1:-}" in
  build) docker build --build-arg VLLM_TAG="$TAG" -t "$IMAGE" "$(dirname "$0")" ;;
  start)
    MODEL=${2:-openai/whisper-large-v3}
    docker rm -f "$NAME" >/dev/null 2>&1 || true
    docker run -d --name "$NAME" --gpus all --ipc=host -p "$PORT:$PORT" \
      -v "$HOME/.cache/huggingface:/root/.cache/huggingface" "$IMAGE" \
      "$MODEL" --host 0.0.0.0 --port "$PORT" --dtype auto --gpu-memory-utilization 0.25
    echo "bekleniyor..."; for i in $(seq 1 120); do curl -s -m 2 "http://localhost:$PORT/v1/models" >/dev/null && break; sleep 5; done
    curl -s "http://localhost:$PORT/v1/models" ;;
  test)
    curl -s "http://localhost:$PORT/v1/audio/transcriptions" -F "file=@$2" \
      -F model="${3:-openai/whisper-large-v3}" -F language=tr -F response_format=verbose_json \
      -F "timestamp_granularities[]=word" -F "timestamp_granularities[]=segment" ;;
  *) echo "kullanım: $0 build | start [MODEL] | test FILE [MODEL]"; exit 1 ;;
esac
