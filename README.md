# OTUS Data Drift

Проект для создания Apache Spark кластера в Yandex Cloud с использованием Terraform для задач обнаружения и анализа дрейфа данных.

## Описание

Этот проект предоставляет инфраструктуру для развертывания Spark кластера в Yandex Cloud, который может быть использован для:
- Анализа дрейфа данных
- Обработки больших объемов данных
- Мониторинга качества данных
- Выполнения ETL операций

## Архитектура

Инфраструктура включает:
- **Master Node**: 1 узел с конфигурацией s3-c2-m8 (2 vCPU, 8 GB RAM, 40 GB SSD)
- **Data Nodes**: 3 узла с конфигурацией s3-c4-m16 (4 vCPU, 16 GB RAM, 128 GB SSD)
- **Security Group**: Настроенная группа безопасности для кластера
- **NAT Gateway**: Для доступа в интернет
- **VPC Subnet**: Выделенная подсеть для кластера

## Компоненты

- `main.tf` - Основная конфигурация Terraform
- `variables.tf` - Переменные проекта
- `outputs.tf` - Выходные значения
- `.env.example` - Пример файла с переменными окружения

## Предварительные требования

1. Terraform >= 0.13
2. Yandex Cloud CLI
3. Сервисный аккаунт в Yandex Cloud с необходимыми правами
4. SSH ключи для доступа к кластеру

## Установка и настройка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/your-username/otus_data_drift.git
cd otus_data_drift
```

2. Скопируйте файл с переменными окружения:
```bash
cp .env.example .env
```

3. Отредактируйте `.env` файл, указав ваши данные:
```bash
# Yandex Cloud Configuration
YC_CLOUD_ID=your-cloud-id
YC_FOLDER_ID=your-folder-id
YC_ZONE=ru-central1-a
YC_SERVICE_ACCOUNT_KEY_FILE=path/to/your/service-account-key.json
YC_SERVICE_ACCOUNT_ID=your-service-account-id
YC_NETWORK_ID=your-network-id

# SSH Configuration
PUBLIC_KEY_PATH=path/to/your/public-key.pub

# Cluster Configuration
CLUSTER_NAME=spark-data-drift-cluster
```

4. Инициализируйте Terraform:
```bash
terraform init
```

5. Проверьте план развертывания:
```bash
terraform plan
```

6. Примените конфигурацию:
```bash
terraform apply
```

## Использование

После успешного развертывания вы получите:
- IP адреса узлов кластера
- Информацию для подключения по SSH
- Веб-интерфейсы Spark и Hadoop

### Подключение к кластеру

```bash
ssh ubuntu@<master-node-ip>
```

### Запуск задач Spark

```bash
# Пример запуска Spark Shell
spark-shell

# Пример запуска PySpark
pyspark
```

## Мониторинг и управление

- **Spark UI**: http://master-node-ip:8080
- **Hadoop UI**: http://master-node-ip:9870
- **YARN UI**: http://master-node-ip:8088

## Безопасность

Кластер настроен с базовыми правилами безопасности:
- SSH доступ (порт 22)
- HTTPS доступ (порт 443)
- Внутренний трафик кластера
- Исходящие подключения к сервисам Yandex Cloud

## Очистка ресурсов

Для удаления всех созданных ресурсов:
```bash
terraform destroy
```

## Поддержка

Для вопросов и предложений создавайте Issues в этом репозитории.

## Лицензия

MIT License
