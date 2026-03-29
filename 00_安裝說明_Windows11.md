# 🚀 安麗 AI Agent 系統 — Windows 11 安裝說明

## 📁 資料夾結構

```
C:\Users\user\claude AI_Agent\
├── agents\
│   ├── 01_scraper.py          ← 爬蟲Agent
│   ├── 02_scoring.py          ← 評分Agent
│   ├── 03_templates.py        ← 邀約話術
│   └── 04_crew_main.py        ← 多Agent主控
├── output\
│   ├── prospects_raw\         ← 爬蟲原始資料
│   ├── prospects_scored\      ← 評分後名單
│   └── messages\              ← 生成的邀約訊息
├── monitor\
│   └── AmwayWatcher.cs        ← C# 監看程式
├── config\
│   └── settings.json          ← 全域設定
└── logs\
    └── agent_log.txt          ← 執行紀錄
```

---

## ⚙️ 環境安裝（Windows 11 PowerShell）

```powershell
# 1. 建立資料夾
New-Item -ItemType Directory -Force -Path "C:\Users\user\claude AI_Agent\agents"
New-Item -ItemType Directory -Force -Path "C:\Users\user\claude AI_Agent\output\prospects_raw"
New-Item -ItemType Directory -Force -Path "C:\Users\user\claude AI_Agent\output\prospects_scored"
New-Item -ItemType Directory -Force -Path "C:\Users\user\claude AI_Agent\output\messages"
New-Item -ItemType Directory -Force -Path "C:\Users\user\claude AI_Agent\monitor"
New-Item -ItemType Directory -Force -Path "C:\Users\user\claude AI_Agent\config"
New-Item -ItemType Directory -Force -Path "C:\Users\user\claude AI_Agent\logs"

# 2. 安裝 Python 套件
pip install crewai crewai-tools anthropic requests python-dotenv

# 3. 設定環境變數（PowerShell）
[System.Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "your_key_here", "User")
[System.Environment]::SetEnvironmentVariable("TAVILY_API_KEY", "your_key_here", "User")

# 4. 安裝 Claude Code CLI
npm install -g @anthropic-ai/claude-code

# 5. 安裝 Gemini CLI（選用）
npm install -g @google/generative-ai-cli
```

---

## 🔄 每日執行流程

```
[VS Code 觸發]
      ↓
python 01_scraper.py      → 產出 prospects_raw/YYYYMMDD.json
      ↓
python 02_scoring.py      → 產出 prospects_scored/YYYYMMDD.json
      ↓
python 04_crew_main.py    → 產出 messages/YYYYMMDD.json
      ↓
[C# Watcher 偵測新檔案]
      ↓
[未來] LINE Bot 自動發送
```

---

## 📋 settings.json 範例

```json
{
  "output_dir": "C:\\claude AI_Agent\\output",
  "log_file": "C:\\claude AI_Agent\\logs\\agent_log.txt",
  "daily_limit": 100,
  "ai_model": "claude-sonnet-4-20250514",
  "keywords": ["副業推薦","兼職機會","在家工作","斜槓收入","媽媽副業"],
  "regions": ["台灣","台北","台中","高雄","新北"],
  "scoring_threshold": {
    "high": 70,
    "mid": 40
  },
  "line_bot": {
    "enabled": false,
    "channel_token": "YOUR_LINE_TOKEN"
  }
}
```
