# 🤖 Kiro: Agentic macOS Assistant

Kiro is an advanced, fully autonomous **Personal AI Assistant** designed explicitly for macOS. Moving beyond a standard LLM wrapper, Kiro leverages **Agentic AI orchestration**, long-term memory extraction, and deep native operating system integrations to perform complex, multi-step workflows directly on your machine.

---

## 🧠 Core Agentic Architecture

Kiro is built on modern AI engineering paradigms:

* **LangGraph Orchestration**: State-machine-based execution that allows the agent to iteratively think, act, and observe results until a task is completed.
* **Dual-LLM Strategy (DeepSeek)**:
  * **The Orchestrator**: A high-temperature conversational LLM that parses intent, selects tools, and executes multi-step logic.
  * **The Memory Extractor**: A low-temperature, strict-output LLM that runs invisibly in the background to analyze conversations and extract passive facts about the user.
* **Long-Term Persistent Memory**: Kiro learns about you over time. It saves user preferences, relationships, and project details natively, retrieving them contextually without requiring manual instruction.
* **Human-in-the-Loop (HITL)**: Safety first. While Kiro is autonomous, it is programmed to request explicit user approval via a CLI prompt before executing irreversible or sensitive actions (such as sending an email).

---

## 🛠️ Tool Repertoire (22 Native Tools)

Kiro is equipped with 22 distinct tools that bridge the gap between text generation and actual execution. 

### 🖥️ Native macOS Integrations (via AppleScript)
* **Apple Notes**: `read_apple_notes`, `create_apple_note`, `append_apple_note` — seamlessly manage local notes.
* **macOS Calendar**: `read_calendar_events`, `create_calendar_event`, `delete_calendar_event` — fully manage your native schedule.
* **macOS Reminders**: `create_reminder` — add tasks to your Apple ecosystem.
* **System Automation**: `open_app_or_website` (launches native apps or URLs), `get_system_status` (reads battery, storage, and local time), `find_local_files` (searches your local `~/Documents` directory).

### 📧 Gmail API Integration (with HITL)
* `search_emails`: Query your inbox using advanced syntax (e.g., "from:boss yesterday").
* `read_email`: Extract the full body of specific emails.
* `send_email`: Draft an email, display it to the user, and wait for explicit **Human-in-the-Loop** approval before sending via the Gmail API.

### 🎵 YouTube & Media
* `play_youtube_music`: Directly opens and autoplays specific artists or tracks on YouTube Music.
* `get_youtube_subscriptions`: Read your subscribed channels.
* `create_youtube_playlist` & `add_to_youtube_playlist`: Programmatically organize videos.

### 🌐 Information & Utilities
* `tavily_search`: Agentic web search for real-time internet data.
* `wikipedia_search`: Factual background context retrieval.
* `get_weather`: Real-time OpenWeather API integration.
* `calculator`: Safe math execution for precise calculations.

---

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/manasch3/Personal-Assistant-AI-Agent.git
   cd Personal-Assistant-AI-Agent
   ```

2. **Setup the Virtual Environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   * Rename `.env.example` to `.env`.
   * Fill in your `DEEPSEEK_API_KEY`, `TAVILY_API_KEY`, `USER_NAME`, and `USER_EMAIL`.
   * Place your Google API `credentials.json` in the root directory for Gmail/YouTube access.

4. **Run Kiro:**
   ```bash
   python main.py
   ```
   *(We recommend setting up an alias like `alias kiro="cd /path/to/project && source .venv/bin/activate && python main.py"` for easy access!)*
