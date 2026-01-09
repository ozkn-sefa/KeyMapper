import sys
import os
import json
import threading
import time
import ctypes
import subprocess
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QListWidget,
    QFileDialog, QMessageBox, QFrame, QListWidgetItem, QScrollArea, QGroupBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor

from pynput import mouse
from PIL import Image, ImageDraw
import pystray

# -------------------- AYARLAR --------------------
BASE_DIR = Path(__file__).resolve().parent
DLL_PATH = str(BASE_DIR / "klavye.dll")
MAP_FILE = "keymap_gui.json"
DEBOUNCE_SEC = 0.4

VK_VOLUME_UP, VK_VOLUME_DOWN = 0xAF, 0xAE
VK_VOLUME_MUTE, VK_MEDIA_PLAY_PAUSE = 0xAD, 0xB3
VK_MEDIA_NEXT_TRACK, VK_MEDIA_PREV_TRACK = 0xB0, 0xB1


def send_media_key(vk, repeat=1):
    for _ in range(repeat):
        ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
        ctypes.windll.user32.keybd_event(vk, 0, 2, 0)
        if repeat > 1: time.sleep(0.01)


def load_map():
    if os.path.exists(MAP_FILE):
        try:
            with open(MAP_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_map(m):
    try:
        with open(MAP_FILE, "w", encoding="utf-8") as f:
            json.dump(m, f, indent=2, ensure_ascii=False)
    except:
        pass


class TriggerManager:
    def __init__(self, key_event_callback):
        self.callback = key_event_callback
        self.dll = None
        self._callback_c = None
        self._loaded = False
        self._start_listener()

    def _start_listener(self):
        if not os.path.exists(DLL_PATH): return
        try:
            self.dll = ctypes.WinDLL(DLL_PATH)
            CALLBACK_TYPE = ctypes.WINFUNCTYPE(None, ctypes.c_char_p)

            def py_key_callback(c_str):
                if c_str:
                    s = c_str.decode("utf-8", errors="ignore")
                    if s: self.callback(s)

            self._callback_c = CALLBACK_TYPE(py_key_callback)
            self.dll.Initialize(self._callback_c)
            if self.dll.StartListener(): self._loaded = True
        except:
            pass

    def stop_listener(self):
        if self._loaded and self.dll: self.dll.StopListener()


# -------------------- ANA ARAYÜZ --------------------
class ModernKeyMapper(QMainWindow):
    key_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("KeyMapper")
        self.setMinimumSize(1000, 750)

        self.key_map = load_map()
        self.last_trigger = {}
        self._listening = False
        self.store_apps_data = []

        self.init_ui()
        self.setup_backend()
        QTimer.singleShot(500, self.load_store_apps)

    def init_ui(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QGroupBox { 
                color: #0078D4; font-weight: bold; border: 1px solid #333; 
                margin-top: 15px; padding-top: 10px; border-radius: 5px;
            }
            QLabel { color: #bbb; font-size: 12px; }
            QLineEdit { 
                background-color: #2d2d2d; border: 1px solid #444; color: white; 
                padding: 8px; border-radius: 4px; 
            }
            QPushButton { 
                background-color: #3a3a3a; color: white; border-radius: 4px; padding: 8px;
            }
            QPushButton:hover { background-color: #454545; }
            QListWidget { background-color: #252525; border: 1px solid #333; color: #eee; }
            QListWidget::item:selected { background-color: #0078D4; }
            QScrollBar:vertical { background: #2d2d2d; width: 10px; }
            QScrollBar::handle:vertical { background: #555; border-radius: 5px; }
        """)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # --- SOL TARAF (AYARLAR) ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setSpacing(15)

        # Bölüm 1: Tetikleyici
        group_trigger = QGroupBox("1. TETİKLEYİCİ TUŞ")
        gt_layout = QVBoxLayout()
        self.btn_listen = QPushButton("TUŞ YAKALAMAYI BAŞLAT")
        self.btn_listen.setFixedHeight(45)
        self.btn_listen.setStyleSheet("background-color: #0078D4; font-weight: bold;")
        self.btn_listen.clicked.connect(self.start_listening)

        self.txt_key_id = QLineEdit()
        self.txt_key_id.setPlaceholderText("Seçilen tuş burada görünecek...")
        self.txt_key_id.setReadOnly(True)
        self.txt_key_id.setAlignment(Qt.AlignmentFlag.AlignCenter)

        gt_layout.addWidget(self.btn_listen)
        gt_layout.addWidget(self.txt_key_id)
        group_trigger.setLayout(gt_layout)
        left_layout.addWidget(group_trigger)

        # Bölüm 2: Windows Uygulamaları
        group_apps = QGroupBox("2. WINDOWS UYGULAMASI SEÇ")
        ga_layout = QVBoxLayout()
        self.txt_search_app = QLineEdit()
        self.txt_search_app.setPlaceholderText("Uygulama ara (Örn: Spotify)...")
        self.txt_search_app.textChanged.connect(self.filter_store_apps)

        self.list_store_apps = QListWidget()
        self.list_store_apps.setFixedHeight(180)
        self.list_store_apps.itemClicked.connect(self.on_store_item_clicked)

        ga_layout.addWidget(self.txt_search_app)
        ga_layout.addWidget(self.list_store_apps)
        group_apps.setLayout(ga_layout)
        left_layout.addWidget(group_apps)

        # Bölüm 3: Manuel Dosya veya Medya
        group_manual = QGroupBox("3. MANUEL DOSYA VEYA MEDYA")
        gm_layout = QVBoxLayout()

        path_layout = QHBoxLayout()
        self.txt_prog_path = QLineEdit()
        self.txt_prog_path.setPlaceholderText("C:\\Programlar\\uygulama.exe")
        self.txt_prog_path.textChanged.connect(self.on_manual_path_changed)

        btn_browse = QPushButton("Dosya Seç")
        btn_browse.clicked.connect(self.select_file)
        path_layout.addWidget(self.txt_prog_path)
        path_layout.addWidget(btn_browse)

        self.combo_media = QComboBox()
        self.combo_media.addItems(["Medya İşlemi Yok", "VOL_UP", "VOL_DOWN", "MUTE", "PLAY_PAUSE", "NEXT", "PREV"])
        self.combo_media.currentIndexChanged.connect(self.on_media_changed)

        gm_layout.addLayout(path_layout)
        gm_layout.addWidget(QLabel("VEYA MEDYA KONTROLÜ SEÇİN:"))
        gm_layout.addWidget(self.combo_media)
        group_manual.setLayout(gm_layout)
        left_layout.addWidget(group_manual)

        # Kaydet Butonu
        self.btn_save = QPushButton("EŞLEMEYİ SİSTEME EKLE")
        self.btn_save.setFixedHeight(50)
        self.btn_save.setStyleSheet("background-color: #28a745; font-weight: bold; font-size: 14px;")
        self.btn_save.clicked.connect(self.save_binding)
        left_layout.addWidget(self.btn_save)
        left_layout.addStretch()

        scroll_area.setWidget(left_container)
        main_layout.addWidget(scroll_area, 45)

        # --- SAĞ TARAF (LİSTE) ---
        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("AKTİF TUŞ ATAMALARI (Silmek için çift tıkla)"))
        self.list_active = QListWidget()
        self.list_active.itemDoubleClicked.connect(self.remove_item)
        right_panel.addWidget(self.list_active)

        self.btn_clear_all = QPushButton("TÜMÜNÜ SİL")
        self.btn_clear_all.setStyleSheet("color: #ff4444; border: 1px solid #ff4444;")
        self.btn_clear_all.clicked.connect(self.clear_all_maps)
        right_panel.addWidget(self.btn_clear_all)

        main_layout.addLayout(right_panel, 55)

    # -------------------- MANTIK VE ETKİLEŞİM --------------------

    def on_store_item_clicked(self):
        """Mağaza uygulaması seçilince manuel alanları temizle"""
        self.txt_prog_path.clear()
        self.combo_media.setCurrentIndex(0)

    def on_manual_path_changed(self):
        """Manuel yol girilince liste seçimini temizle"""
        if self.txt_prog_path.text():
            self.list_store_apps.clearSelection()
            self.combo_media.setCurrentIndex(0)

    def on_media_changed(self, index):
        """Medya seçilince diğerlerini temizle"""
        if index > 0:
            self.list_store_apps.clearSelection()
            self.txt_prog_path.clear()

    def load_store_apps(self):
        try:
            cmd = 'powershell -NoProfile "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Get-StartApps | ConvertTo-Json -Compress"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')
            if result.stdout:
                apps = json.loads(result.stdout)
                if isinstance(apps, dict): apps = [apps]
                self.store_apps_data = sorted([a for a in apps if a.get("Name")], key=lambda x: x["Name"].lower())
                self.update_store_list(self.store_apps_data)
        except:
            pass

    def update_store_list(self, apps):
        self.list_store_apps.clear()
        for app in apps:
            item = QListWidgetItem(app["Name"])
            item.setData(Qt.ItemDataRole.UserRole, f"shell:AppsFolder\\{app['AppID']}")
            self.list_store_apps.addItem(item)

    def filter_store_apps(self):
        search = self.txt_search_app.text().lower()
        filtered = [a for a in self.store_apps_data if search in a["Name"].lower()]
        self.update_store_list(filtered)

    def setup_backend(self):
        self.key_signal.connect(self.handle_incoming_key)
        self.trigger_manager = TriggerManager(self.key_signal.emit)
        self.mouse_listener = mouse.Listener(
            on_click=lambda x, y, b, p: self.key_signal.emit(f"Mouse_{b.name}") if p else None,
            on_scroll=lambda x, y, dx, dy: self.key_signal.emit("Mouse_Wheel_Up" if dy > 0 else "Mouse_Wheel_Down")
        )
        self.mouse_listener.start()
        self.setup_tray()
        self.refresh_list()

    def handle_incoming_key(self, key_id):
        if self._listening:
            self.txt_key_id.setText(key_id)
            self._listening = False
            self.btn_listen.setText("TUŞ YAKALAMAYI BAŞLAT")
            self.btn_listen.setEnabled(True)
        else:
            self.execute_hotkey(key_id)

    def execute_hotkey(self, key_id):
        if key_id in self.key_map:
            now = time.time()
            debounce = 0.12 if "Wheel" in key_id else DEBOUNCE_SEC
            if now - self.last_trigger.get(key_id, 0) < debounce: return
            self.last_trigger[key_id] = now

            data = self.key_map[key_id]
            if "program" in data:
                self.run_process(data["program"])
            elif "media" in data:
                self.run_media(data["media"])

    def run_process(self, path):
        try:
            if path.startswith("shell:AppsFolder"):
                subprocess.Popen(["explorer.exe", path], shell=True)
            else:
                os.startfile(path)
        except:
            pass

    def run_media(self, action):
        actions = {"VOL_UP": (VK_VOLUME_UP, 5), "VOL_DOWN": (VK_VOLUME_DOWN, 5),
                   "MUTE": (VK_VOLUME_MUTE, 1), "PLAY_PAUSE": (VK_MEDIA_PLAY_PAUSE, 1),
                   "NEXT": (VK_MEDIA_NEXT_TRACK, 1), "PREV": (VK_MEDIA_PREV_TRACK, 1)}
        if action in actions: send_media_key(*actions[action])

    def start_listening(self):
        self._listening = True
        self.txt_key_id.setText("KLAVYEDEN VEYA FAREDEN BİR TUŞA BASIN...")
        self.btn_listen.setEnabled(False)

    def select_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Çalıştırılacak Dosyayı Seç", "",
                                              "Executable (*.exe);;All Files (*.*)")
        if file:
            self.txt_prog_path.setText(file)
            self.on_manual_path_changed()

    def save_binding(self):
        kid = self.txt_key_id.text()
        if not kid or "BASIN" in kid:
            QMessageBox.Warning(self, "Hata", "Lütfen önce bir tetikleyici tuş belirleyin!")
            return

        selected_store = self.list_store_apps.currentItem()
        media_act = self.combo_media.currentText()
        prog_path = self.txt_prog_path.text().strip()

        if selected_store:
            self.key_map[kid] = {"program": selected_store.data(Qt.ItemDataRole.UserRole)}
        elif prog_path:
            self.key_map[kid] = {"program": prog_path}
        elif media_act != "Medya İşlemi Yok":
            self.key_map[kid] = {"media": media_act}
        else:
            QMessageBox.Warning(self, "Hata", "Lütfen bir uygulama veya medya işlemi seçin!")
            return

        save_map(self.key_map)
        self.refresh_list()
        self.txt_key_id.clear()
        QMessageBox.information(self, "Başarılı", f"'{kid}' tuşu başarıyla atandı.")

    def refresh_list(self):
        self.list_active.clear()
        for k, v in self.key_map.items():
            val = v.get("program", f"[Medya: {v.get('media')}]")
            # Uzun yolları kısalt (Sadece dosya adı göster)
            display_val = os.path.basename(str(val)) if "\\" in str(val) else str(val)
            self.list_active.addItem(f"{k}  =>  {display_val}")

    def remove_item(self, item):
        key_id = item.text().split("  =>")[0].strip()
        if key_id in self.key_map:
            del self.key_map[key_id]
            save_map(self.key_map)
            self.refresh_list()

    def clear_all_maps(self):
        if QMessageBox.question(self, "Onay", "Tüm eşlemeler silinsin mi?") == QMessageBox.StandardButton.Yes:
            self.key_map = {}
            save_map(self.key_map)
            self.refresh_list()

    def setup_tray(self):
        def on_exit(icon):
            icon.stop()
            self.trigger_manager.stop_listener()
            QApplication.quit()

        img = Image.new("RGB", (64, 64), (0, 120, 212))
        d = ImageDraw.Draw(img)
        d.ellipse((10, 10, 54, 54), fill="white")

        self.tray_icon = pystray.Icon("keymapper", img, "KeyMapper", menu=pystray.Menu(
            pystray.MenuItem("Göster", lambda: QTimer.singleShot(0, self.showNormal)),
            pystray.MenuItem("Çıkış", on_exit)
        ))
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        # İlk kapanışta bilgilendirme yapabiliriz
        # self.tray_icon.notify("Uygulama arka planda çalışmaya devam ediyor.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = ModernKeyMapper()
    window.hide()
    sys.exit(app.exec())