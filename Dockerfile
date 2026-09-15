FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Local TLS interception breaks certificate verification inside the container.
# Desktop antivirus on the host (here: Kaspersky) re-signs every outbound
# connection with its own root, which neither the system store nor certifi
# knows about, so every Anthropic API call fails with CERTIFICATE_VERIFY_FAILED.
# Any *.crt dropped into config/certs/ is trusted here. httpx pins certifi
# rather than reading the system store, so the bundle has to be appended too.
# The certs themselves are gitignored -- machine-specific, not project content.
COPY config/certs/ /usr/local/share/ca-certificates/local/
RUN update-ca-certificates  && cat /usr/local/share/ca-certificates/local/*.crt       >> "$(python -c 'import certifi; print(certifi.where())')" || true

COPY . .

CMD ["python", "-m", "agents.team_leader"]
