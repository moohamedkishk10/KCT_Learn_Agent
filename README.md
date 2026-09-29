# KCT Learn Agent

A Telegram bot that acts as a structured instructor and code reviewer for learners in **Artificial Intelligence** and **Data Science**. Built with Google Gemini 2.5 Flash and LangChain.

## Features

- **Structured roadmaps:** Generates multi-module curricula for the AI or Data Science track.
- **Dual assessment:** Each phase ends with a theory question and a hands-on coding assignment.
- **Code review:** Reviews submitted code for correctness, performance, and best practices (LLM-based; code is not executed).
- **Per-user memory:** Separate conversation memory per Telegram user ID.
- **Language adaptation:** Replies in the language and tone the learner uses.

## Stack

| Component | Technology |
|---|---|
| Language | Python 3.10+ |
| LLM | Google Gemini 2.5 Flash |
| Orchestration | LangChain (`langchain-classic`, `langchain-core`) |
| Bot framework | `python-telegram-bot` v20+ |
| Event loop patching | `nest_asyncio` |

## Getting Started

### Prerequisites

- Python 3.10 or newer
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/)

### Installation

Clone the repository:

```bash
git clone https://github.com/moohamedkishk10/KCT_Learn_Agent.git
cd KCT_Learn_Agent
```

Create and activate a virtual environment:

```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Then set your credentials in `.env`:

```env
TELEGRAM_TOKEN=your_telegram_bot_token
GEMINI_API_KEY=your_gemini_api_key
```

### Run

```bash
python main.py
```

## Usage

Open your bot in Telegram and send `/start`. Choose a track, follow the roadmap, and submit answers and code directly in the chat.

## Limitations

- Code review is performed by the LLM and may miss runtime errors, since submitted code is never executed.
- Session memory is kept per user ID; see the source for its persistence behavior.

## Security

Never commit your `.env` file. It is excluded by `.gitignore`. If a token or key is ever exposed, revoke and regenerate it immediately.