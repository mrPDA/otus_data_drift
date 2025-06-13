# ML Data Pipeline for Yandex Cloud DataProc
# Optimized for large-scale fraud detection dataset processing
# GitHub Public Version - Anonymized

import os
import sys
from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, when, isnan, isnull, count, mean, stddev, min as spark_min, max as spark_max,
    broadcast, monotonically_increasing_id, hash, abs as spark_abs,
    dayofweek, hour, minute, lag, lead, row_number, dense_rank, log,
    regexp_replace, trim, upper, coalesce, expr
)
from pyspark.sql.window import Window
from pyspark.sql.types import *
from pyspark import StorageLevel
from datetime import datetime, timedelta
import logging

# ────────────────────────────────────────────────────────────────────
# CONFIGURATION VARIABLES - UPDATE THESE FOR YOUR ENVIRONMENT
# ────────────────────────────────────────────────────────────────────
# S3 Buckets - replace with your bucket names
SOURCE_BUCKET = "your-source-bucket-name"
OUTPUT_BUCKET = "your-output-bucket-name"

# Data paths
TARGET_FILE_PATH = f"s3a://{SOURCE_BUCKET}/*.txt"  # Adjust file pattern as needed
PARQUET_OUTPUT_DIR = f"s3a://{OUTPUT_BUCKET}/ml_ready_data/"

# S3A Credentials - REPLACE WITH YOUR CREDENTIALS
S3A_ACCESS_KEY = "YOUR_ACCESS_KEY_HERE"
S3A_SECRET_KEY = "YOUR_SECRET_KEY_HERE"
S3A_ENDPOINT = "storage.yandexcloud.net"  # Or your S3 endpoint

# Schema for fraud detection dataset - adjust for your data structure
schema = StructType([
    StructField("transaction_id", LongType(), True),
    StructField("tx_datetime", StringType(), True),
    StructField("customer_id", IntegerType(), True),
    StructField("terminal_id", IntegerType(), True),
    StructField("tx_amount", DecimalType(10, 2), True),
    StructField("tx_time_seconds", IntegerType(), True),
    StructField("tx_time_days", IntegerType(), True),
    StructField("tx_fraud", ByteType(), True),
    StructField("tx_fraud_scenario", ByteType(), True)
])

