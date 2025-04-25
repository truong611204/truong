import sys
import json
import requests
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLineEdit, QTextEdit, QListWidget, QLabel, QMessageBox,
                             QDialog, QFormLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon
import websocket

# URL của server
SERVER_URL = "https://niltalk-server.onrender.com"
WS_URL = "wss://niltalk-server.onrender.com/ws"

class WebSocketThread(QThread):
    message_received = pyqtSignal(dict)

    def __init__(self, username):
        super().__init__()
        self.username = username
        self.ws = None
        self.running = True

    def run(self):
        self.ws = websocket.WebSocketApp(f"{WS_URL}/{self.username}",
                                        on_message=self.on_message,
                                        on_error=self.on_error,
                                        on_close=self.on_close)
        self.ws.run_forever()

    def on_message(self, ws, message):
        data = json.loads(message)
        self.message_received.emit(data)

    def on_error(self, ws, error):
        print(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("WebSocket closed")

    def send_message(self, data):
        if self.ws and self.ws.sock:
            self.ws.send(json.dumps(data))

    def stop(self):
        self.running = False
        if self.ws:
            self.ws.close()

# Dialog đăng nhập/đăng ký
class AuthDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Niltalk")
        self.setWindowIcon(QIcon("logo.png"))
        self.setFixedSize(400, 300)
        layout = QFormLayout()

        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        layout.addRow("Tên tài khoản:", self.username_input)
        layout.addRow("Mật khẩu:", self.password_input)

        button_layout = QHBoxLayout()
        self.login_btn = QPushButton("Đăng nhập")
        self.register_btn = QPushButton("Đăng ký")
        button_layout.addWidget(self.login_btn)
        button_layout.addWidget(self.register_btn)

        layout.addRow(button_layout)
        self.setLayout(layout)

        self.login_btn.clicked.connect(self.login)
        self.register_btn.clicked.connect(self.register)

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        if not username or not password:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ tên tài khoản và mật khẩu")
            return
        try:
            response = requests.post(f"{SERVER_URL}/login", json={"username": username, "password": password})
            if response.status_code == 200:
                self.accept()
            else:
                error_msg = response.json().get("error", f"Đăng nhập thất bại (mã lỗi: {response.status_code})")
                QMessageBox.warning(self, "Lỗi", error_msg)
        except requests.RequestException as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể kết nối đến server: {e}")

    def register(self):
        username = self.username_input.text()
        password = self.password_input.text()
        if not username or not password:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ tên tài khoản và mật khẩu")
            return
        try:
            response = requests.post(f"{SERVER_URL}/register", data={"username": username, "password": password})
            if response.status_code == 200:
                QMessageBox.information(self, "Thành công", "Đăng ký thành công!")
                self.username_input.clear()
                self.password_input.clear()
            else:
                error_msg = response.json().get("error", f"Đăng ký thất bại (mã lỗi: {response.status_code})")
                QMessageBox.critical(self, "Lỗi", error_msg)
        except requests.RequestException as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể kết nối đến server: {str(e)}")
# Cửa sổ chat chính
class ChatWindow(QMainWindow):
    def __init__(self, username, app):
        super().__init__()
        self.username = username
        self.app = app
        self.setWindowTitle(f"Niltalk - {username}")
        self.setWindowIcon(QIcon("logo.png"))
        self.setFixedSize(1000, 800)

        # Widget chính
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()

        # Danh sách người dùng
        user_layout = QVBoxLayout()
        self.user_list = QListWidget()
        self.refresh_users()
        user_layout.addWidget(QLabel("Danh sách người dùng:"))
        user_layout.addWidget(self.user_list)

        # Khu vực chat
        chat_layout = QVBoxLayout()
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.message_input = QLineEdit()
        self.message_input.returnPressed.connect(self.send_message)
        self.send_btn = QPushButton("Gửi")
        self.logout_btn = QPushButton("Đăng xuất")

        chat_layout.addWidget(QLabel("Tin nhắn:"))
        chat_layout.addWidget(self.chat_display)
        chat_layout.addWidget(self.message_input)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.send_btn)
        button_layout.addWidget(self.logout_btn)
        chat_layout.addLayout(button_layout)

        main_layout.addLayout(user_layout)
        main_layout.addLayout(chat_layout)
        central_widget.setLayout(main_layout)

        # Kết nối sự kiện
        self.send_btn.clicked.connect(self.send_message)
        self.logout_btn.clicked.connect(self.logout)
        self.user_list.itemClicked.connect(self.view_messages)

        # Khởi động WebSocket
        self.ws_thread = WebSocketThread(username)
        self.ws_thread.message_received.connect(self.handle_message)
        self.ws_thread.start()

    def refresh_users(self):
        self.user_list.clear()
        try:
            response = requests.get(f"{SERVER_URL}/users")
            if response.status_code == 200:
                users = response.json()["users"]
                for user in users:
                    if user != self.username:
                        self.user_list.addItem(user)
        except requests.RequestException as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể tải danh sách người dùng: {e}")

    def send_message(self):
        receiver = self.user_list.currentItem()
        if not receiver:
            QMessageBox.warning(self, "Lỗi", "Vùi lòng chọn người nhận!")
            return
        receiver = receiver.text()
        message = self.message_input.text()
        if not message:
            QMessageBox.warning(self, "Lỗi", "Tin nhắn không được để trống!")
            return
        data = {
            "sender": self.username,
            "receiver": receiver,
            "message": message,
        }
        self.ws_thread.send_message(data)
        self.message_input.clear()

    def handle_message(self, data):
        if (data["sender"] == self.username or data["receiver"] == self.username):
            selected_user = self.user_list.currentItem()
            if selected_user and (data["sender"] == selected_user.text() or data["receiver"] == selected_user.text()):
                prefix = "Bạn: " if data["sender"] == self.username else f"{data['sender']}: "
                self.chat_display.append(f"[{data['timestamp']}] {prefix}{data['message']}")

    def view_messages(self):
        self.chat_display.clear()
        try:
            response = requests.get(f"{SERVER_URL}/users")  # Giả sử server có API để lấy tin nhắn
            if response.status_code == 200:
                data = read_data()
                messages = data["messages"].get(self.username, [])
                selected_user = self.user_list.currentItem()
                for msg in messages:
                    if selected_user and (msg["sender"] == selected_user.text() or msg["receiver"] == selected_user.text()):
                        prefix = "Bạn: " if msg["sender"] == self.username else f"{msg['sender']}: "
                        self.chat_display.append(f"[{msg['timestamp']}] {prefix}{msg['message']}")
        except requests.RequestException as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể tải tin nhắn: {e}")

    def logout(self):
        self.ws_thread.stop()
        self.close()
        self.app.show_auth_dialog()

    def closeEvent(self, event):
        self.ws_thread.stop()
        event.accept()

# Ứng dụng chính
class ChatApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.show_auth_dialog()

    def show_auth_dialog(self):
        dialog = AuthDialog()
        if dialog.exec_():
            username = dialog.username_input.text()
            self.main_window = ChatWindow(username, self)
            self.main_window.show()

if __name__ == "__main__":
    app = ChatApp(sys.argv)
    sys.exit(app.exec_())