#!/usr/bin/env bash
# ============================================================
# Jarvis Demo Script — CLI Walkthrough
# ============================================================
# Prerequisites:
#   1. Jarvis is running locally (docker compose up -d OR uv run python -m jarvis)
#   2. API keys are configured in .env
#   3. Google OAuth token is set up (scripts/setup_google_oauth.py)
#
# Usage: Run this script, then copy-paste the suggested prompts
#        into the Jarvis CLI when prompted.
# ============================================================

set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
RESET='\033[0m'

prompt() {
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
    echo -e "${CYAN}$1${RESET}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
    echo ""
    echo "  Try typing this in the Jarvis CLI:"
    echo ""
    echo "    $2"
    echo ""
    read -rp "  Press Enter to continue..."
}

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║            Jarvis — Interactive Demo                    ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "Make sure Jarvis is running in another terminal:"
echo "  uv run python -m jarvis"
echo ""
read -rp "Press Enter when ready..."

# --- Basic Chat ---
prompt "1. Basic Conversation" \
    "Hello Jarvis, what can you help me with?"

prompt "2. Memory — Jarvis remembers context" \
    "Remember that my favorite programming language is Python."

prompt "3. Memory Recall" \
    "What is my favorite programming language?"

# --- Gmail ---
prompt "4. Gmail — Search inbox" \
    "Search my email for messages from GitHub in the last week."

prompt "5. Gmail — Send an email" \
    "Draft an email to myself with subject 'Test from Jarvis' and body 'Hello from the demo!'"

# --- Google Calendar ---
prompt "6. Calendar — List upcoming events" \
    "What's on my calendar today?"

prompt "7. Calendar — Create an event" \
    "Create a meeting called 'Jarvis Demo' tomorrow at 2pm for 30 minutes."

# --- Google Docs ---
prompt "8. Google Docs — Create a document" \
    "Create a new Google Doc called 'Jarvis Demo Notes'."

prompt "9. Google Docs — Append content" \
    "Add 'This document was created by Jarvis during the demo.' to the doc you just created."

# --- Google Sheets ---
prompt "10. Google Sheets — Create a spreadsheet" \
    "Create a new spreadsheet called 'Demo Data'."

# --- Google Slides ---
prompt "11. Google Slides — Create a presentation" \
    "Create a new presentation called 'Jarvis Overview'."

# --- Notion ---
prompt "12. Notion — Search pages" \
    "Search Notion for pages about 'projects'."

# --- Todoist ---
prompt "13. Todoist — List tasks" \
    "Show my Todoist tasks."

prompt "14. Todoist — Create a task" \
    "Create a Todoist task: 'Review Jarvis demo' due tomorrow."

# --- Shell ---
prompt "15. Shell — Run a command" \
    "Run the command: uname -a"

# --- Browser ---
prompt "16. Browser — Navigate to a page" \
    "Browse to https://news.ycombinator.com and tell me the top 3 stories."

# --- Web Search ---
prompt "17. Web Search" \
    "Search the web for 'latest Python release'."

# --- Reminders ---
prompt "18. Reminders — Set a timer" \
    "Remind me in 2 minutes to check the oven."

# --- Voice (if enabled) ---
prompt "19. Voice — Send a voice message (if enabled)" \
    "Press and hold the mic button to send a voice note."

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║              Demo Complete!                             ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "Jarvis supports all of the above across CLI, Slack, and WhatsApp."
echo "For more info, see README.md."
echo ""
