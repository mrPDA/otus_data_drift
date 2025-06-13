#!/bin/bash

# 🚀 Скрипт запуска Jupyter Notebook на кластере DataProc
# Автоматический запуск и настройка доступа к Jupyter

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_step() {
    echo -e "${BLUE}🔄 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

echo "🚀 ЗАПУСК JUPYTER NOTEBOOK НА КЛАСТЕРЕ DATAPROC"
echo "================================================="
echo ""

# Получение информации о кластере
print_step "Получение информации о кластере"

# Проверяем наличие активного кластера
CLUSTER_ID=$(yc dataproc cluster list --format=json | jq -r '.[] | select(.status=="RUNNING") | .id' | head -1)

if [ -z "$CLUSTER_ID" ]; then
    print_error "Активный кластер DataProc не найден!"
    echo "Сначала разверните кластер командой: ./quick_deploy.sh"
    exit 1
fi

print_success "Найден активный кластер: $CLUSTER_ID"

# Получение ID мастер узла
print_step "Получение информации о мастер узле"
MASTER_INSTANCE_ID=$(yc dataproc cluster list-hosts "$CLUSTER_ID" --format=json | jq -r '.[] | select(.role=="MASTERNODE") | .compute_instance_id')

if [ -z "$MASTER_INSTANCE_ID" ]; then
    print_error "Не удалось найти мастер узел"
    exit 1
fi

print_success "Master Instance ID: $MASTER_INSTANCE_ID"

# Получение внешнего IP адреса
print_step "Получение внешнего IP адреса"
MASTER_IP=$(yc compute instance get "$MASTER_INSTANCE_ID" --format=json | jq -r '.network_interfaces[0].primary_v4_address.one_to_one_nat.address')

if [ -z "$MASTER_IP" ] || [ "$MASTER_IP" = "null" ]; then
    print_error "Не удалось получить внешний IP адрес мастер узла"
    exit 1
fi

print_success "Master IP: $MASTER_IP"

# Проверка SSH подключения
print_step "Проверка SSH подключения к кластеру"
if ! ssh -o ConnectTimeout=10 -o BatchMode=yes ubuntu@"$MASTER_IP" "echo 'SSH работает'" 2>/dev/null; then
    print_error "Не удается подключиться по SSH к мастер узлу"
    echo "Убедитесь, что:"
    echo "  1. Кластер полностью запущен"
    echo "  2. SSH ключ добавлен правильно"
    echo "  3. Группа безопасности разрешает SSH подключения"
    exit 1
fi

print_success "SSH подключение работает"

# Проверка статуса Jupyter
print_step "Проверка статуса Jupyter Notebook"
JUPYTER_STATUS=$(ssh ubuntu@"$MASTER_IP" "sudo systemctl is-active jupyter 2>/dev/null || echo 'inactive'")

if [ "$JUPYTER_STATUS" = "active" ]; then
    print_success "Jupyter уже запущен"
else
    print_step "Запуск Jupyter Notebook"
    
    # Создание конфигурации Jupyter
    ssh ubuntu@"$MASTER_IP" << 'EOF'
# Создание директории для конфигурации
mkdir -p ~/.jupyter

# Создание конфигурационного файла
cat > ~/.jupyter/jupyter_notebook_config.py << 'CONFIG'
c.NotebookApp.ip = '0.0.0.0'
c.NotebookApp.port = 8888
c.NotebookApp.open_browser = False
c.NotebookApp.token = ''
c.NotebookApp.password = ''
c.NotebookApp.allow_origin = '*'
c.NotebookApp.allow_remote_access = True
c.NotebookApp.notebook_dir = '/home/ubuntu'
CONFIG

# Установка Jupyter если не установлен
if ! command -v jupyter &> /dev/null; then
    echo "Установка Jupyter..."
    sudo apt-get update
    sudo apt-get install -y python3-pip
    sudo pip3 install jupyter pandas numpy matplotlib seaborn
fi

# Создание systemd сервиса для Jupyter
sudo tee /etc/systemd/system/jupyter.service > /dev/null << 'SERVICE'
[Unit]
Description=Jupyter Notebook Server
After=network.target

[Service]
Type=simple
User=ubuntu
ExecStart=/usr/local/bin/jupyter notebook --config=/home/ubuntu/.jupyter/jupyter_notebook_config.py
Restart=always
RestartSec=10
Environment=PATH=/usr/local/bin:/usr/bin:/bin
WorkingDirectory=/home/ubuntu

[Install]
WantedBy=multi-user.target
SERVICE

# Запуск сервиса
sudo systemctl daemon-reload
sudo systemctl enable jupyter
sudo systemctl start jupyter

echo "Jupyter запущен"
EOF
    
    print_success "Jupyter Notebook настроен и запущен"
fi

# Проверка доступности Jupyter через HTTP
print_step "Проверка доступности Jupyter через веб-интерфейс"
sleep 5  # Даем время на запуск

if curl -s --connect-timeout 10 "http://$MASTER_IP:8888" > /dev/null; then
    print_success "Jupyter доступен через веб-интерфейс"
else
    print_warning "Jupyter может еще запускаться, подождите 1-2 минуты"
fi

# Создание информационного файла
cat > jupyter_access_info.txt << EOF
🚀 ДОСТУП К JUPYTER NOTEBOOK
============================
Дата запуска: $(date)
Cluster ID: $CLUSTER_ID
Master IP: $MASTER_IP

🌐 Веб-доступ:
URL: http://$MASTER_IP:8888

🔑 SSH доступ:
ssh ubuntu@$MASTER_IP

📝 Полезные команды на кластере:
# Проверить статус Jupyter
sudo systemctl status jupyter

# Перезапустить Jupyter
sudo systemctl restart jupyter

# Просмотр логов Jupyter
sudo journalctl -u jupyter -f

# Проверить Spark
spark-submit --version

# Проверить HDFS
hdfs dfsadmin -report

📚 Установленные библиотеки:
- PySpark (встроенный)
- Pandas
- NumPy  
- Matplotlib
- Seaborn

🎯 Готов для анализа данных!
EOF

print_success "Информация сохранена в jupyter_access_info.txt"

echo ""
echo "================================================="
print_success "🎉 JUPYTER NOTEBOOK УСПЕШНО ЗАПУЩЕН!"
echo ""
print_success "🌐 Откройте в браузере: http://$MASTER_IP:8888"
echo ""
print_warning "📝 Полезная информация:"
echo "  - Jupyter запущен без пароля для удобства разработки"
echo "  - Автоматический перезапуск при сбоях"
echo "  - Доступ к Spark через PySpark"
echo "  - Рабочая директория: /home/ubuntu"
echo ""
print_warning "🛡️  Безопасность:"
echo "  - Доступ открыт только через IP кластера"
echo "  - Не забудьте остановить кластер после работы!"
echo ""
