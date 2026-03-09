"""Root certificate import module for Windows.

Uses certutil to import certificates into the Windows certificate store.
"""

import os
import subprocess
import sys


def get_cert_path() -> str:
    """Get the path to the bundled root CA certificate.

    Handles both normal execution and PyInstaller bundled execution.
    """
    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "assets", "root_ca.cer")


def is_cert_file_valid(cert_path: str) -> bool:
    """Check if the certificate file exists and is not a placeholder."""
    if not os.path.exists(cert_path):
        return False
    with open(cert_path, "r", errors="replace") as f:
        content = f.read(100)
    if content.startswith("PLACEHOLDER"):
        return False
    return True


def import_root_cert() -> tuple[bool, str]:
    """Import the bundled root CA certificate into the Windows Trusted Root store."""
    cert_path = get_cert_path()

    if not is_cert_file_valid(cert_path):
        return False, (
            "証明書ファイルが見つからないか、プレースホルダーのままです。\n"
            f"パス: {cert_path}\n"
            "実際のルートCA証明書ファイルに置き換えてください。"
        )

    result = subprocess.run(
        f'certutil -addstore "Root" "{cert_path}"',
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode == 0:
        return True, "ルート証明書を正常にインポートしました"
    return False, f"証明書インポート失敗: {result.stdout} {result.stderr}"


def check_cert_imported() -> tuple[bool, str]:
    """Check if a root certificate from the bundled file is already imported.

    This is a best-effort check using certutil.
    """
    cert_path = get_cert_path()
    if not is_cert_file_valid(cert_path):
        return False, "証明書ファイルが無効です"

    # Try to verify the cert against the Root store
    result = subprocess.run(
        f'certutil -verify "{cert_path}"',
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode == 0:
        return True, "証明書は既にインストール済みです"
    return False, "証明書は未インストールです"
