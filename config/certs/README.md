# Locally trusted CAs

Drop a PEM-encoded `*.crt` here if this machine runs software that intercepts
TLS (desktop antivirus, a corporate proxy). The Dockerfile installs everything
in this directory into the image's system trust store *and* appends it to
certifi's bundle, because httpx — which the Anthropic SDK uses — pins certifi
and ignores the system store.

Without this, every agent run fails with:

    httpx.ConnectError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify
    failed: self-signed certificate in certificate chain

The certificates are gitignored. They are specific to one machine's security
software and say nothing about the project; only this README and `.gitkeep`
are committed, so the `COPY` step works on a fresh clone.

Export one on Windows with PowerShell, e.g. for Kaspersky:

    $c = Get-ChildItem Cert:\LocalMachine\Root |
         Where-Object { $_.Subject -like "*Kaspersky*" } | Select-Object -First 1
    $b64 = [Convert]::ToBase64String($c.RawData, 'InsertLineBreaks')
    Set-Content config/certs/kaspersky-root.crt `
      "-----BEGIN CERTIFICATE-----`n$b64`n-----END CERTIFICATE-----" -Encoding ascii

Then rebuild: `docker compose build agents dashboard`.
