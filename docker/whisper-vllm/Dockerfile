# Whisper'ı vLLM ile servis eden imaj — verbose_json ve PARÇA düzeyi zaman
# damgası döndüren sürüm (vLLM ≥ 0.12; PR #24209). Kelime düzeyi damga
# vLLM'de yok (#13400 "not planned"); kelime damgası için kiraat'ın
# zorlamalı hizalama aşaması kullanılır.
ARG VLLM_TAG=v0.27.1
FROM vllm/vllm-openai:${VLLM_TAG}
RUN pip install --no-cache-dir librosa soundfile
ENV CUDA_DEVICE_ORDER=PCI_BUS_ID
EXPOSE 8001
ENTRYPOINT ["vllm", "serve"]
CMD ["openai/whisper-large-v3", "--host", "0.0.0.0", "--port", "8001", "--dtype", "auto", "--gpu-memory-utilization", "0.25"]
