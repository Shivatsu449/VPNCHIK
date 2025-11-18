import sys
import subprocess
import threading
import requests
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QTextEdit, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class OpenVPNClient(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python OpenVPN Client")
        self.setFixedSize(700, 500)

        self.ovpn_file = None
        self.ovpn_process = None
        self.thread = None
        self.ip_thread = None
        self.stop_ip_thread = False

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("Python OpenVPN Client", self)
        title.setFont(QFont("Arial", 22))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.select_file_btn = QPushButton("Выбрать .ovpn файл", self)
        self.select_file_btn.clicked.connect(self.select_ovpn)
        layout.addWidget(self.select_file_btn)

        self.connect_btn = QPushButton("Подключиться", self)
        self.connect_btn.clicked.connect(self.connect_vpn)
        layout.addWidget(self.connect_btn)

        self.disconnect_btn = QPushButton("Отключиться", self)
        self.disconnect_btn.clicked.connect(self.disconnect_vpn)
        layout.addWidget(self.disconnect_btn)

        self.log_area = QTextEdit(self)
        self.log_area.setReadOnly(True)
        self.log_area.setPlaceholderText("Логи подключения OpenVPN...")
        layout.addWidget(self.log_area)

        self.ip_label = QLabel("Текущий IP: Не подключен", self)
        layout.addWidget(self.ip_label)

        self.setLayout(layout)

    def select_ovpn(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Выберите .ovpn файл", "", "OpenVPN Files (*.ovpn)")
        if file_name:
            self.ovpn_file = file_name
            self.log_area.append(f"Выбран файл: {file_name}")

    def connect_vpn(self):
        if not self.ovpn_file:
            QMessageBox.warning(self, "Ошибка", "Выберите .ovpn файл!")
            return
        if self.ovpn_process:
            QMessageBox.information(self, "VPN", "Уже подключены!")
            return

        OPENVPN_PATH = r"C:\Program Files\OpenVPN\bin\openvpn.exe"  # укажи путь к openvpn.exe
        try:
            self.ovpn_process = subprocess.Popen(
                [OPENVPN_PATH, "--config", self.ovpn_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            self.log_area.append(f"Подключение к {self.ovpn_file}...")

            # Поток для логов OpenVPN
            self.thread = threading.Thread(target=self.read_logs, daemon=True)
            self.thread.start()

            # Поток для проверки внешнего IP
            self.stop_ip_thread = False
            self.ip_thread = threading.Thread(target=self.check_ip_loop, daemon=True)
            self.ip_thread.start()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось подключиться: {e}")

    def read_logs(self):
        for line in self.ovpn_process.stdout:
            self.log_area.append(line.strip())
        self.ovpn_process = None

    def disconnect_vpn(self):
        if self.ovpn_process:
            self.ovpn_process.terminate()
            self.ovpn_process.wait(timeout=5)
            self.ovpn_process = None
            self.stop_ip_thread = True
            self.log_area.append("Отключено!")
            self.ip_label.setText("Текущий IP: Не подключен")
        else:
            QMessageBox.information(self, "VPN", "Вы не подключены!")

    def check_ip_loop(self):
        while not self.stop_ip_thread:
            try:
                r = requests.get("https://api.ipify.org?format=text", timeout=5)
                ip = r.text.strip()
                self.ip_label.setText(f"Текущий IP: {ip}")
            except:
                self.ip_label.setText("Текущий IP: Не удалось определить")
            finally:
                threading.Event().wait(5)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OpenVPNClient()
    window.show()
    sys.exit(app.exec())
