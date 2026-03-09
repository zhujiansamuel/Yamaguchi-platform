"""Root certificate import module for Windows.

Uses certutil to import certificates into the Windows certificate store.
"""

import os
import subprocess
import sys


CERT_FILES = ["root_ca_1.cer", "root_ca_2.cer"]


def get_assets_dir() -> str:
    """Get the path to the assets directory.

    Handles both normal execution and PyInstaller bundled execution.
    """
    if getattr(sys, "frozen", False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "assets")


def is_cert_file_valid(cert_path: str) -> bool:
    """Check if the certificate file exists and is not a placeholder."""
    if not os.path.exists(cert_path):
        return False
    with open(cert_path, "r", errors="replace") as f:
        content = f.read(100)
    if content.startswith("PLACEHOLDER"):
        return False
    return True


def import_root_certs() -> list[tuple[bool, str]]:
    """Import all bundled root CA certificates into the Windows Trusted Root store."""
    assets_dir = get_assets_dir()
    results = []

    for cert_file in CERT_FILES:
        cert_path = os.path.join(assets_dir, cert_file)

        if not is_cert_file_valid(cert_path):
            results.append((False, (
                f"[{cert_file}] 証明書ファイルが見つからないか、"
                f"プレースホルダーのままです。\n"
                f"パス: {cert_path}"
            )))
            continue

        result = subprocess.run(
            f'certutil -addstore "Root" "{cert_path}"',
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if result.returncode == 0:
            results.append((True, f"[{cert_file}] ルート証明書を正常にインポートしました"))
        else:
            results.append((False,
                f"[{cert_file}] 証明書インポート失敗: {result.stdout} {result.stderr}"
            ))

    return results
