#!/bin/bash

# 🔌 Скрипт создания SSH туннеля к кластеру DataProc
# Обеспечивает безопасный доступ к Jupyter Notebook и другим сервисам

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

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Конфигурация
CLUSTER_IP="62.84.116.68"
USERNAME="ubuntu"

echo "🔌 СОЗДАНИЕ SSH ТУННЕЛЯ К КЛАСТЕРУ DATAPROC"
echo "=============================================="
echo ""
print_info "Кластер IP: $CLUSTER_IP"
echo ""

# Проверка доступности кластера
print_step "Проверка доступности кластера"
if ping -c 1 -W 3000 "$CLUSTER_IP" >/dev/null 2>&1; then
    print_success "Кластер доступен"
else
    print_warning "Кластер не отвечает на ping (возможно, ICMP заблокирован)"
fi

# Проверка SSH ключей
print_step "Проверка SSH ключей"
if [ -f ~/.ssh/id_rsa ]; then
    print_success "SSH ключ найден: ~/.ssh/id_rsa"
elif [ -f ~/.ssh/id_ed25519 ]; then
    print_success "SSH ключ найден: ~/.ssh/id_ed25519"
else
    print_error "SSH ключи не найдены в ~/.ssh/"
    echo "Создайте SSH ключ командой: ssh-keygen -t ed25519"
    exit 1
fi

# Меню выбора туннелей
echo ""
print_step "Выберите тип туннеля:"
echo "1) Jupyter Notebook (порт 8888 -> localhost:8888)"
echo "2) Jupyter + Spark UI (порты 8888, 4040 -> localhost:8888, 4040)"
echo "3) Полный туннель (Jupyter, Spark UI, Yarn, HDFS)"
echo "4) Пользовательский туннель"
echo ""

read -p "Выберите опцию (1-4): " choice

case $choice in
    1)
        TUNNELS="-L 8888:localhost:8888"
        DESCRIPTION="Jupyter Notebook"
        URLS=("http://localhost:8888")
        ;;
    2)
        TUNNELS="-L 8888:localhost:8888 -L 4040:localhost:4040"
        DESCRIPTION="Jupyter + Spark UI"
        URLS=("http://localhost:8888" "http://localhost:4040")
        ;;
    3)
        TUNNELS="-L 8888:localhost:8888 -L 4040:localhost:4040 -L 8088:localhost:8088 -L 9870:localhost:9870 -L 19888:localhost:19888"
        DESCRIPTION="Полный набор сервисов"
        URLS=("http://localhost:8888" "http://localhost:4040" "http://localhost:8088" "http://localhost:9870" "http://localhost:19888")
        ;;
    4)
        echo "Введите порты для туннелирования (например: 8888 4040 8080):"
        read -a ports
        TUNNELS=""
        URLS=()
        for port in "${ports[@]}"; do
            TUNNELS="$TUNNELS -L ${port}:localhost:${port}"
            URLS+=("http://localhost:${port}")
        done
        DESCRIPTION="Пользовательские порты: ${ports[*]}"
        ;;
    *)
        print_error "Неверный выбор"
        exit 1
        ;;
esac

echo ""
print_info "Настройка туннеля: $DESCRIPTION"
echo ""

# Создание туннеля
print_step "Создание SSH туннеля"
echo ""
print_warning "Туннель будет создан в фоновом режиме"
print_info "Для остановки используйте: kill \$(pgrep -f 'ssh.*$CLUSTER_IP')"
echo ""

# Проверка на существующие туннели
EXISTING_TUNNEL=$(pgrep -f "ssh.*$CLUSTER_IP" || true)
if [ -n "$EXISTING_TUNNEL" ]; then
    print_warning "Обнаружен существующий туннель (PID: $EXISTING_TUNNEL)"
    read -p "Закрыть существующий туннель? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kill "$EXISTING_TUNNEL"
        sleep 2
        print_success "Существующий туннель закрыт"
    else
        print_error "Отменено пользователем"
        exit 1
    fi
fi

# Создание туннеля с проверкой подключения
print_step "Установка соединения"
SSH_CMD="ssh -N -f $TUNNELS -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -o ExitOnForwardFailure=yes $USERNAME@$CLUSTER_IP"

echo "Команда SSH: $SSH_CMD"
echo ""

if $SSH_CMD; then
    print_success "SSH туннель успешно создан!"
    
    # Получение PID туннеля
    TUNNEL_PID=$(pgrep -f "ssh.*$CLUSTER_IP" || true)
    
    if [ -n "$TUNNEL_PID" ]; then
        print_success "PID туннеля: $TUNNEL_PID"
        
        # Сохранение информации о туннеле
        cat > tunnel_info.txt << EOF
Информация о SSH туннеле
========================
Дата создания: $(date)
Кластер IP: $CLUSTER_IP
PID процесса: $TUNNEL_PID
Описание: $DESCRIPTION

Активные порты:
EOF
        
        for url in "${URLS[@]}"; do
            echo "- $url" >> tunnel_info.txt
        done
        
        cat >> tunnel_info.txt << EOF

Команды управления:
- Проверка статуса: ps aux | grep $TUNNEL_PID
- Остановка туннеля: kill $TUNNEL_PID
- Принудительная остановка: kill -9 $TUNNEL_PID
- Остановка всех туннелей: pkill -f 'ssh.*$CLUSTER_IP'

SSH команда для прямого подключения:
ssh $USERNAME@$CLUSTER_IP
EOF
        
        print_success "Информация сохранена в tunnel_info.txt"
    fi
    
    echo ""
    print_success "🎉 Туннель готов к использованию!"
    echo ""
    print_info "Доступные сервисы:"
    for url in "${URLS[@]}"; do
        echo "  🔗 $url"
    done
    
    echo ""
    print_warning "Полезные команды:"
    echo "  Проверка туннеля: ps aux | grep 'ssh.*$CLUSTER_IP'"
    echo "  Остановка туннеля: kill \$(pgrep -f 'ssh.*$CLUSTER_IP')"
    echo "  Прямое SSH подключение: ssh $USERNAME@$CLUSTER_IP"
    
    # Проверка доступности Jupyter
    echo ""
    print_step "Проверка доступности Jupyter Notebook"
    sleep 3
    
    if curl -s -f http://localhost:8888 >/dev/null 2>&1; then
        print_success "Jupyter Notebook доступен: http://localhost:8888"
    else
        print_warning "Jupyter Notebook пока недоступен"
        print_info "Возможно, сервис еще запускается или требует настройка"
        print_info "Попробуйте запустить: ./start_jupyter.sh"
    fi
    
else
    print_error "Не удалось создать SSH туннель"
    echo ""
    print_info "Возможные причины:"
    echo "  1. Неверные SSH ключи"
    echo "  2. Кластер недоступен"
    echo "  3. Заняты локальные порты"
    echo ""
    print_info "Проверьте подключение: ssh $USERNAME@$CLUSTER_IP"
    exit 1
fi
