🧹 РАЗМЕЩЕНИЕ ОЧИЩЕННЫХ ДАННЫХ

Очищенные данные размещены в бакете

s3a://otus-additional-bucket-b1gjj3po03aa3m4j8ps5/ml_ready_data_production/

🧹 ЭТАПЫ ОЧИСТКИ ДАННЫХ
Этап 1: Базовая валидация данных
pythonstep1_df = df.filter(
    col("transaction_id").isNotNull() &
    col("customer_id").isNotNull() & 
    col("terminal_id").isNotNull() &
    col("tx_amount").isNotNull() &
    col("tx_fraud").isNotNull() &
    (col("tx_amount") >= 0.0) &
    (col("tx_fraud").isin(0, 1)) &
    (col("customer_id") >= 0) &
    (col("terminal_id") >= 0) &
    (col("transaction_id") > 0)
)
Удаляет:

❌ NULL значения в ключевых полях (ID транзакции, клиента, терминала, суммы, флага мошенничества)
❌ Отрицательные суммы транзакций (tx_amount < 0)
❌ Некорректные флаги мошенничества (не 0 и не 1)
❌ Отрицательные ID клиентов и терминалов
❌ Нулевые или отрицательные ID транзакций

Этап 2: Статистические выбросы
python# Вычисляет квантили и IQR
q1, q3 = percentile_approx(tx_amount, 0.25), percentile_approx(tx_amount, 0.75)
p1, p99 = percentile_approx(tx_amount, 0.01), percentile_approx(tx_amount, 0.99)
iqr = q3 - q1

# Мягкие границы для сохранения данных
outlier_lower = q1 - 3.0 * iqr if q1 - 3.0 * iqr > p1 else p1
outlier_upper = q3 + 3.0 * iqr if q3 + 3.0 * iqr < p99 else p99
Удаляет:

📊 Экстремальные выбросы по сумме транзакций (используя правило 3×IQR)
📊 Аномально большие суммы (выше 99-го перцентиля + 3×IQR)
📊 Аномально малые суммы (ниже 1-го перцентиля - 3×IQR)

Особенность: Использует "мягкие границы" - не удаляет данные слишком агрессивно, ограничиваясь 1-99 перцентилями.
Этап 3: Дедупликация
pythonstep3_df = step2_df.dropDuplicates(["transaction_id"])
Удаляет:

🔄 Дублированные транзакции с одинаковым transaction_id

Этап 4: Логическая консистентность
pythonstep4_df = step3_df.filter(
    ~((col("tx_fraud") == 1) & (col("tx_fraud_scenario") == 0)) &
    ~((col("tx_fraud") == 0) & (col("tx_fraud_scenario") > 0))
)
Удаляет:

🚫 Логически противоречивые записи:

Транзакции помеченные как мошенничество (tx_fraud=1), но без сценария (tx_fraud_scenario=0)
Транзакции НЕ помеченные как мошенничество (tx_fraud=0), но с указанным сценарием мошенничества (tx_fraud_scenario>0)



📊 АНАЛИЗ КАЧЕСТВА ДАННЫХ
Детекция проблем:
pythonnull_counts = df_sample.select([
    count(when(col(c).isNull() | (col(c) == ""), c)).alias(f"{c}_nulls") 
    for c in df_sample.columns
]).collect()[0].asDict()
Анализирует:

🔍 NULL и пустые значения по каждой колонке
📈 Процент некорректных данных с использованием сэмплирования для больших данных
📋 Статистика очистки на каждом этапе

🎯 СПЕЦИФИКА ДЛЯ FRAUD DETECTION
Скрипт оптимизирован для данных по мошенничеству и учитывает:

Бизнес-логику - невозможность отрицательных сумм и ID
Целостность меток - консистентность флагов мошенничества
Статистические аномалии - выбросы в суммах транзакций
Временные данные - корректность timestamp'ов

📈 РЕЗУЛЬТАТ ОЧИСТКИ
Скрипт выводит детальную статистику:
Step 1 - Basic validation: 1,500,000 (50,000 removed)
Step 2 - Outlier removal: 1,480,000 (20,000 removed)  
Step 3 - Deduplication: 1,475,000 (5,000 removed)
Step 4 - Fraud logic: 1,470,000 (5,000 removed)
TOTAL CLEANED: 1,470,000 (94.8% retained)