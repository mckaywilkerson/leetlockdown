import sys, subprocess, os, datetime, json, time, requests, webbrowser, traceback
from pathlib import Path
from zoneinfo import ZoneInfo

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QDialog,
    QHBoxLayout, QLineEdit, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer

import keyring

# --- Config ---
USERNAME = "YOUR_LEETCODE_USERNAME"   # update to your username
SERVICE_NAME = "DailyGate.LeetCode"   # keyring service
COOKIE_KEY = "LEETCODE_SESSION"       # key name stored in keyring
STATE_PATH = Path(r"C:\ProgramData\DailyGate\state.json")
LOG_PATH = Path(r"C:\ProgramData\DailyGate\gate.log")
TZ = ZoneInfo("America/Boise")

GRAPHQL_URL = "https://leetcode.com/graphql"
GRAPHQL_QUERY = """
query recentAccepted($username: String!, $limit: Int!) {
  recentAcSubmissionList(username: $username, limit: $limit) {
    id
    title
    timestamp
  }
}
"""

POLL_SECONDS = 30


# --- Utilities ---
def log(msg: str):
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as f:
            ts = datetime.datetime.now(tz=TZ).isoformat()
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass

def load_state():
    try:
        if STATE_PATH.exists():
            return json.loads(STATE_PATH.read_text())
    except Exception:
        pass
    return {}

def save_state(d):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(d))

def mark_unlocked_today(reason="solved"):
    s = load_state()
    s["last_unlock_date"] = str(datetime.date.today())
    s["last_unlock_reason"] = reason
    save_state(s)
    log(f"Unlocked by: {reason}")

def already_unlocked_today():
    s = load_state()
    return s.get("last_unlock_date") == str(datetime.date.today())

def is_today_epoch(ts):
    d = datetime.datetime.fromtimestamp(int(ts), tz=TZ).date()
    return d == datetime.datetime.now(tz=TZ).date()

def get_cookie():
    return keyring.get_password(SERVICE_NAME, COOKIE_KEY)

def set_cookie(value: str):
    keyring.set_password(SERVICE_NAME, COOKIE_KEY, value)

def clear_cookie():
    try:
        keyring.delete_password(SERVICE_NAME, COOKIE_KEY)
    except Exception:
        pass


# --- LeetCode checks ---
class CookieInvalid(Exception):
    pass

def fetch_recent_accepts():
    cookie = get_cookie()
    if not cookie:
        raise CookieInvalid("No cookie stored")

    s = requests.Session()
    # Secure cookie scope
    s.cookies.set("LEETCODE_SESSION", cookie, domain=".leetcode.com", secure=True)
    data = {
        "operationName": "recentAccepted",
        "variables": {"username": USERNAME, "limit": 20},
        "query": GRAPHQL_QUERY
    }
    r = s.post(GRAPHQL_URL, json=data, timeout=15)
    if r.status_code == 401:
        raise CookieInvalid("401 Unauthorized from LeetCode")
    r.raise_for_status()

    payload = r.json()
    # When cookie is invalid, LeetCode often returns errors or null data
    if "data" not in payload or payload.get("data") is None:
        raise CookieInvalid("GraphQL returned no data (likely invalid/expired session)")
    items = (payload["data"].get("recentAcSubmissionList") or [])
    return items

def solved_today():
    items = fetch_recent_accepts()
    today_items = [i for i in items if is_today_epoch(i["timestamp"])]
    return today_items[0] if today_items else None