# ────────────────────────────────────────────────────────────────────
# ENVIRONMENT SETUP FOR YANDEX CLOUD DATAPROC
# ────────────────────────────────────────────────────────────────────
def setup_dataproc_environment():
    """Setup environment for Yandex Cloud DataProc cluster"""
    
    # Check if running on DataProc cluster
    is_on_cluster = Path('/usr/lib/spark').exists()
    
    if is_on_cluster:
        print("🎯 Detected Yandex Cloud DataProc cluster")
        
        # Set Spark environment variables
        os.environ['SPARK_HOME'] = '/usr/lib/spark'
        os.environ['JAVA_HOME'] = '/usr/lib/jvm/java-8-openjdk-amd64'
        os.environ['HADOOP_HOME'] = '/usr/lib/hadoop'
        os.environ['HADOOP_CONF_DIR'] = '/etc/hadoop/conf'
        os.environ['YARN_CONF_DIR'] = '/etc/hadoop/conf'
        
        # Add PySpark to Python path
        spark_python_path = '/usr/lib/spark/python'
        py4j_path = '/usr/lib/spark/python/lib/py4j-0.10.9-src.zip'
        
        if spark_python_path not in sys.path:
            sys.path.insert(0, spark_python_path)
            print(f"➕ Added to path: {spark_python_path}")
            
        if py4j_path not in sys.path:
            sys.path.insert(0, py4j_path)
            print(f"➕ Added to path: {py4j_path}")
            
        # Update PYTHONPATH
        current_pythonpath = os.environ.get('PYTHONPATH', '')
        new_paths = [spark_python_path, py4j_path]
        
        pythonpath_parts = []
        for path in new_paths:
            if path not in current_pythonpath:
                pythonpath_parts.append(path)
        
        if current_pythonpath:
            pythonpath_parts.append(current_pythonpath)
            
        os.environ['PYTHONPATH'] = ':'.join(pythonpath_parts)
        print(f"🔧 PYTHONPATH updated")
        
        # Verify paths exist
        paths_to_check = {
            'SPARK_HOME': os.environ['SPARK_HOME'],
            'JAVA_HOME': os.environ['JAVA_HOME'], 
            'HADOOP_HOME': os.environ['HADOOP_HOME'],
            'HADOOP_CONF_DIR': os.environ['HADOOP_CONF_DIR']
        }
        
        for name, path in paths_to_check.items():
            if Path(path).exists():
                print(f"✅ {name}: {path}")
            else:
                print(f"❌ {name}: {path} - DOES NOT EXIST")
        
        print("✅ Environment configured for DataProc cluster")
        return True
    else:
        print("⚠️ Cluster not detected - attempting PySpark installation")
        import subprocess
        try:
            result = subprocess.run(['pip3', 'install', '--user', 'pyspark==3.0.3'], 
                                  capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                print("✅ PySpark installed via pip")
            else:
                print(f"❌ Installation error: {result.stderr}")
        except Exception as e:
            print(f"❌ Pip execution error: {e}")
        return False

# ────────────────────────────────────────────────────────────────────
# HDFS AUTO-DETECTION for automatic configuration
# ────────────────────────────────────────────────────────────────────
def get_hdfs_namenode():
    """Automatically detect HDFS namenode from cluster configuration"""
    try:
        # Read Hadoop configuration files
        hadoop_conf_paths = [
            '/etc/hadoop/conf/core-site.xml',
            '/usr/lib/hadoop/etc/hadoop/core-site.xml',
            '/opt/hadoop/etc/hadoop/core-site.xml'
        ]
        
        for conf_path in hadoop_conf_paths:
            if Path(conf_path).exists():
                print(f"📋 Reading Hadoop config from: {conf_path}")
                with open(conf_path, 'r') as f:
                    content = f.read()
                    # Look for fs.defaultFS
                    import re
                    match = re.search(r'<name>fs\.defaultFS</name>\s*<value>(hdfs://[^<]+)</value>', content)
                    if match:
                        hdfs_uri = match.group(1)
                        print(f"🎯 Auto-detected HDFS: {hdfs_uri}")
                        return hdfs_uri
        
        # If not found in config, try hostname-based detection
        import socket
        hostname = socket.gethostname()
        if 'dataproc-m-' in hostname:
            hdfs_uri = f"hdfs://{hostname}:8020"
            print(f"🔍 Using hostname-based HDFS: {hdfs_uri}")
            return hdfs_uri
            
        # Fallback for local testing
        print("⚠️ HDFS namenode not found, using local fallback")
        return "file:///"
        
    except Exception as e:
        print(f"❌ Error detecting HDFS: {e}")
        return "file:///"

# ────────────────────────────────────────────────────────────────────
# SPARK SESSION CONFIGURATION
# ────────────────────────────────────────────────────────────────────
def create_optimized_spark_session():
    """Create Spark session optimized for DataProc cluster"""
    
    # Close existing session if it exists
    active = SparkSession.getActiveSession()
    if active and active.sparkContext.master.startswith("local"):
        print(f"🛑 Detected local master ({active.sparkContext.master}) → stopping it.")
        active.stop()
        active = None
    
    if not active:
        # Auto-detect HDFS namenode
        hdfs_namenode = get_hdfs_namenode()
        
        return (
            SparkSession.builder
            .appName("ML-DataPipeline-Optimized")
            .master("yarn")
            .config("spark.submit.deployMode", "client")
            
            # HDFS configuration (automatically detected)
            .config("spark.hadoop.fs.defaultFS", hdfs_namenode)
            .config("spark.hadoop.fs.default.name", hdfs_namenode)
            
            # RESOURCE CONFIGURATION - adjust for your cluster size
            .config("spark.executor.instances", "4")
            .config("spark.executor.memory", "12g")
            .config("spark.executor.cores", "3")
            .config("spark.executor.memoryOverhead", "2g")
            .config("spark.driver.memory", "4g")
            .config("spark.driver.cores", "2")
            
            # PERFORMANCE SETTINGS
            .config("spark.sql.shuffle.partitions", "200")
            .config("spark.default.parallelism", "48")
            .config("spark.sql.adaptive.enabled", "true")
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
            .config("spark.sql.adaptive.coalescePartitions.initialPartitionNum", "200")
            
            # YARN STAGING (automatically determined)
            .config("spark.yarn.stagingDir", f"{hdfs_namenode}/user/ubuntu/spark-staging")
            
            # S3A SETTINGS - UPDATE WITH YOUR CREDENTIALS
            .config("spark.hadoop.fs.s3a.endpoint", S3A_ENDPOINT)
            .config("spark.hadoop.fs.s3a.access.key", S3A_ACCESS_KEY)
            .config("spark.hadoop.fs.s3a.secret.key", S3A_SECRET_KEY)
            .config("spark.hadoop.fs.s3a.path.style.access", "true")
            .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "true")
            .config("spark.hadoop.fs.s3a.multipart.size", "67108864")
            .config("spark.hadoop.fs.s3a.fast.upload", "true")
            .config("spark.hadoop.fs.s3a.connection.maximum", "50")
            .config("spark.hadoop.fs.s3a.threads.max", "5")
            
            # MEMORY OPTIMIZATIONS
            .config("spark.executor.memoryFraction", "0.8")
            .config("spark.storage.memoryFraction", "0.3")
            .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
            
            # PARQUET OPTIMIZATIONS
            .config("spark.sql.parquet.compression.codec", "snappy")
            .config("spark.sql.parquet.filterPushdown", "true")
            .config("spark.sql.parquet.enableVectorizedReader", "true")
            
            .getOrCreate()
        )
    else:
        return active

