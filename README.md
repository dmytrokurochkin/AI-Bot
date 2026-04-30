# AI-Bot 🤖

A smart Telegram AI Assistant powered by the NVIDIA API. It can answer complex questions, write and format programming code, and analyze provided images.

## Prerequisites
- **Linux Server** (Debian/Ubuntu highly recommended)
- **Telegram Bot Token** (obtain from [@BotFather](https://t.me/BotFather))
- **NVIDIA API Key** (obtain from NVIDIA Developer portal)
- **Your Telegram ID** (to restrict bot access to yourself)

## 🚀 Quick Automatic Installation (Debian/Ubuntu)

The easiest way to install and configure the bot is using the provided auto-deploy script. It will automatically install dependencies, set up the virtual environment, configure your tokens, and create a user-level `systemd` service so the bot runs 24/7.

**1. Clone the repository:**
```bash
git clone https://github.com/dmytrokurochkin/AI-Bot.git
cd AI-Bot
```

**2. Run the deployment script:**
```bash
chmod +x auto_deploy.sh
./auto_deploy.sh
```

**3. Follow the on-screen prompts.** You'll be asked to provide your Bot Token, NVIDIA API Key, and your Telegram User ID(s).

🎉 **And that's it!** The bot is now running in the background and will start automatically when your server reboots.

### Useful Commands (for auto-deployed bot)
- **Check Status:** `sudo systemctl status ai-bot`
- **View Logs:** `sudo journalctl -u ai-bot -f`
- **Restart the Bot:** `sudo systemctl restart ai-bot`
- **Stop the Bot:** `sudo systemctl stop ai-bot`

---

## 🛠️ Manual Installation

If you prefer to set up everything manually or are not using Debian/Ubuntu:

**1. Clone the repository:**
```bash
git clone https://github.com/dmytrokurochkin/AI-Bot.git
cd AI-Bot
```

**2. Install system dependencies:**
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv
```

**3. Create and activate a virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**4. Install Python dependencies:**
```bash
pip install -r requirements.txt
```

**5. Configure environment variables:**
Create a `.env` file in the root directory:
```bash
nano .env
```
Paste and fill in:
```env
BOT_TOKEN=your_telegram_bot_token_here
NVIDIA_API_KEY=your_nvidia_api_key_here
MODEL_NAME=meta/llama-3.1-70b-instruct
ALLOWED_USER_IDS=123456789
```

**6. Run the bot:**
```bash
python3 bot.py
```