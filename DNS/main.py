"""DNS Configuration Tool - PyQt5 GUI Application.

A tool to configure internal network DNS, disable IPv6,
and import root CA certificates on Windows.
"""

import ctypes
import sys
from datetime import datetime

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import cert_manager
import dns_config


def is_admin() -> bool:
    """Check if the current process has administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def run_as_admin():
    """Re-launch the current script with administrator privileges."""
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit(0)


class WorkerThread(QThread):
    """Background thread for running network configuration tasks."""

    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, task: str):
        super().__init__()
        self.task = task

    def run(self):
        timestamp = datetime.now().strftime("%H:%M:%S")

        if self.task == "apply":
            self.log_signal.emit(f"[{timestamp}] === 内網設定を適用中 ===")

            # Import certificates
            self.log_signal.emit(f"[{timestamp}] ルート証明書をインポート中...")
            results = cert_manager.import_root_certs()
            for ok, msg in results:
                t = datetime.now().strftime("%H:%M:%S")
                self.log_signal.emit(f"[{t}] {msg}")

            # Apply DNS + disable IPv6
            self.log_signal.emit(f"[{timestamp}] DNS設定 / IPv6無効化中...")
            logs = dns_config.apply_all()
            for log in logs:
                t = datetime.now().strftime("%H:%M:%S")
                self.log_signal.emit(f"[{t}] {log}")

            self.log_signal.emit(f"[{timestamp}] === 設定完了 ===\n")

        elif self.task == "restore":
            self.log_signal.emit(f"[{timestamp}] === 設定を復元中 ===")

            # Restore DNS + enable IPv6
            logs = dns_config.restore_all()
            for log in logs:
                t = datetime.now().strftime("%H:%M:%S")
                self.log_signal.emit(f"[{t}] {log}")

            self.log_signal.emit(f"[{timestamp}] === 復元完了 ===\n")

        elif self.task == "refresh":
            adapters = dns_config.get_active_adapters()
            if not adapters:
                self.log_signal.emit(f"[{timestamp}] アダプタが検出されませんでした")
            for adapter in adapters:
                dns = dns_config.get_dns_for_adapter(adapter)
                ipv6 = dns_config.get_ipv6_status(adapter)
                ipv6_text = "有効" if ipv6 else "無効"
                self.log_signal.emit(
                    f"[{timestamp}] {adapter}: DNS={dns}, IPv6={ipv6_text}"
                )

        self.finished_signal.emit()


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.worker = None
        self.init_ui()
        self.refresh_status()

    def init_ui(self):
        self.setWindowTitle("内網 DNS 設定ツール")
        self.setFixedSize(560, 520)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # --- Title ---
        title = QLabel("内網 DNS 設定ツール")
        title.setFont(QFont("Meiryo UI", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # --- Info Group ---
        info_group = QGroupBox("設定情報")
        info_layout = QVBoxLayout(info_group)

        self.dns_label = QLabel(f"DNS サーバー: {dns_config.DNS_SERVER}")
        self.dns_label.setFont(QFont("Meiryo UI", 10))
        info_layout.addWidget(self.dns_label)

        self.status_label = QLabel("状態: 読み込み中...")
        self.status_label.setFont(QFont("Meiryo UI", 10))
        self.status_label.setWordWrap(True)
        info_layout.addWidget(self.status_label)

        layout.addWidget(info_group)

        # --- Buttons ---
        btn_layout = QHBoxLayout()

        self.apply_btn = QPushButton("一括設定（内網）")
        self.apply_btn.setFixedHeight(48)
        self.apply_btn.setFont(QFont("Meiryo UI", 11, QFont.Bold))
        self.apply_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: #0078D4; color: white; border-radius: 6px;"
            "}"
            "QPushButton:hover { background-color: #106EBE; }"
            "QPushButton:disabled { background-color: #CCCCCC; }"
        )
        self.apply_btn.clicked.connect(self.on_apply)
        btn_layout.addWidget(self.apply_btn)

        self.restore_btn = QPushButton("一括復元（デフォルト）")
        self.restore_btn.setFixedHeight(48)
        self.restore_btn.setFont(QFont("Meiryo UI", 11, QFont.Bold))
        self.restore_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: #E81123; color: white; border-radius: 6px;"
            "}"
            "QPushButton:hover { background-color: #C50F1F; }"
            "QPushButton:disabled { background-color: #CCCCCC; }"
        )
        self.restore_btn.clicked.connect(self.on_restore)
        btn_layout.addWidget(self.restore_btn)

        layout.addLayout(btn_layout)

        # --- Refresh button ---
        self.refresh_btn = QPushButton("状態を更新")
        self.refresh_btn.setFixedHeight(32)
        self.refresh_btn.setFont(QFont("Meiryo UI", 9))
        self.refresh_btn.clicked.connect(self.refresh_status)
        layout.addWidget(self.refresh_btn)

        # --- Log area ---
        log_group = QGroupBox("操作ログ")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setMinimumHeight(180)
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group)

    def set_buttons_enabled(self, enabled: bool):
        self.apply_btn.setEnabled(enabled)
        self.restore_btn.setEnabled(enabled)
        self.refresh_btn.setEnabled(enabled)

    def append_log(self, text: str):
        self.log_text.append(text)
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def on_worker_finished(self):
        self.set_buttons_enabled(True)
        self.worker = None

    def run_task(self, task: str):
        if self.worker and self.worker.isRunning():
            return
        self.set_buttons_enabled(False)
        self.worker = WorkerThread(task)
        self.worker.log_signal.connect(self.append_log)
        self.worker.finished_signal.connect(self.on_worker_finished)
        self.worker.start()

    def on_apply(self):
        reply = QMessageBox.question(
            self,
            "確認",
            f"以下の操作を実行します:\n\n"
            f"1. ルート証明書（2件）をインポート\n"
            f"2. DNS を {dns_config.DNS_SERVER} に設定\n"
            f"3. IPv6 を無効化\n\n"
            f"すべてのアクティブなアダプタに適用されます。\n"
            f"続行しますか？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.run_task("apply")

    def on_restore(self):
        reply = QMessageBox.question(
            self,
            "確認",
            "以下の操作を実行します:\n\n"
            "1. DNS を DHCP (自動取得) に戻す\n"
            "2. IPv6 を有効化\n\n"
            "すべてのアクティブなアダプタに適用されます。\n"
            "続行しますか？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.run_task("restore")

    def refresh_status(self):
        self.status_label.setText("状態: 確認中...")
        self.run_task("refresh")


def main():
    # Check for admin privileges
    if not is_admin():
        reply = QMessageBox.question(
            None,
            "管理者権限が必要",
            "このツールはネットワーク設定を変更するため、\n"
            "管理者権限で実行する必要があります。\n\n"
            "管理者として再起動しますか？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply == QMessageBox.Yes:
            run_as_admin()
        else:
            sys.exit(1)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
