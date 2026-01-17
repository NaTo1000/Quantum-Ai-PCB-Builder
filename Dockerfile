FROM alpine:3.19

LABEL org.opencontainers.image.title="Quantum-Ai-PCB-Builder" \
      org.opencontainers.image.description="Container image for Quantum-Ai-PCB-Builder" \
      org.opencontainers.image.version="0.1.0"

WORKDIR /app
COPY entrypoint.sh /app/entrypoint.sh
COPY README.md /app/README.md

RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
