# CPU-only security pilot. NEVER use this image for unsandboxed production.
# Docker Official Ubuntu 22.04 base pinned by published immutable OCI index.
FROM docker.io/library/ubuntu@sha256:f64b2ffc2f10ab8f8505aa56b2664bd846cbb9df87c7e2532e30f7667021c0e6
LABEL org.coden.llama_archive_sha256="da524c71f9dd09913df29264bb7229b99a2de82d8a26e6902e6921d413560d6d" \
      org.coden.qwen_weights_sha256="1d9614638d18024d0fbb36575a15f1302a3adf044df10345688ec4f6e1c4ff32" \
      org.coden.ubuntu_base="docker.io/library/ubuntu@sha256:f64b2ffc2f10ab8f8505aa56b2664bd846cbb9df87c7e2532e30f7667021c0e6" \
      org.coden.pilot_scope="read-only-synthetic-internal-llama-server"
COPY --chown=65534:65534 llama-b12600/ /opt/llama/
COPY --chown=65534:65534 qwen-model.gguf /opt/model.gguf
ENV LD_LIBRARY_PATH=/opt/llama
USER 65534:65534
ENTRYPOINT ["/opt/llama/llama-server"]
