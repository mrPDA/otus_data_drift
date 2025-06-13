#!/bin/bash

# 🚀 Скрипт для сбора информации о кластере DataProc в Yandex Cloud
# Автор: Денис Пукинов
# Дата: $(date +"%Y-%m-%d")
# Назначение: Быстрый сбор данных для восстановления кластера ИИ

set -e

echo "🔍 СБОР ИНФОРМАЦИИ ДЛЯ РАЗВЕРТЫВАНИЯ КЛАСТЕРА DATAPROC"
echo "=================================================================="
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Функция для вывода секций
print_section() {
    echo -e "${BLUE}📋 $1${NC}"
    echo "----------------------------------------"
}

# Функция для вывода значений
print_value() {
    echo -e "${GREEN}$1:${NC} $2"
}

# Функция для вывода предупреждений
print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Функция для вывода ошибок
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Проверка наличия yc CLI
if ! command -v yc &> /dev/null; then
    print_error "Yandex Cloud CLI не установлен или не найден в PATH"
    exit 1
fi

# Получение текущей конфигурации
print_section "БАЗОВАЯ КОНФИГУРАЦИЯ YANDEX CLOUD"
CLOUD_ID=$(yc config get cloud-id 2>/dev/null || echo "NOT_SET")
FOLDER_ID=$(yc config get folder-id 2>/dev/null || echo "NOT_SET")

print_value "Cloud ID" "$CLOUD_ID"
print_value "Folder ID" "$FOLDER_ID"
print_value "Зона по умолчанию" "ru-central1-a"
echo ""

# Проверка сервисного аккаунта
print_section "СЕРВИСНЫЙ АККАУНТ"
if [ -f "create-admin-sa/admin-key.json" ]; then
    SA_ID=$(cat create-admin-sa/admin-key.json | grep -o '"service_account_id": "[^"]*"' | cut -d'"' -f4)
    print_value "Service Account ID" "$SA_ID"
    print_value "Ключ сервисного аккаунта" "create-admin-sa/admin-key.json ✅"
else
    print_error "Файл ключа сервисного аккаунта не найден: create-admin-sa/admin-key.json"
fi
echo ""

# Проверка S3 ключей
print_section "S3 КОНФИГУРАЦИЯ"
if [ -f "create-admin-sa/s3-access-key.json" ]; then
    S3_ACCESS_KEY=$(cat create-admin-sa/s3-access-key.json | grep -o '"key_id": "[^"]*"' | cut -d'"' -f4)
    S3_SECRET_KEY=$(cat create-admin-sa/s3-access-key.json | grep -o '"secret": "[^"]*"' | cut -d'"' -f4)
    print_value "S3 Access Key" "${S3_ACCESS_KEY:0:10}...*** (скрыто для безопасности)"
    print_value "S3 Secret Key" "***...*** (скрыто для безопасности)"
    print_value "S3 Bucket" "otus-copy-$FOLDER_ID"
else
    print_error "Файл S3 ключей не найден: create-admin-sa/s3-access-key.json"
fi
echo ""

# Проверка SSH ключей
print_section "SSH КОНФИГУРАЦИЯ"
if [ -f "$HOME/.ssh/id_rsa.pub" ]; then
    SSH_KEY_SIZE=$(wc -c < "$HOME/.ssh/id_rsa.pub")
    print_value "SSH публичный ключ" "$HOME/.ssh/id_rsa.pub ✅ ($SSH_KEY_SIZE bytes)"
else
    print_warning "SSH ключ не найден в стандартном месте: $HOME/.ssh/id_rsa.pub"
fi
echo ""

# Проверка сетевой конфигурации
print_section "СЕТЕВАЯ КОНФИГУРАЦИЯ"
echo "🔍 Получение информации о сетях..."
NETWORKS=$(yc vpc network list --format=json 2>/dev/null || echo "[]")
DEFAULT_NETWORK_ID=$(echo "$NETWORKS" | jq -r '.[] | select(.name=="default") | .id' 2>/dev/null || echo "")

if [ -n "$DEFAULT_NETWORK_ID" ] && [ "$DEFAULT_NETWORK_ID" != "null" ]; then
    print_value "Network ID (default)" "$DEFAULT_NETWORK_ID"
else
    # Получаем первую доступную сеть
    FIRST_NETWORK_ID=$(echo "$NETWORKS" | jq -r '.[0].id' 2>/dev/null || echo "")
    if [ -n "$FIRST_NETWORK_ID" ] && [ "$FIRST_NETWORK_ID" != "null" ]; then
        print_value "Network ID (первая доступная)" "$FIRST_NETWORK_ID"
    else
        print_error "Сети не найдены"
    fi
fi
echo ""

# Проверка существующих ресурсов
print_section "СУЩЕСТВУЮЩИЕ РЕСУРСЫ"
echo "🔍 Проверка существующих кластеров DataProc..."
CLUSTERS=$(yc dataproc cluster list --format=json 2>/dev/null || echo "[]")
CLUSTER_COUNT=$(echo "$CLUSTERS" | jq length 2>/dev/null || echo "0")
print_value "Активные кластеры DataProc" "$CLUSTER_COUNT"

if [ "$CLUSTER_COUNT" -gt 0 ]; then
    echo "$CLUSTERS" | jq -r '.[] | "  - " + .name + " (ID: " + .id + ", Status: " + .status + ")"' 2>/dev/null || true
fi
echo ""

