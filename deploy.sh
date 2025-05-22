#!/bin/bash

# Скрипт для автоматичного розгортання бота на хмарному сервері

# Перевіряємо аргументи
if [ "$#" -ne 1 ]; then
    echo "Використання: $0 [dev|prod]"
    exit 1
fi

ENV=$1
HOST=""
SSH_KEY="~/.ssh/id_rsa"

# Визначаємо хост в залежності від середовища
if [ "$ENV" == "dev" ]; then
    HOST="user@dev-server.example.com"
    echo "Розгортання на dev середовищі..."
elif [ "$ENV" == "prod" ]; then
    HOST="user@prod-server.example.com"
    echo "Розгортання на prod середовищі..."
    
    # Додаткова перевірка перед розгортанням на продакшн
    read -p "Ви впевнені, що хочете розгорнути на продакшн? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Розгортання скасовано."
        exit 0
    fi
else
    echo "Невідоме середовище: $ENV"
    echo "Використання: $0 [dev|prod]"
    exit 1
fi

# Архівуємо проект для передачі (без віртуального середовища і кешу)
echo "Архівування проекту..."
tar --exclude='venv' --exclude='__pycache__' --exclude='.git' -czf /tmp/finassistai-bot.tar.gz .

# Передаємо архів на сервер
echo "Передача файлів на сервер..."
scp -i $SSH_KEY /tmp/finassistai-bot.tar.gz $HOST:/tmp/

# Виконуємо розгортання на сервері
echo "Розгортання на сервері..."
ssh -i $SSH_KEY $HOST << 'EOF'
    mkdir -p ~/finassistai-bot
    tar -xzf /tmp/finassistai-bot.tar.gz -C ~/finassistai-bot
    cd ~/finassistai-bot
    
    # Створюємо віртуальне середовище, якщо воно не існує
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    # Активуємо віртуальне середовище та встановлюємо залежності
    source venv/bin/activate
    pip install -r requirements.txt
    
    # Створюємо необхідні директорії
    mkdir -p reports uploads/receipts uploads/statements
    
    # Запускаємо бота з використанням supervisor або systemd
    if command -v supervisorctl &> /dev/null; then
        # Використовуємо supervisor
        if [ -f "/etc/supervisor/conf.d/finassistai-bot.conf" ]; then
            supervisorctl restart finassistai-bot
        else
            # Створюємо конфігурацію supervisor
            sudo bash -c 'cat > /etc/supervisor/conf.d/finassistai-bot.conf << EOL
[program:finassistai-bot]
command=/home/user/finassistai-bot/venv/bin/python /home/user/finassistai-bot/bot.py
directory=/home/user/finassistai-bot
autostart=true
autorestart=true
stderr_logfile=/home/user/finassistai-bot/logs/bot.err.log
stdout_logfile=/home/user/finassistai-bot/logs/bot.out.log
user=user
environment=HOME="/home/user",USER="user"
EOL'
            mkdir -p ~/finassistai-bot/logs
            supervisorctl reread
            supervisorctl update
            supervisorctl start finassistai-bot
        fi
    else
        # Використовуємо systemd
        sudo bash -c 'cat > /etc/systemd/system/finassistai-bot.service << EOL
[Unit]
Description=FinAssistAI Telegram Bot
After=network.target

[Service]
User=user
WorkingDirectory=/home/user/finassistai-bot
ExecStart=/home/user/finassistai-bot/venv/bin/python /home/user/finassistai-bot/bot.py
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOL'
        sudo systemctl daemon-reload
        sudo systemctl enable finassistai-bot
        sudo systemctl restart finassistai-bot
    fi
    
    rm /tmp/finassistai-bot.tar.gz
EOF

echo "Розгортання завершено успішно!"