# ======================================================================
#  MAIN ML DATA PIPELINE
#  Optimized for large-scale fraud detection dataset processing
# ======================================================================

# Setup environment and create Spark session
setup_dataproc_environment()
spark = create_optimized_spark_session()
print("🚀 Optimized SparkContext ready →", spark.sparkContext.master)

# ────────────────────────────────────────────────────────────────────
# DATA READING WITH MEMORY EFFICIENCY
# ────────────────────────────────────────────────────────────────────
print("📖 Reading data with memory-efficient approach...")

def read_large_file_efficiently(file_path, schema, chunk_size_mb=1000):
    """Efficiently read large files"""
    
    # For testing with limit - uncomment if needed
    # return (spark.read.schema(schema)
    #        .option("delimiter", ",")
    #        .option("header", "true")
    #        .csv(file_path)
    #        .limit(100000))
    
    # For production - full file
    return (spark.read.schema(schema)
           .option("delimiter", ",")
           .option("header", "true")
           .option("timestampFormat", "yyyy-MM-dd HH:mm:ss")
           .option("multiline", "false")
           .option("escape", '"')
           .csv(file_path))

df_raw = read_large_file_efficiently(TARGET_FILE_PATH, schema)
df_raw = df_raw.repartition(200)  # Optimize partitioning

initial_count = df_raw.count()
print(f"📥 Initial data loaded: {initial_count:,} rows")

# ────────────────────────────────────────────────────────────────────
# DATA QUALITY ANALYSIS
# ────────────────────────────────────────────────────────────────────
def analyze_data_quality_efficient(df, name="Dataset", sample_size=1000000):
    """Efficient data quality analysis with sampling"""
    print(f"\n📊 DATA QUALITY ANALYSIS: {name}")
    
    total_rows = df.count()
    
    # Use sampling for large datasets
    if total_rows > sample_size:
        sample_fraction = sample_size / total_rows
        df_sample = df.sample(False, sample_fraction, seed=42)
        print(f"  📊 Using sample: {sample_size:,} rows ({sample_fraction:.4f} fraction)")
    else:
        df_sample = df
    
    # Count NULL/NA values on sample
    null_counts = df_sample.select([
        count(when(col(c).isNull() | (col(c) == ""), c)).alias(f"{c}_nulls") 
        for c in df_sample.columns if not c.startswith("row_")
    ]).collect()[0].asDict()
    
    sample_rows = df_sample.count()
    
    print("NULL/NA Analysis (sampled):")
    for col_name, null_count in null_counts.items():
        col_clean = col_name.replace("_nulls", "")
        null_pct = (null_count / sample_rows) * 100
        print(f"  {col_clean}: {null_count:,} ({null_pct:.2f}%)")

