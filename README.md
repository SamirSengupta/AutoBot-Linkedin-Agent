# AutoBot — Agentic AI Job Applicator

> An agentic AI system that autonomously applies to LinkedIn Easy Apply jobs on your behalf, powered by the Groq LLM API and Playwright browser automation.

---

> [!CAUTION]
> **Disclaimer:** This project is a **technical demo** of agentic AI in browser automation. Using automated bots to apply to LinkedIn jobs **violates LinkedIn's Terms of Service**. The author takes no responsibility for any account bans, suspensions, or other consequences resulting from misuse. Use this tool for **educational and research purposes only**.

---

## Features

- 🤖 **Agentic AI** — Uses Groq's LLaMA model to intelligently fill out job application forms.
- 🌐 **Browser Automation** — Playwright drives a real Chromium browser to mimic human behavior.
- 🖥️ **Web UI** — Minimal React frontend to configure the bot without touching code.
- 🔒 **Secure Config** — Credentials are stored locally only and never committed to version control.
- 📄 **CV-Aware** — Reads your PDF CV to answer experience-based questions contextually.

---

## Prerequisites

Make sure the following are installed on your system:

- [Python 3.10+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/)
- [Git](https://git-scm.com/)
- A [Groq API Key](https://console.groq.com/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) (required for OCR fallback)

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/AutoBotMk1.git
cd AutoBotMk1
```

### 2. Set up the Python backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install fastapi uvicorn pydantic python-dotenv
```

### 3. Install Playwright and its browser

```bash
# From the root project directory (with your main venv or global Python)
pip install playwright pdfplumber pytesseract Pillow groq python-dotenv
playwright install chromium
```

### 4. Set up the React frontend

```bash
cd frontend
npm install
```

---

## Running the App

### Windows (Recommended)
Simply double-click **`run.bat`** in the project root. It will open two terminal windows:
- 🟢 **Backend** — FastAPI server at `http://localhost:8000`
- 🔵 **Frontend** — React dev server at `http://localhost:5173`

### Manual Start

**Terminal 1 — Backend:**
```bash
cd backend
venv\Scripts\activate
python server.py
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

Then open your browser and navigate to `http://localhost:5173`.

---

## How to Use

1. **Open** `http://localhost:5173` in your browser.
2. **Fill in** the form:
   - **Groq API Key** — Your key from [console.groq.com](https://console.groq.com)
   - **LinkedIn Email & Password** — Your login credentials
   - **CV Path** — Absolute path to your CV PDF (e.g. `C:\Users\Name\Documents\CV.pdf`)
   - **Profile & Preferences** — Fill in your address, phone, salary expectations, etc.
3. **Click "Start Automation"** — The bot will launch a Chromium window, log into LinkedIn, and begin applying to matching Easy Apply jobs.
4. **Monitor** the backend terminal for real-time logs of each application step.

---

## Configuration (Advanced)

You can also configure the bot via a `.env` file in the project root:

```env
LINKEDIN_EMAIL=your@email.com
LINKEDIN_PASSWORD=yourpassword
GROQ_API_KEY=gsk_...
CV_PATH=C:\path\to\your\cv.pdf
LOCATION=City, State
PHONE=5551234567
ADDRESS=123 Main St, City, State, US
ZIP_CODE=10001
SALARY_EXPECTATION=80000
COMMUTING=New York City
GENDER=Male
ETHNICITY=Your ethnicity
VETERAN_STATUS=No
DISABILITY=No
MIDDLE_NAME=A
```

> The Web UI takes priority over `.env` values when you click "Start Automation".

---

## Project Structure

```
AutoBotMk1/
├── app-groq.py          # Core automation script (Playwright + Groq)
├── run.bat              # One-click launcher for Windows
├── .gitignore
├── backend/
│   ├── server.py        # FastAPI backend API
│   └── config.json      # ⚠️ Auto-generated at runtime, git-ignored
└── frontend/
    ├── index.html
    ├── vite.config.js
    └── src/
        ├── main.jsx
        ├── App.jsx      # Main React form UI
        └── index.css    # Styles
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built as an agentic AI research demo. Not affiliated with LinkedIn.*
