# Kiro: Agentic macOS Assistant

An autonomous, local AI agent built with LangGraph and DeepSeek that natively interacts with macOS. The project leverages dual-LLM architecture, semantic long-term memory extraction, and native AppleScript bridging to execute complex, multi-step workflows directly on the operating system.

## Overview

Traditional LLM wrappers act as passive conversational agents. This project explores Agentic AI, where the system is given the autonomy to think, plan, and execute actions across local and web environments.

By integrating LangGraph for state management and DeepSeek for reasoning, Kiro functions as a native macOS assistant. It bridges the gap between text generation and actual execution by managing calendars, writing Apple Notes, reading local files, and securely interfacing with the Gmail API. 

The project demonstrates a complete agentic workflow including tool orchestration, background memory extraction, Human-in-the-Loop (HITL) safety protocols, and native system automation.

## Objectives

The primary objectives of this project are:

- Build an autonomous agent capable of executing multi-step logic.
- Implement a dual-LLM architecture separating conversational flow from background memory extraction.
- Create native bridges to macOS applications (Notes, Calendar, Reminders).
- Integrate secure, authenticated external APIs (Gmail, YouTube).
- Implement Human-in-the-Loop (HITL) protocols for sensitive actions.
- Build a persistent semantic memory layer that adapts to the user over time.

## Architecture

The project follows a state-machine based agentic pipeline using LangGraph.

```text
User Input
       ↓
Memory Node (Background LLM extracts permanent facts)
       ↓
Chat Node (Core Orchestrator LLM)
       ↓
Tool Execution Node (22 Custom Tools)
       ↓
State Update & Loop (Until task is completed)
       ↓
Final Response
```

## Core AI Technologies

Before executing tools, the network utilizes several advanced AI engineering paradigms.

### Dual-LLM Strategy

The system utilizes two distinct LLM instances:
- **The Orchestrator:** A high-temperature instance responsible for conversation, reasoning, and tool selection.
- **The Memory Extractor:** A low-temperature, strict-output instance that analyzes conversation history invisibly to extract factual data and user preferences.

### Long-Term Persistent Memory

Instead of treating each session independently, the model builds a persistent semantic memory. It passively learns user preferences, project details, and relationships, storing them securely on the local machine and injecting them as context into future sessions.

### Human-in-the-Loop (HITL)

While the agent is autonomous, strict safety protocols are implemented. For irreversible actions (e.g., sending emails via the Gmail API), the agent drafts the action and suspends execution until the user provides explicit CLI approval.

## Tool Repertoire

The agent is equipped with 22 distinct execution tools.

### Native macOS Integration
- `read_apple_notes` / `create_apple_note` / `append_apple_note`
- `read_calendar_events` / `create_calendar_event` / `delete_calendar_event`
- `create_reminder`
- `open_app_or_website`
- `get_system_status`
- `find_local_files`

### External API Integration
- `search_emails` / `read_email` / `send_email` (Gmail API)
- `play_youtube_music` / `get_youtube_subscriptions` / `create_youtube_playlist`
- `tavily_search` / `wikipedia_search`
- `get_weather`

## Repository Structure

```text
Personal-Assistant-AI-Agent/
│
├── agent.py               # LangGraph state machine definition
├── brain.py               # Dynamic prompt and identity management
├── llm.py                 # DeepSeek model initialization
├── memory.py              # Long-term semantic memory extractor
├── tools.py               # 22 custom tool definitions
├── google_service.py      # OAuth2 authentication for Google APIs
├── main.py                # CLI entry point and Rich UI
├── persona.md             # Local user background context
├── .env.example           # Environment variables template
└── requirements.txt
```

## Running the Project

### Clone the Repository

```bash
git clone https://github.com/manasch3/Personal-Assistant-AI-Agent.git
cd Personal-Assistant-AI-Agent
```

### Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configuration

Copy the example environment file and add your API keys:
```bash
cp .env.example .env
```
Ensure you have a `credentials.json` file in the root directory for Google API access.

### Launch the Agent

```bash
python main.py
```

## Key Findings

Several important observations emerged during the development of this agentic architecture:

- LangGraph provides vastly superior state management compared to traditional zero-shot agent loops, preventing infinite tool-calling loops.
- Separating memory extraction into a parallel, low-temperature LLM significantly reduces hallucinations in long-term factual recall.
- AppleScript serves as an incredibly stable bridge between Python and native macOS applications.
- Human-in-the-Loop protocols are essential for agentic systems interacting with external communication APIs.

## Skills Demonstrated

This project showcases practical experience in:

- Agentic AI & LLM Orchestration
- LangGraph / LangChain
- DeepSeek / Advanced LLMs
- Native macOS Automation (AppleScript)
- Google Workspace APIs (OAuth2, Gmail, YouTube)
- Semantic Memory Management
- Python CLI Development (Rich)

## Future Improvements

Potential future enhancements include:

- Migrating from `InMemoryStore` to SQLite for persistent multi-device memory.
- Adding Vision capabilities (e.g., screenshot analysis) for UI-aware automation.
- Implementing a Raycast extension or menubar application for global OS access.
- Integrating RAG (Retrieval-Augmented Generation) for local PDF and codebase indexing.
