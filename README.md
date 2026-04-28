# AI-Bot 🤖

A smart Telegram AI Assistant powered by the NVIDIA API. It can answer complex questions, write and format programming code, and analyze provided images.

## Prerequisites
- **Linux Server** (Arch Linux)
- **Python 3.9+** (Requires `python` and `python-virtualenv`)
- **Telegram Bot Token** (obtain from [@BotFather](https://t.me/BotFather))
- **NVIDIA API Key** (obtain from NVIDIA Developer portal)
- **Your Telegram ID** (to restrict bot access to yourself)

## Installation

**1. Clone the repository:**
```fish
git clone https://github.com/dmytrokurochkin/AI-Bot.git
cd AI-Bot
```

**2. Create and activate a virtual environment (for Fish shell):**
```fish
python -m venv venv
source venv/bin/activate.fish
```

**3. Install dependencies:**
```fish
pip install -r requirements.txt
```

**4. Configure environment variables:**
Create a `.env` file in the root directory of the project:
```fish
nano .env
```
Paste and fill in the following variables:
```env
BOT_TOKEN=your_telegram_bot_token_here
NVIDIA_API_KEY=your_nvidia_api_key_here
MODEL_NAME=meta/llama-3.1-70b-instruct  # Optional: Define your preferred model
ALLOWED_USER_IDS=123456789,987654321    # Comma-separated list of allowed Telegram user IDs
```

## Running as a Background Service (Systemd)

To make the bot work 24/7 and start automatically after your server reboots, configure it as a `systemd` service:

**1. Create a service file:**
```fish
sudo nano /etc/systemd/system/ai-bot.service
```

**2. Paste the following configuration:**
*(⚠️ Note: Replace `/path/to/AI-Bot` with the absolute path to your cloned repository, and `your_arch_user` with your actual Linux user)*
```ini
[Unit]
Description=Telegram AI Bot Service
After=network.target

[Service]
User=your_arch_user
WorkingDirectory=/path/to/AI-Bot
Environment="PATH=/path/to/AI-Bot/venv/bin"
ExecStart=/path/to/AI-Bot/venv/bin/python bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**3. Reload systemd and enable the service:**
```fish
sudo systemctl daemon-reload
sudo systemctl enable ai-bot.service
```

**4. Start the bot:**
```fish
sudo systemctl start ai-bot.service
```

**5. Check the status or logs:**
To verify the bot is running properly:
```fish
sudo systemctl status ai-bot.service
```
To monitor the real-time bot logs:
```fish
sudo journalctl -u ai-bot.service -f
```