analyze_data_quality_efficient(df_raw, "Raw Data")

# ────────────────────────────────────────────────────────────────────
# MEMORY-EFFICIENT DATA CLEANING
# ────────────────────────────────────────────────────────────────────
def clean_for_ml_efficient(df):
    """Efficient data cleaning for large datasets"""
    print("\n🧹 MEMORY-EFFICIENT DATA CLEANING")
    
    initial_count = df.count()
    
    # Step 1: Basic validation
    step1_df = df.filter(
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
    ).cache()
    
    step1_count = step1_df.count()
    print(f"  Step 1 - Basic validation: {step1_count:,} ({initial_count - step1_count:,} removed)")
    
    # Step 2: Statistical outlier removal
    if step1_count >= 1000:
        sample_fraction = 1000000.0 / step1_count if step1_count > 1000000 else 1.0
        sample_for_stats = step1_df.sample(False, sample_fraction, seed=42)
        
        amount_stats = sample_for_stats.select(
            expr("percentile_approx(tx_amount, 0.25)").alias("q1"),
            expr("percentile_approx(tx_amount, 0.75)").alias("q3"),
            expr("percentile_approx(tx_amount, 0.01)").alias("p1"),
            expr("percentile_approx(tx_amount, 0.99)").alias("p99")
        ).collect()[0]
        
        q1, q3 = float(amount_stats["q1"]), float(amount_stats["q3"])
        p1, p99 = float(amount_stats["p1"]), float(amount_stats["p99"])
        iqr = q3 - q1
        
        # Soft boundaries to preserve data
        outlier_lower = q1 - 3.0 * iqr if q1 - 3.0 * iqr > p1 else p1
        outlier_upper = q3 + 3.0 * iqr if q3 + 3.0 * iqr < p99 else p99
        
        step2_df = step1_df.filter(
            (col("tx_amount") >= outlier_lower) & 
            (col("tx_amount") <= outlier_upper)
        )
        
        step2_count = step2_df.count()
        print(f"  Step 2 - Outlier removal: {step2_count:,} ({step1_count - step2_count:,} removed)")
        print(f"    Amount range: {outlier_lower:.2f} to {outlier_upper:.2f}")
    else:
        step2_df = step1_df
        step2_count = step1_count
    
    step1_df.unpersist()
    
    # Step 3: Deduplication
    step3_df = step2_df.dropDuplicates(["transaction_id"])
    step3_count = step3_df.count()
    print(f"  Step 3 - Deduplication: {step3_count:,} ({step2_count - step3_count:,} removed)")
    
    # Step 4: Fraud logic consistency
    step4_df = step3_df.filter(
        ~((col("tx_fraud") == 1) & (col("tx_fraud_scenario") == 0)) &
        ~((col("tx_fraud") == 0) & (col("tx_fraud_scenario") > 0))
    )
    step4_count = step4_df.count()
    print(f"  Step 4 - Fraud logic: {step4_count:,} ({step3_count - step4_count:,} removed)")
    
    print(f"  💚 TOTAL CLEANED: {step4_count:,} ({((step4_count/initial_count)*100):.1f}% retained)")
    
    return step4_df

# ────────────────────────────────────────────────────────────────────
# FEATURE ENGINEERING
# ────────────────────────────────────────────────────────────────────
def create_ml_features_efficient(df):
    """Efficient feature creation for ML"""
    print("\n🔧 EFFICIENT FEATURE ENGINEERING")
    
    # Basic temporal features
    df_features = df.withColumn("tx_timestamp", 
                               col("tx_datetime").cast(TimestampType()))
    
    # Batch creation of temporal features
    df_features = (df_features
        .withColumn("tx_hour", hour("tx_timestamp"))
        .withColumn("tx_day_of_week", dayofweek("tx_timestamp"))
        .withColumn("is_weekend", when(col("tx_day_of_week").isin(1, 7), 1).otherwise(0))
        .withColumn("is_night", when((col("tx_hour") >= 22) | (col("tx_hour") <= 6), 1).otherwise(0))
        .withColumn("is_business_hours", when((col("tx_hour") >= 9) & (col("tx_hour") <= 17), 1).otherwise(0))
        .withColumn("tx_amount_log", when(col("tx_amount") > 0, log(col("tx_amount"))).otherwise(0))
        .withColumn("amount_category",
            when(col("tx_amount") <= 10, 0)      # small
            .when(col("tx_amount") <= 100, 1)    # medium
            .when(col("tx_amount") <= 1000, 2)   # large
            .otherwise(3))                       # xlarge
    )
    
    print("  ✅ Created efficient temporal and categorical features")
    return df_features

