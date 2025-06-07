# 🔐 Авторизация провайдера через JSON-ключ сервисного аккаунта
variable "service_account_key_file" {
  description = "Путь к JSON-ключу сервисного аккаунта, используемого в Terraform"
  type        = string
  default     = "admin-key.json"
}

# ☁️ Базовая конфигурация облака
variable "cloud_id" {
  description = "ID облака в Yandex Cloud"
  type        = string
}

variable "folder_id" {
  description = "ID каталога в Yandex Cloud"
  type        = string
}

# 🌐 Зона доступности и сеть
variable "zone" {
  description = "Зона доступности в Yandex Cloud"
  type        = string
  default     = "ru-central1-a"
}

variable "network_id" {
  description = "ID сети в Yandex Cloud"
  type        = string
  default     = "enpkktr4k8tdpi6l24oj"  # ID существующей сети
}

# 🔑 SSH ключи
variable "public_key_path" {
  description = "Путь к публичному SSH ключу"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

# 🖥️ Конфигурация кластера
variable "cluster_name" {
  description = "Имя создаваемого кластера Data Proc"
  type        = string
  default     = "spark-cluster"
}

# 🔗 Сеть — подсеть, из которой будет взята зона размещения кластера
variable "subnet_id" {
  description = "ID существующей подсети в выбранной зоне"
  type        = string
}

# 👤 ID сервисного аккаунта для Data Proc кластера
variable "service_account_id" {
  description = "ID сервисного аккаунта для Data Proc кластера"
  type        = string
}

# 🪣 S3 Configuration
variable "s3_bucket" {
  description = "S3 bucket for Data Proc cluster"
  type        = string
  default     = "otus-copy-b1gjj3po03aa3m4j8ps5"
}

variable "s3_access_key" {
  description = "Access key for S3 bucket"
  type        = string
}

variable "s3_secret_key" {
  description = "Secret key for S3 bucket"
  type        = string
  sensitive   = true
}