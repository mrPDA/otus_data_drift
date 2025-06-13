#!/bin/bash

# 🚀 Скрипт быстрого развертывания кластера DataProc
# Использует данные, собранные collect_cluster_info.sh

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

echo "🚀 БЫСТРОЕ РАЗВЕРТЫВАНИЕ КЛАСТЕРА DATAPROC"
echo "================================================="
echo ""

# Проверка наличия сгенерированного файла конфигурации
if [ ! -f "terraform.tfvars.generated" ]; then
    print_error "Файл terraform.tfvars.generated не найден!"
    echo "Сначала запустите: ./collect_cluster_info.sh"
    exit 1
fi

# Шаг 1: Копирование конфигурации
print_step "Копирование конфигурации"
cp terraform.tfvars.generated terraform.tfvars
print_success "Конфигурация скопирована"

# Шаг 2: Инициализация Terraform
print_step "Инициализация Terraform"
terraform init
print_success "Terraform инициализирован"

# Шаг 3: Проверка плана
print_step "Создание плана развертывания"
terraform plan -out=tfplan
print_success "План создан"

# Шаг 4: Подтверждение развертывания
echo ""
print_warning "Готов к развертыванию кластера DataProc"
echo "Конфигурация:"
echo "  - Master: s3-c2-m8, 40GB (1 хост)"
echo "  - Compute: s3-c4-m16, 128GB (2 хоста)"  
echo "  - Data: s3-c2-m8, 100GB (1 хост)"
echo ""

read -p "Продолжить развертывание? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Развертывание отменено"
    exit 1
fi

# Шаг 5: Развертывание
print_step "Развертывание кластера (это займет 10-15 минут)"
terraform apply tfplan
print_success "Кластер развернут!"

# Шаг 6: Получение информации о кластере
echo ""
print_step "Получение информации о кластере"
CLUSTER_ID=$(terraform output -raw cluster_id 2>/dev/null || echo "")

if [ -n "$CLUSTER_ID" ]; then
    print_success "Cluster ID: $CLUSTER_ID"
    
    # Получение IP адресов
    echo ""
    print_step "Получение IP адресов узлов"
    yc dataproc cluster list-hosts "$CLUSTER_ID" --format=table
    
    # Получение master IP для SSH
    MASTER_IP=$(yc dataproc cluster list-hosts "$CLUSTER_ID" --format=json | jq -r '.[] | select(.role=="MASTERNODE") | .assign_public_ip' 2>/dev/null || echo "")
    
    if [ -n "$MASTER_IP" ] && [ "$MASTER_IP" != "null" ] && [ "$MASTER_IP" != "false" ]; then
        echo ""
        print_success "🔗 Команды для подключения:"
        echo "SSH к master узлу:"
        echo "  ssh ubuntu@$MASTER_IP"
        echo ""
        echo "Jupyter Notebook:"
        echo "  http://$MASTER_IP:8888"
        echo ""
    fi
fi

# Создание файла с информацией о развертывании
cat > deployment_info.txt << EOF
Информация о развертывании кластера DataProc
============================================
Дата развертывания: $(date)
Cluster ID: $CLUSTER_ID

Конфигурация:
- Master: s3-c2-m8, 40GB SSD (1 хост)
- Compute: s3-c4-m16, 128GB SSD (2 хоста)
- Data: s3-c2-m8, 100GB SSD (1 хост)

Команды для управления:
- Остановка: terraform destroy
- Статус: yc dataproc cluster get $CLUSTER_ID
- Хосты: yc dataproc cluster list-hosts $CLUSTER_ID

SSH подключение:
ssh ubuntu@$MASTER_IP

Jupyter Notebook:
http://$MASTER_IP:8888
EOF

print_success "Информация сохранена в deployment_info.txt"
echo ""
print_success "🎉 Развертывание завершено успешно!"
echo ""
print_warning "Не забудьте остановить кластер после работы:"
echo "  terraform destroy"
