# leetlockdown (Daily LeetCode Gate for Windows)

Solve one LeetCode problem each day to unlock your desktop.
A full-screen gate launches at login, lets you open LeetCode to work, and auto-unlocks as soon as an **Accepted** submission is detected for **today**. Includes an **Emergency Exit** button (logged) and a simple **manual cookie refresh** flow.

---

## ✨ Features

* Full-screen, always-on-top lock at login
* “Open LeetCode” / “Open Daily” buttons that **minimize the gate** so your browser gains focus
* Auto-checks every \~30s for an Accepted submission **today** (America/Boise by default)
* **Manual cookie refresh** dialog (stores securely in Windows Credential Manager via `keyring`)
* **Emergency Exit** button (logs usage) so you’re never bricked
* Fail-safe: if the app crashes, it unlocks rather than trapping you

---

## 🧰 Prerequisites

* **Windows 10/11**
* **Python 3.11+** (3.9+ likely fine, but 3.11 recommended)
* Ability to install Python packages (pip)
* A LeetCode account

> Optional (nice to have): create and use a Python **virtual environment** for this project.

---

## 🚀 Quick Start

1. **Clone** the repo & open a terminal in the project folder.

2. **(Optional) Create a venv**

```powershell
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
```

3. **Install dependencies**

```powershell
pip install requests pyqt5 keyring
```

4. **Configure your username**
   Open `daily_gate.py` and set:

```python
USERNAME = "YOUR_LEETCODE_USERNAME"
```

5. **First run (foreground)**

```powershell
python daily_gate.py
```

* You’ll see the full-screen gate.
* Click **Open LeetCode** → log in.
* If prompted that your session expired, click **Update Session (Paste Cookie)** (see “Get your cookie” below).

6. **(Recommended) Use `pythonw.exe` for silent background**

```powershell
# Test it without a console window:
C:\Path\To\Python\pythonw.exe C:\Path\To\leetlock\daily_gate.py
```

---

## 🔑 How to get your `LEETCODE_SESSION` cookie

You only need to do this when the session expires (usually every few weeks).

**Chrome/Edge/Brave**

1. Log in at [https://leetcode.com](https://leetcode.com)
2. Press **F12** → **Application** (or “Storage”) tab
3. **Storage → Cookies → [https://leetcode.com](https://leetcode.com)**
4. Copy the **Value** of `LEETCODE_SESSION`
5. In the gate, click **Update Session (Paste Cookie)** and paste the value → **Save & Validate**

**Firefox**

1. Log in at [https://leetcode.com](https://leetcode.com)
2. Press **F12** → **Storage** tab
3. **Cookies → [https://leetcode.com](https://leetcode.com)**
4. Copy `LEETCODE_SESSION` **Value**
5. Paste it via **Update Session (Paste Cookie)** in the gate

> The cookie is stored securely in **Windows Credential Manager** via `keyring`.

---

## ⚙️ Auto-Run at Login (Task Scheduler)

1. Open **Task Scheduler** → **Create Task…**
2. **General**

   * Name: `Daily LeetCode Gate`
   * Check **Run with highest privileges**
3. **Triggers**

   * **New…** → **Begin the task:** *At log on* → **OK**
4. **Actions**

   * **New…**
   * **Program/script:** `C:\Path\To\Python\pythonw.exe`
   * **Add arguments:** `"C:\Path\To\leetlock\daily_gate.py"`
   * **Start in:** `C:\Path\To\leetlock`
5. **Settings**

   * If the task is already running, **Do not start a new instance**
6. Save → **Log off / Log on** to test.

> **Escape hatch:** Keep a separate admin account **without** this task in case you need to troubleshoot.

---

## 🖥️ Daily Flow

1. Log in → full-screen gate appears.
2. Click **Open Daily** or **Open LeetCode**. The gate **minimizes** so your browser is in front.
3. Solve and submit. Once you get **Accepted**, the gate detects it (polls every \~30s) and **auto-closes**.
4. If you’re in a rush, use **Emergency Exit** (logged).

---

## 🔒 Where data is stored

* `C:\ProgramData\DailyGate\state.json` – last unlock date/reason
* `C:\ProgramData\DailyGate\gate.log` – simple log (unlocks, errors, exits)
* **Cookie** – stored in **Windows Credential Manager** via `keyring` (not in plain text)

---

## 🛠️ Configuration Tips

* **Timezone:** defaults to `America/Boise`. Change in `TZ = ZoneInfo("America/Boise")`.
* **Polling interval:** `POLL_SECONDS = 30`.
* **Browser focus:** Buttons call `cmd /c start` and **minimize** the gate so the browser takes focus.
* **Daily Challenge only (optional):**
  You can modify the check to require the “Daily” problem’s slug for that date instead of any accepted submission.

---

## ❓ FAQ

**Q: Do I need a new cookie every day?**
A: No. Sessions typically last **weeks**. The gate will prompt you when it expires; just paste a fresh value.

**Q: My browser opens behind the gate.**
A: This project minimizes the gate while launching URLs so apps open in front. If you forked or changed that part, ensure you temporarily remove `WindowStaysOnTopHint` and call `showMinimized()` after launch.

**Q: I got `TypeError: create_cookie() got unexpected keyword arguments: ['httponly']`.**
A: Remove `httponly=True` from `s.cookies.set(...)`. `requests` doesn’t accept it—use `secure=True` and `domain=".leetcode.com"` only.

**Q: Can I make it impossible to bypass?**
A: The safest approach is using a **custom shell** (replace Explorer) or stricter policies, but that’s advanced and easier to lock yourself out. This project balances motivation with safety.

**Q: Can I use this on macOS?**
A: Yes, with tweaks: use a LaunchAgent and a full-screen PyQt app; manage cookies similarly. This repo focuses on Windows.

---

## 🔍 Troubleshooting

* **“Session expired” keeps showing even after paste**

  * Make sure you copied the **Value** only (no quotes/whitespace).
  * You must be logged into the same account as `USERNAME`.
  * Try again after refreshing the page and re-copying.
* **Gate never unlocks even with Accepted**

  * Check `gate.log`.
  * Verify timezone and that the acceptance timestamp is **today** locally.
  * Increase polling interval or click **Update Session** and re-paste the cookie.
* **Nothing happens at login**

  * Recheck Task Scheduler *Action* path and “Start in”.
  * Test manually with `pythonw.exe "C:\Path\To\daily_gate.py"`.

---

## 🧹 Uninstall

1. Delete the Task Scheduler task.
2. Remove the project folder.
3. (Optional) Remove stored cookie from **Credential Manager** (`DailyGate.LeetCode` / `LEETCODE_SESSION`).
4. Delete `C:\ProgramData\DailyGate\` if you don’t need logs/state.

---

## 🙌 Contributions

PRs welcome! Ideas: Daily-Challenge check, local judge mode, VS Code launcher, stats panel, stricter anti-bypass, auto-restore gate after N minutes, system-tray helper.

---

You can also drop in a **`requirements.txt`** and **Task Scheduler XML** export so setup is literally import-and-go.
