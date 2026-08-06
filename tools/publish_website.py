"""Publish the chosen editorial website concept to the external FTPS host.

Runs on the host (not inside the agents Docker container), since it shells
out to the `sops` binary to decrypt config/ftp.secrets.enc.env at runtime.
Independent of the agent sprint pipeline -- this is founder-run infra, not
an agent task.

Usage: python tools/publish_website.py
"""
import os
import subprocess
from ftplib import FTP_TLS

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOPS_EXE = (
    r"C:\Users\micro\AppData\Local\Microsoft\WinGet\Packages"
    r"\SecretsOPerationS.SOPS_Microsoft.Winget.Source_8wekyb3d8bbwe\sops.exe"
)
SECRETS_FILE = os.path.join(REPO_ROOT, "config", "ftp.secrets.enc.env")

SITE_HTML = os.path.join(REPO_ROOT, "workspace", "outputs", "site-concept-1-editorial.html")
TEAM_PHOTOS_DIR = os.path.join(REPO_ROOT, "workspace", "outputs", "team-photos")
SPRINT_REPORTS_DIR = os.path.join(REPO_ROOT, "workspace", "outputs", "sprint-reports")
INFRA_DIAGRAM = os.path.join(REPO_ROOT, "workspace", "outputs", "infrastructure-diagram.png")
IMPRESSUM_HTML = os.path.join(REPO_ROOT, "workspace", "outputs", "impressum.html")
PRIVACY_HTML = os.path.join(REPO_ROOT, "workspace", "outputs", "privacy.html")

REMOTE_HTML_NAME = "index.html"
REMOTE_PHOTOS_DIR = "team-photos"
REMOTE_SPRINT_REPORTS_DIR = "sprint-reports"
REMOTE_INFRA_DIAGRAM_NAME = "infrastructure-diagram.png"
REMOTE_IMPRESSUM_NAME = "impressum.html"
REMOTE_PRIVACY_NAME = "privacy.html"


def load_ftp_secrets() -> dict:
    result = subprocess.run(
        [SOPS_EXE, "-d", SECRETS_FILE], capture_output=True, text=True, check=True
    )
    secrets = {}
    for line in result.stdout.splitlines():
        if "=" in line:
            key, _, value = line.partition("=")
            secrets[key.strip()] = value.strip()
    return secrets


def connect(secrets: dict) -> FTP_TLS:
    ftps = FTP_TLS()
    ftps.connect(secrets["FTP_HOST"], int(secrets["FTP_PORT"]))
    ftps.auth()
    ftps.login(secrets["FTP_USER"], secrets["FTP_PASSWORD"])
    ftps.prot_p()
    return ftps


def ensure_remote_dir(ftps: FTP_TLS, dirname: str) -> None:
    try:
        ftps.mkd(dirname)
    except Exception:
        pass


def upload_file(ftps: FTP_TLS, local_path: str, remote_name: str) -> None:
    with open(local_path, "rb") as f:
        ftps.storbinary(f"STOR {remote_name}", f)


def run() -> None:
    secrets = load_ftp_secrets()
    ftps = connect(secrets)
    print(f"Connected to {secrets['FTP_HOST']} as {secrets['FTP_USER']}")

    upload_file(ftps, SITE_HTML, REMOTE_HTML_NAME)
    print(f"Uploaded {SITE_HTML} -> {REMOTE_HTML_NAME}")

    upload_file(ftps, INFRA_DIAGRAM, REMOTE_INFRA_DIAGRAM_NAME)
    print(f"Uploaded {INFRA_DIAGRAM} -> {REMOTE_INFRA_DIAGRAM_NAME}")

    upload_file(ftps, IMPRESSUM_HTML, REMOTE_IMPRESSUM_NAME)
    print(f"Uploaded {IMPRESSUM_HTML} -> {REMOTE_IMPRESSUM_NAME}")

    upload_file(ftps, PRIVACY_HTML, REMOTE_PRIVACY_NAME)
    print(f"Uploaded {PRIVACY_HTML} -> {REMOTE_PRIVACY_NAME}")

    ensure_remote_dir(ftps, REMOTE_PHOTOS_DIR)
    ftps.cwd(REMOTE_PHOTOS_DIR)
    for filename in os.listdir(TEAM_PHOTOS_DIR):
        local_path = os.path.join(TEAM_PHOTOS_DIR, filename)
        if os.path.isfile(local_path):
            upload_file(ftps, local_path, filename)
            print(f"Uploaded {filename} -> {REMOTE_PHOTOS_DIR}/{filename}")
    ftps.cwd("..")

    ensure_remote_dir(ftps, REMOTE_SPRINT_REPORTS_DIR)
    ftps.cwd(REMOTE_SPRINT_REPORTS_DIR)
    for filename in os.listdir(SPRINT_REPORTS_DIR):
        local_path = os.path.join(SPRINT_REPORTS_DIR, filename)
        if os.path.isfile(local_path):
            upload_file(ftps, local_path, filename)
            print(f"Uploaded {filename} -> {REMOTE_SPRINT_REPORTS_DIR}/{filename}")

    ftps.quit()
    print("Done.")


if __name__ == "__main__":
    run()