# --- UI Dialogs ---
class PasteCookieDialog(QDialog):
    """
    Simple dialog to paste a new LEETCODE_SESSION cookie.
    Validates by making a small GraphQL call.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Update LeetCode Session")
        self.setModal(True)
        self.setMinimumWidth(500)

        v = QVBoxLayout()

        help_label = QLabel(
            "Your session appears to be expired.\n"
            "1) Click 'Open LeetCode Login' and sign in.\n"
            "2) Open your browser DevTools → Application/Storage → Cookies → leetcode.com\n"
            "3) Copy the value of LEETCODE_SESSION and paste it below.\n"
        )
        help_label.setWordWrap(True)
        v.addWidget(help_label)

        self.cookie_edit = QLineEdit()
        self.cookie_edit.setPlaceholderText("Paste LEETCODE_SESSION value here")
        self.cookie_edit.setEchoMode(QLineEdit.Normal)
        v.addWidget(self.cookie_edit)

        btn_row = QHBoxLayout()
        btn_open = QPushButton("Open LeetCode Login")
        btn_open.clicked.connect(lambda: webbrowser.open("https://leetcode.com/accounts/login/"))
        btn_row.addWidget(btn_open)

        btn_save = QPushButton("Save & Validate")
        btn_save.clicked.connect(self.validate_and_save)
        btn_row.addWidget(btn_save)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        v.addLayout(btn_row)
        self.setLayout(v)

    def validate_and_save(self):
        new_cookie = self.cookie_edit.text().strip()
        if not new_cookie:
            QMessageBox.warning(self, "Missing", "Please paste a cookie value.")
            return
        try:
            # Temporarily set and validate
            set_cookie(new_cookie)
            # Quick validate: attempt to fetch some data
            _ = fetch_recent_accepts()
            QMessageBox.information(self, "Saved", "Session updated successfully.")
            self.accept()
        except CookieInvalid:
            clear_cookie()
            QMessageBox.critical(self, "Invalid", "That cookie didn't work. Please try again.")
        except Exception as e:
            log("Validation error: " + repr(e))
            # keep cookie in place; may be transient net error
            QMessageBox.warning(self, "Network/Error",
                                "Could not validate right now. If this persists, paste again.\n\n"
                                f"{type(e).__name__}: {e}")
            self.accept()


# --- Main Gate UI ---
from PyQt5.QtGui import QCloseEvent

class Gate(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Daily LeetCode Gate")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.showFullScreen()

        btn_open = QPushButton("Open LeetCode Problemset")
        btn_open.clicked.connect(lambda: self.open_for_work("https://leetcode.com/problemset/"))

        layout = QVBoxLayout()
        layout.setSpacing(14)

        self.label = QLabel("🔒 Solve one LeetCode problem today to unlock")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 22px;")
        layout.addWidget(self.label)

        # Open LeetCode / Daily Problem buttons
        row = QHBoxLayout()
        btn_daily = QPushButton("Open Daily Challenge")
        btn_daily.clicked.connect(lambda: self.open_for_work("https://leetcode.com/problemset/all/?listId=wpwgkgt"))
        row.addWidget(btn_daily)

        btn_open = QPushButton("Open LeetCode Problemset")
        btn_open.clicked.connect(lambda: self.open_for_work("https://leetcode.com/problemset/"))
        row.addWidget(btn_open)
        layout.addLayout(row)

        # Cookie refresh
        btn_cookie = QPushButton("Update Session (Paste Cookie)")
        btn_cookie.clicked.connect(self.open_cookie_dialog)
        layout.addWidget(btn_cookie)

        # Emergency exit
        btn_exit = QPushButton("Emergency Exit (logs usage)")
        btn_exit.clicked.connect(self.emergency_exit)
        layout.addWidget(btn_exit)

        help_note = QLabel("Tip: If you just solved a problem, the gate checks every 30s.\n"
                           "If your session expired, click 'Update Session (Paste Cookie)'.")
        help_note.setAlignment(Qt.AlignCenter)
        help_note.setStyleSheet("color: #666;")
        layout.addWidget(help_note)

        self.setLayout(layout)

        # periodic check
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_status)
        self.timer.start(POLL_SECONDS * 1000)

        # Immediate check on show (so you aren’t stuck if you already solved today)
        QTimer.singleShot(1000, self.check_status)

    def check_status(self):
        try:
            item = solved_today()
            if item:
                mark_unlocked_today(reason=f"solved:{item.get('id', 'unknown')}")
                self.close()  # unlock
        except CookieInvalid:
            # Prompt gently to refresh
            self.label.setText("🔑 Your LeetCode session expired. Click 'Update Session (Paste Cookie)'.")
        except Exception as e:
            log("check_status error: " + repr(e))
            # no crash; maybe offline—just try later

    def open_cookie_dialog(self):
        dlg = PasteCookieDialog(self)
        dlg.exec_()  # on accept, cookie is saved/validated (or attempted)

    def emergency_exit(self):
        mark_unlocked_today(reason="emergency")
        self.close()

    # Prevent accidental close with Alt+F4
    def closeEvent(self, event: QCloseEvent):
        # Only allow close if we are marked unlocked today
        if already_unlocked_today():
            event.accept()
        else:
            event.ignore()

    def open_for_work(self, url: str):
        # Remove always-on-top temporarily
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.showFullScreen()

        # Use Windows 'start' to foreground default browser more reliably
        try:
            subprocess.Popen(['cmd', '/c', 'start', '', url], shell=True)
        except Exception:
            webbrowser.open_new(url)

        # Minimize the gate so it’s out of the way while you work
        QTimer.singleShot(200, self.showMinimized)

        # (Optional) after X minutes, auto-restore the gate if you want to be stricter
        # QTimer.singleShot(15 * 60 * 1000, self.bring_gate_back)

    # --- NEW: bring the gate back to the front (optional control) ---
    def bring_gate_back(self):
        # Re-assert always-on-top and full-screen
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.showFullScreen()
        self.raise_()
        self.activateWindow()


# --- Entrypoint ---
def main():
    # If already unlocked today, exit silently
    if already_unlocked_today():
        sys.exit(0)

    # Start GUI
    app = QApplication(sys.argv)
    g = Gate()
    g.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log("Fatal: " + repr(e))
        log(traceback.format_exc())
        # fail-safe: don’t brick the machine if script dies unexpectedly
        mark_unlocked_today(reason="crash-failsafe")
        sys.exit(0)