# Проверка групп безопасности
echo "🔍 Проверка групп безопасности..."
SECURITY_GROUPS=$(yc vpc security-group list --format=json 2>/dev/null || echo "[]")
SG_COUNT=$(echo "$SECURITY_GROUPS" | jq length 2>/dev/null || echo "0")
print_value "Группы безопасности" "$SG_COUNT"

# Ищем группу dataproc-security-group
DATAPROC_SG_ID=$(echo "$SECURITY_GROUPS" | jq -r '.[] | select(.name=="dataproc-security-group") | .id' 2>/dev/null || echo "")
if [ -n "$DATAPROC_SG_ID" ] && [ "$DATAPROC_SG_ID" != "null" ]; then
    print_value "DataProc Security Group" "$DATAPROC_SG_ID ✅"
fi
echo ""

# Проверка подсетей
echo "🔍 Проверка подсетей..."
SUBNETS=$(yc vpc subnet list --format=json 2>/dev/null || echo "[]")
DATAPROC_SUBNET_ID=$(echo "$SUBNETS" | jq -r '.[] | select(.name=="dataproc-subnet") | .id' 2>/dev/null || echo "")
if [ -n "$DATAPROC_SUBNET_ID" ] && [ "$DATAPROC_SUBNET_ID" != "null" ]; then
    print_value "DataProc Subnet" "$DATAPROC_SUBNET_ID ✅"
fi
echo ""

# Генерация terraform.tfvars
print_section "ГЕНЕРАЦИЯ TERRAFORM.TFVARS"
TFVARS_FILE="terraform.tfvars.generated"

cat > "$TFVARS_FILE" << EOF
# Автоматически сгенерированный файл terraform.tfvars
# Дата генерации: $(date +"%Y-%m-%d %H:%M:%S")

# Yandex Cloud Configuration
cloud_id                   = "$CLOUD_ID"
folder_id                  = "$FOLDER_ID"
zone                       = "ru-central1-a"
service_account_key_file   = "create-admin-sa/admin-key.json"
service_account_id         = "$SA_ID"
network_id                 = "${DEFAULT_NETWORK_ID:-$FIRST_NETWORK_ID}"

# SSH Configuration
public_key_path            = "~/.ssh/id_rsa.pub"

# Cluster Configuration
cluster_name               = "spark-data-drift-cluster"

# S3 Configuration
s3_bucket                  = "otus-copy-$FOLDER_ID"
s3_access_key              = "REPLACE_WITH_YOUR_S3_ACCESS_KEY"
s3_secret_key              = "REPLACE_WITH_YOUR_S3_SECRET_KEY"
EOF

print_value "Сгенерирован файл" "$TFVARS_FILE ✅"
echo ""

# Рекомендуемая конфигурация кластера
print_section "РЕКОМЕНДУЕМАЯ КОНФИГУРАЦИЯ КЛАСТЕРА"
cat << EOF
📋 Конфигурация подкластеров для main.tf:

🎯 Master подкластер:
  - Роль: MASTERNODE
  - Класс хоста: s3-c2-m8 (2 vCPU, 8GB RAM)
  - Диск: 40GB network-ssd
  - Количество хостов: 1

💻 Compute подкластер:
  - Роль: COMPUTENODE  
  - Класс хоста: s3-c4-m16 (4 vCPU, 16GB RAM)
  - Диск: 128GB network-ssd
  - Количество хостов: 2

💾 Data подкластер:
  - Роль: DATANODE
  - Класс хоста: s3-c2-m8 (2 vCPU, 8GB RAM)
  - Диск: 100GB network-ssd
  - Количество хостов: 1

📊 Общие ресурсы: 12 vCPU, 48GB RAM, 368GB SSD
EOF
echo ""

# Команды для быстрого развертывания
print_section "КОМАНДЫ ДЛЯ БЫСТРОГО РАЗВЕРТЫВАНИЯ"
cat << EOF
🚀 Последовательность команд для развертывания:

1. Копирование конфигурации:
   cp $TFVARS_FILE terraform.tfvars

2. Инициализация Terraform:
   terraform init

3. Проверка плана:
   terraform plan

4. Развертывание кластера:
   terraform apply -auto-approve

5. Проверка статуса:
   yc dataproc cluster list

🔗 После развертывания доступ по SSH:
   ssh ubuntu@<MASTER_NODE_IP>

📝 Jupyter Notebook будет доступен на:
   http://<MASTER_NODE_IP>:8888
EOF
echo ""

# Проверка состояния terraform
print_section "СОСТОЯНИЕ TERRAFORM"
if [ -f "terraform.tfstate" ]; then
    TFSTATE_SIZE=$(wc -c < "terraform.tfstate")
    print_value "Terraform State" "terraform.tfstate ✅ ($TFSTATE_SIZE bytes)"
    
    # Попытка получить информацию о ресурсах из state
    if command -v terraform &> /dev/null; then
        RESOURCES_COUNT=$(terraform state list 2>/dev/null | wc -l || echo "0")
        print_value "Ресурсы в состоянии" "$RESOURCES_COUNT"
    fi
else
    print_warning "Файл состояния terraform.tfstate не найден"
fi
echo ""

print_section "ИТОГОВАЯ ИНФОРМАЦИЯ"
echo "✅ Скрипт завершен успешно"
echo "📄 Сгенерированный файл конфигурации: $TFVARS_FILE"
echo "🔄 Для развертывания используйте команды выше"
echo ""
print_warning "Убедитесь, что все файлы ключей существуют перед развертыванием!"
echo ""
echo "=================================================================="
echo "🎯 Готово для передачи ИИ для быстрой настройки кластера!"
