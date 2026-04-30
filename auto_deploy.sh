#!/bin/bash
set -e

# Кольори для виводу
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Автоматичне налаштування AI-Bot (Debian/Ubuntu) ===${NC}"

# 1. Запит даних у користувача
echo -e "\n${BLUE}[1/4] Налаштування змінних оточення...${NC}"
if [ ! -f .env ]; then
    read -p "Введіть TELEGRAM_BOT_TOKEN: " bot_token
    read -p "Введіть NVIDIA_API_KEY: " nvidia_key
    read -p "Введіть ваші ALLOWED_USER_IDS (через кому, напр. 12345678,87654321): " user_ids

    cat > .env <<EOL
BOT_TOKEN=${bot_token}
NVIDIA_API_KEY=${nvidia_key}
MODEL_NAME=meta/llama-3.1-70b-instruct
ALLOWED_USER_IDS=${user_ids}
EOL
    echo -e "${GREEN}Файл .env створено!${NC}"
else
    echo ".env файл вже існує. Використовую його."
fi

# 2. Встановлення системних пакетів
echo -e "\n${BLUE}[2/4] Встановлення залежностей Debian/Ubuntu...${NC}"
SUDO=""
if [ "$EUID" -ne 0 ]; then
    SUDO="sudo"
fi
$SUDO apt-get update
$SUDO apt-get install -y python3 python3-pip python3-venv

# 3. Налаштування Python
echo -e "\n${BLUE}[3/4] Налаштування Python віртуального середовища...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}Залежності Python встановлено!${NC}"

# 4. Створення systemd сервісу (user-level)
echo -e "\n${BLUE}[4/4] Створення systemd сервісу для фонової роботи...${NC}"

mkdir -p ~/.config/systemd/user
WORK_DIR=$(pwd)

# Сервіс AI-бота
cat > ~/.config/systemd/user/ai-bot.service <<EOL
[Unit]
Description=Telegram AI Assistant Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=${WORK_DIR}
ExecStart=${WORK_DIR}/venv/bin/python3 bot.py
Restart=always
RestartSec=5
Environment="PATH=${WORK_DIR}/venv/bin:%E/PATH"

[Install]
WantedBy=default.target
EOL

systemctl --user daemon-reload
systemctl --user enable --now ai-bot.service

# Дозволити сервісам користувача працювати навіть після виходу з ssh
loginctl enable-linger $USER

echo -e "\n${GREEN}======================================================================${NC}"
echo -e "${GREEN}ГОТОВО! Ваш AI-Bot успішно встановлений та запущений у фоні.${NC}"
echo -e "======================================================================"
echo -e "🔄 Бот автоматично запуститься після перезавантаження сервера."
echo -e ""
echo -e "📋 Перевірити статус бота:        ${BLUE}systemctl --user status ai-bot${NC}"
echo -e "📋 Подивитись логи бота:          ${BLUE}journalctl --user -u ai-bot -f${NC}"
