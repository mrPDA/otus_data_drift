# 🚀 СТАТУС JUPYTER И ТУННЕЛЯ

## ✅ Кластер DataProc развернут и настроен

**IP адрес кластера:** `YOUR_CLUSTER_IP`
**Дата настройки:** 13 июня 2025 г.

## ✅ Jupyter Notebook запущен и доступен

### 🔗 Доступ к Jupyter:
- **Через туннель:** http://localhost:8888
- **Напрямую:** http://YOUR_CLUSTER_IP:8888

### 📊 Статус сервисов:
- ✅ **Jupyter Notebook** - работает (процесс 23747, порт 8888)
- ✅ **SSH туннель** - активен
- ✅ **Интернет доступ** - настроен (security group обновлена)

### 🛠️ Установленные библиотеки:
- `jupyter notebook`
- `pandas`
- `numpy` 
- `matplotlib`
- `seaborn`

## 🔧 Полезные команды

### Управление туннелем:
```bash
# Проверить статус
./tunnel_helper.sh status

# Создать туннель для Jupyter
./tunnel_helper.sh jupyter

# Остановить туннели
./tunnel_helper.sh stop
```

### Управление Jupyter на кластере:
```bash
# Проверить процессы
ssh ubuntu@62.84.116.68 "pgrep -f jupyter"

# Посмотреть логи
ssh ubuntu@62.84.116.68 "tail -f jupyter.log"

# Остановить
ssh ubuntu@62.84.116.68 "pkill -f jupyter"

# Перезапустить
ssh ubuntu@62.84.116.68 "pkill -f jupyter && nohup jupyter notebook > jupyter.log 2>&1 &"
```

### Прямое подключение к кластеру:
```bash
# SSH подключение
ssh ubuntu@62.84.116.68

# Запуск Jupyter (если нужно)
./start_jupyter_simple.sh
```

## 🎯 Быстрый старт

1. **Проверить туннель:**
   ```bash
   ./tunnel_helper.sh status
   ```

2. **При необходимости создать туннель:**
   ```bash
   ./tunnel_helper.sh jupyter
   ```

3. **Открыть Jupyter:**
   - Браузер: http://localhost:8888
   - VS Code: Ctrl+Shift+P → "Open URL" → http://localhost:8888

## 🚨 Важные замечания

- **Не забывайте остановить кластер** после работы: `terraform destroy`
- Кластер имеет доступ к интернету для установки пакетов
- Jupyter настроен без паролей и токенов для удобства разработки
- Security group настроена на полный исходящий доступ

## 📝 Файлы проекта

- `tunnel_helper.sh` - управление туннелями
- `start_jupyter_simple.sh` - запуск Jupyter на кластере
- `quick_deploy.sh` - быстрое развертывание кластера
- `collect_cluster_info.sh` - сбор информации о ресурсах
- `main.tf` - основная конфигурация Terraform

**Статус:** ✅ **ВСЁ ГОТОВО К РАБОТЕ!**