# ────────────────────────────────────────────────────────────────────
# PIPELINE EXECUTION
# ────────────────────────────────────────────────────────────────────

print(f"\n{'='*60}")
print("🚀 STARTING ML DATA PIPELINE")
print(f"{'='*60}")

# Data cleaning
clean_df = clean_for_ml_efficient(df_raw)
clean_df.cache()

# Analyze cleaned data
analyze_data_quality_efficient(clean_df, "Cleaned Data")

# Feature engineering
ml_df = create_ml_features_efficient(clean_df)

# Final preparation
ml_ready_df = (ml_df
    .select([
        "transaction_id", "customer_id", "terminal_id",
        "tx_amount", "tx_amount_log", "amount_category",
        "tx_hour", "tx_day_of_week",
        "is_weekend", "is_night", "is_business_hours",
        "tx_time_days", "tx_time_seconds",
        "tx_fraud",  # TARGET
        "tx_fraud_scenario"
    ])
    .filter(col("tx_amount_log").isNotNull())
)

final_count = ml_ready_df.count()
print(f"\n🎯 ML-READY DATASET: {final_count:,} rows")

# ────────────────────────────────────────────────────────────────────
# CLASS DISTRIBUTION ANALYSIS
# ────────────────────────────────────────────────────────────────────
print("\n📈 CLASS DISTRIBUTION")
fraud_dist = ml_ready_df.groupBy("tx_fraud").count().collect()
for row in fraud_dist:
    fraud_class, count = row["tx_fraud"], row["count"]
    pct = (count / final_count) * 100
    print(f"  Class {fraud_class}: {count:,} ({pct:.2f}%)")

# ────────────────────────────────────────────────────────────────────
# MEMORY-EFFICIENT SAVING
# ────────────────────────────────────────────────────────────────────
print("\n💾 Saving with cluster optimization...")

# Calculate optimal partitions for your cluster
partitions_calc = final_count // 1000000 if final_count > 1000000 else 50
optimal_partitions = partitions_calc if partitions_calc < 200 else 200
optimal_partitions = optimal_partitions if optimal_partitions > 50 else 50

(ml_ready_df
    .coalesce(optimal_partitions)
    .write
    .mode("overwrite")
    .option("compression", "snappy")
    .option("maxRecordsPerFile", 1000000)
    .partitionBy("tx_fraud")
    .parquet(PARQUET_OUTPUT_DIR)
)

print(f"✅ Data saved to: {PARQUET_OUTPUT_DIR}")

# ────────────────────────────────────────────────────────────────────
# FINAL STATISTICS
# ────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("🎉 ML PIPELINE COMPLETED SUCCESSFULLY")
print("="*60)
print(f"📥 Input:  {df_raw.count():,} rows")
print(f"📤 Output: {final_count:,} rows")
print(f"💾 Retention: {(final_count/df_raw.count())*100:.1f}%")
print(f"🗂️  Location: {PARQUET_OUTPUT_DIR}")
print(f"⚡ Partitions: {optimal_partitions}")

print("\n🤖 OPTIMIZATION FEATURES:")
print("  • Auto-detected HDFS configuration")
print("  • Memory-efficient data processing")
print("  • Adaptive query execution enabled")
print("  • Optimized for distributed ML training")
print("  • Parquet format with Snappy compression")

# Resource cleanup
clean_df.unpersist()
spark.catalog.clearCache()

print(f"\n🚀 Ready for ML model training!")