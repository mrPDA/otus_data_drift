#!/bin/bash

# 🔧 Упрощенный помощник для работы с туннелями

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

CLUSTER_IP="62.84.116.68"

echo "🔧 ТУННЕЛЬ ПОМОЩНИК"
echo "=================="
echo ""

# Функция проверки статуса туннелей
check_status() {
    print_step "Проверка статуса туннелей"
    
    TUNNELS=$(pgrep -f "ssh.*$CLUSTER_IP" || true)
    
    if [ -n "$TUNNELS" ]; then
        print_success "Активные туннели:"
        ps aux | grep "ssh.*$CLUSTER_IP" | grep -v grep
        echo ""
        
        # Проверка портов
        print_step "Проверка портов"
        for port in 8888 4040 8088 9870 19888; do
            if lsof -i ":$port" >/dev/null 2>&1; then
                echo -e "${GREEN}✅ localhost:$port - активен${NC}"
            else
                echo -e "${YELLOW}⚠️  localhost:$port - недоступен${NC}"
            fi
        done
    else
        print_warning "Туннели не найдены"
    fi
}

# Функция тестирования Jupyter
test_jupyter() {
    print_step "Тестирование Jupyter Notebook"
    
    if curl -s -f http://localhost:8888 >/dev/null 2>&1; then
        print_success "Jupyter доступен: http://localhost:8888"
        
        # Попытка получить информацию о токене
        if curl -s http://localhost:8888/api/status >/dev/null 2>&1; then
            echo "  📊 API статус: активен"
        fi
    else
        print_warning "Jupyter недоступен на localhost:8888"
        echo "  💡 Попробуйте: ./manage_tunnel.sh jupyter"
    fi
}

# Функция создания быстрого туннеля
quick_tunnel() {
    print_step "Создание быстрого туннеля для Jupyter"
    
    # Убиваем старые туннели
    pkill -f "ssh.*$CLUSTER_IP" || true
    sleep 1
    
    # Создаем новый туннель
    ssh -N -f -L 8888:localhost:8888 -o ServerAliveInterval=60 -o ServerAliveCountMax=3 ubuntu@$CLUSTER_IP
    
    if [ $? -eq 0 ]; then
        print_success "Туннель создан!"
        sleep 2
        test_jupyter
    else
        print_error "Ошибка создания туннеля"
    fi
}

# Функция остановки туннелей
stop_all() {
    print_step "Остановка всех туннелей"
    
    PIDS=$(pgrep -f "ssh.*$CLUSTER_IP" || true)
    
    if [ -n "$PIDS" ]; then
        echo "Останавливаем процессы: $PIDS"
        kill $PIDS
        sleep 2
        
        # Принудительная остановка
        REMAINING=$(pgrep -f "ssh.*$CLUSTER_IP" || true)
        if [ -n "$REMAINING" ]; then
            kill -9 $REMAINING
        fi
        
        print_success "Туннели остановлены"
    else
        print_warning "Нет активных туннелей"
    fi
}

# Главное меню
case "${1:-menu}" in
    "status")
        check_status
        ;;
    "jupyter")
        quick_tunnel
        ;;
    "test")
        test_jupyter
        ;;
    "stop")
        stop_all
        ;;
    *)
        echo "Использование:"
        echo "  $0 status   - проверить статус"
        echo "  $0 jupyter  - создать туннель для Jupyter"
        echo "  $0 test     - протестировать Jupyter"
        echo "  $0 stop     - остановить туннели"
        echo ""
        echo "Быстрые команды:"
        echo "  🚀 Создать туннель: $0 jupyter"
        echo "  🔍 Проверить статус: $0 status"
        echo "  🧪 Тест Jupyter: $0 test"
        ;;
esac
