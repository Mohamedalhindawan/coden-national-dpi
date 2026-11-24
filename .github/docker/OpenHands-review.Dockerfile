# linux/amd64 only. Copy the official frozen server without executing either image.
FROM ghcr.io/openhands/agent-server@sha256:9a36355fa2baacaae1c6dd5a1a80492bba89d1dec5a536af572ba5fb3e96e22f AS upstream
FROM docker.io/library/ubuntu@sha256:9a04f13b3f80ef056361e30868593b1cfd2279fe19e4081cb93a90bf56819d6a
COPY --from=upstream /usr/local/bin/openhands-agent-server /usr/local/bin/openhands-agent-server
USER 65534:65534
ENTRYPOINT ["/usr/local/bin/openhands-agent-server"]
CMD []
