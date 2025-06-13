# S3 Bucket Row Counter and Data Analysis Tool
# Optimized for Yandex Cloud DataProc clusters
# GitHub Public Version - Anonymized

import os
import sys
from pathlib import Path
from datetime import datetime
import json

# ────────────────────────────────────────────────────────────────────
# CONFIGURATION - UPDATE THESE FOR YOUR ENVIRONMENT
# ────────────────────────────────────────────────────────────────────

# S3 Configuration - REPLACE WITH YOUR CREDENTIALS
S3A_ACCESS_KEY = "YOUR_ACCESS_KEY_HERE"
S3A_SECRET_KEY = "YOUR_SECRET_KEY_HERE"
S3A_ENDPOINT = "storage.yandexcloud.net"  # Or your S3 endpoint

# Target bucket path - UPDATE WITH YOUR BUCKET
TARGET_BUCKET = "s3a://your-bucket-name/your-data-path/"

# Report output directory (adjust for your environment)
REPORT_OUTPUT_DIR = "/home/ubuntu"  # Default for YC DataProc

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

# Setup environment before importing PySpark
is_on_cluster = setup_dataproc_environment()

# Import PySpark after environment setup
try:
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import count
    print("✅ PySpark modules imported successfully")
except ImportError as e:
    print(f"❌ PySpark import error: {e}")
    print("💡 Try running: spark-submit your_script.py")
    sys.exit(1)

# ────────────────────────────────────────────────────────────────────
# HDFS AUTO-DETECTION
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
# SPARK SESSION CREATION
# ────────────────────────────────────────────────────────────────────

def create_spark_session_for_analysis():
    """Create optimized Spark session for data analysis"""
    
    # Close existing session if it exists
    active = SparkSession.getActiveSession()
    if active and active.sparkContext.master.startswith("local"):
        print(f"🛑 Stopping local session ({active.sparkContext.master})")
        active.stop()
        active = None
    
    if not active:
        builder = SparkSession.builder.appName("S3BucketAnalyzer")
        
        if is_on_cluster:
            # Auto-detect HDFS namenode
            hdfs_namenode = get_hdfs_namenode()
            
            # Cluster configuration
            spark_session = (builder
                .master("yarn")
                .config("spark.submit.deployMode", "client")
                
                # HDFS configuration (automatically detected)
                .config("spark.hadoop.fs.defaultFS", hdfs_namenode)
                .config("spark.hadoop.fs.default.name", hdfs_namenode)
                
                # Lightweight resources for analysis
                .config("spark.executor.instances", "2")
                .config("spark.executor.memory", "8g")
                .config("spark.executor.cores", "2")
                .config("spark.driver.memory", "2g")
                .config("spark.driver.cores", "1")
                
                # S3A settings - UPDATE WITH YOUR CREDENTIALS
                .config("spark.hadoop.fs.s3a.endpoint", S3A_ENDPOINT)
                .config("spark.hadoop.fs.s3a.access.key", S3A_ACCESS_KEY)
                .config("spark.hadoop.fs.s3a.secret.key", S3A_SECRET_KEY)
                .config("spark.hadoop.fs.s3a.path.style.access", "true")
                .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "true")
                .config("spark.hadoop.fs.s3a.multipart.size", "67108864")
                .config("spark.hadoop.fs.s3a.fast.upload", "true")
                
                # YARN staging (automatically determined)
                .config("spark.yarn.stagingDir", f"{hdfs_namenode}/user/ubuntu/spark-staging")
                
                # Optimizations for reading
                .config("spark.sql.shuffle.partitions", "100")
                .config("spark.sql.adaptive.enabled", "true")
                .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
                
                .getOrCreate()
            )
        else:
            # Local configuration for testing
            spark_session = (builder
                .master("local[*]")
                .config("spark.driver.memory", "4g")
                .config("spark.sql.shuffle.partitions", "4")
                .getOrCreate()
            )
        
        return spark_session
    else:
        return active

# ────────────────────────────────────────────────────────────────────
# OPTIMIZED PARQUET ANALYSIS
# ────────────────────────────────────────────────────────────────────

def count_parquet_rows_optimized(spark, parquet_path):
    """
    Optimized row counting for Parquet files
    Uses Parquet metadata for fast counting
    """
    print(f"\n🚀 OPTIMIZED PARQUET ANALYSIS: {parquet_path}")
    
    report_data = {
        'path': parquet_path,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'schema': None,
        'partitions': 0,
        'total_rows': 0,
        'fraud_distribution': {},
        'columns': [],
        'errors': []
    }
    
    try:
        # Read Parquet as partitioned dataset
        df = spark.read.parquet(parquet_path)
        
        # Collect schema information for report
        schema_info = []
        for field in df.schema.fields:
            schema_info.append({
                'name': field.name,
                'type': str(field.dataType),
                'nullable': field.nullable
            })
        
        report_data['schema'] = schema_info
        report_data['columns'] = df.columns
        
        print("📋 Data schema:")
        df.printSchema()
        
        # Check partitions
        if hasattr(df, 'rdd') and hasattr(df.rdd, 'getNumPartitions'):
            partitions = df.rdd.getNumPartitions()
            report_data['partitions'] = partitions
            print(f"📦 Number of partitions: {partitions}")
        
        # Count rows
        print("⏳ Counting rows...")
        total_rows = df.count()
        report_data['total_rows'] = total_rows
        
        # If tx_fraud column exists (from ML pipeline), show distribution
        if 'tx_fraud' in df.columns:
            print("\n📊 Class distribution (tx_fraud):")
            fraud_dist = df.groupBy("tx_fraud").count().collect()
            fraud_distribution = {}
            for row in fraud_dist:
                fraud_class, count = row["tx_fraud"], row["count"]
                pct = (count / total_rows) * 100
                fraud_distribution[f"class_{fraud_class}"] = {
                    'count': count,
                    'percentage': round(pct, 2)
                }
                print(f"  Class {fraud_class}: {count:,} ({pct:.2f}%)")
            
            report_data['fraud_distribution'] = fraud_distribution
        
        # Additional statistics for numeric columns
        numeric_stats = {}
        numeric_columns = [f.name for f in df.schema.fields if str(f.dataType) in ['IntegerType', 'LongType', 'DoubleType', 'FloatType', 'DecimalType(10,2)']]
        
        if numeric_columns:
            print(f"\n📈 Statistics for numeric columns:")
            for col_name in numeric_columns[:5]:  # Limit for performance
                try:
                    stats = df.select(col_name).describe().collect()
                    col_stats = {}
                    for stat_row in stats:
                        col_stats[stat_row['summary']] = stat_row[col_name]
                    numeric_stats[col_name] = col_stats
                    print(f"  {col_name}: min={col_stats.get('min', 'N/A')}, max={col_stats.get('max', 'N/A')}, mean={col_stats.get('mean', 'N/A')}")
                except Exception as e:
                    print(f"  {col_name}: error getting statistics - {str(e)[:50]}")
        
        report_data['numeric_statistics'] = numeric_stats
        
        return total_rows, report_data
        
    except Exception as e:
        error_msg = f"❌ Error reading Parquet: {str(e)}"
        print(error_msg)
        report_data['errors'].append(error_msg)
        return 0, report_data

# ────────────────────────────────────────────────────────────────────
# REPORT GENERATION
# ────────────────────────────────────────────────────────────────────

def generate_report(result_data, target_bucket, output_dir=REPORT_OUTPUT_DIR):
    """
    Generate detailed report and save to specified directory
    """
    timestamp = datetime.now()
    
    # Create file names
    json_filename = f"s3_bucket_analysis_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
    txt_filename = f"s3_bucket_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.txt"
    
    json_path = os.path.join(output_dir, json_filename)
    txt_path = os.path.join(output_dir, txt_filename)
    
    # Prepare report content
    report_content = f"""
{'='*80}
📊 S3 BUCKET ANALYSIS REPORT
{'='*80}

📅 Analysis date and time: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
🎯 Analyzed path: {target_bucket}
🖥️  Environment: Yandex Cloud DataProc

{'='*80}
📈 GENERAL RESULTS
{'='*80}

"""
    
    if result_data.get('total_rows', 0) > 0:
        report_content += f"✅ Total number of rows: {result_data['total_rows']:,}\n"
        report_content += f"📁 Files/datasets processed: {result_data['files_processed']}\n\n"
        
        # File details
        report_content += "📋 DATASET BREAKDOWN:\n"
        report_content += "-" * 50 + "\n"
        
        for stat in result_data.get('file_stats', []):
            report_content += f"• Type: {stat['type']}\n"
            report_content += f"  Path: {stat['pattern']}\n"
            report_content += f"  Rows: {stat['rows']:,}\n\n"
        
        # Detailed data structure information (if available)
        if 'detailed_info' in result_data and result_data['detailed_info']:
            detailed = result_data['detailed_info']
            
            report_content += f"{'='*80}\n"
            report_content += f"🔍 DETAILED DATA INFORMATION\n"
            report_content += f"{'='*80}\n\n"
            
            if detailed.get('schema'):
                report_content += "📋 DATA SCHEMA:\n"
                report_content += "-" * 30 + "\n"
                for field in detailed['schema']:
                    nullable = "NULL" if field['nullable'] else "NOT NULL"
                    report_content += f"• {field['name']}: {field['type']} ({nullable})\n"
                report_content += "\n"
            
            if detailed.get('partitions', 0) > 0:
                report_content += f"📦 Number of partitions: {detailed['partitions']}\n\n"
            
            # Fraud class distribution
            if detailed.get('fraud_distribution'):
                report_content += "📊 CLASS DISTRIBUTION (FRAUD DETECTION):\n"
                report_content += "-" * 40 + "\n"
                for class_name, class_data in detailed['fraud_distribution'].items():
                    report_content += f"• {class_name}: {class_data['count']:,} ({class_data['percentage']}%)\n"
                report_content += "\n"
            
            # Numeric column statistics
            if detailed.get('numeric_statistics'):
                report_content += "📈 NUMERIC COLUMN STATISTICS:\n"
                report_content += "-" * 35 + "\n"
                for col_name, stats in detailed['numeric_statistics'].items():
                    report_content += f"• {col_name}:\n"
                    for stat_name, stat_value in stats.items():
                        if stat_name != 'summary':
                            report_content += f"  └─ {stat_name}: {stat_value}\n"
                    report_content += "\n"
    else:
        report_content += "❌ No data found or inaccessible\n"
        if 'error' in result_data:
            report_content += f"   Error: {result_data['error']}\n"
    
    report_content += f"\n{'='*80}\n"
    report_content += f"🏁 ANALYSIS COMPLETE\n"
    report_content += f"{'='*80}\n"
    report_content += f"📄 Report saved: {txt_filename}\n"
    report_content += f"📋 JSON data: {json_filename}\n"
    report_content += f"📂 Directory: {output_dir}\n"
    
    try:
        # Save text report
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        # Save JSON with detailed data
        json_data = {
            'analysis_info': {
                'timestamp': timestamp.isoformat(),
                'target_bucket': target_bucket,
                'environment': 'Yandex Cloud DataProc'
            },
            'results': result_data
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 REPORTS CREATED:")
        print(f"  📝 Text report: {txt_path}")  
        print(f"  📋 JSON data: {json_path}")
        
        return {
            'txt_report': txt_path,
            'json_report': json_path,
            'success': True
        }
        
    except Exception as e:
        error_msg = f"❌ Error creating report: {str(e)}"
        print(error_msg)
        return {
            'error': error_msg,
            'success': False
        }

# ────────────────────────────────────────────────────────────────────
# MAIN ROW COUNTING FUNCTION
# ────────────────────────────────────────────────────────────────────

def count_rows_in_bucket(spark, bucket_path):
    """
    Count total number of rows in all files in the bucket
    
    Args:
        spark: SparkSession
        bucket_path: path to bucket (s3a://bucket-name/)
    
    Returns:
        dict: file statistics and total row count
    """
    
    print(f"\n📊 Counting rows in bucket: {bucket_path}")
    print("="*60)
    
    try:
        # Special handling for Parquet files from ML pipeline
        if 'ml_ready_data' in bucket_path.lower() or bucket_path.endswith('.parquet'):
            print("🎯 Detected ML dataset - using optimized counting")
            total_rows, detailed_info = count_parquet_rows_optimized(spark, bucket_path)
            
            if total_rows > 0:
                return {
                    'total_rows': total_rows,
                    'files_processed': 1,
                    'file_stats': [{'pattern': bucket_path, 'type': 'ML_PARQUET', 'rows': total_rows}],
                    'detailed_info': detailed_info
                }
        
        # Try to find Parquet files (priority) and other formats
        file_patterns = [
            f"{bucket_path}*.parquet",     # Direct parquet files
            f"{bucket_path}**/*.parquet",  # Parquet in subfolders  
            f"{bucket_path}*/*.parquet",   # Parquet in partitions
            f"{bucket_path}",              # Entire path as Parquet dataset
            f"{bucket_path}*.txt",         # Text files
            f"{bucket_path}*.csv"          # CSV files
        ]
        
        total_rows = 0
        files_processed = 0
        file_stats = []
        
        for pattern in file_patterns:
            try:
                print(f"🔍 Checking pattern: {pattern}")
                
                # Determine file format by extension
                if pattern.endswith('.parquet') or '*.parquet' in pattern or pattern == bucket_path.rstrip('/'):
                    # For Parquet files - read as partitioned dataset
                    df = spark.read.parquet(pattern)
                    file_type = "PARQUET"
                elif pattern.endswith('.txt') or '*.txt' in pattern:
                    df = spark.read.option("header", "true").csv(pattern)
                    file_type = "TXT/CSV"
                else:
                    df = spark.read.option("header", "true").csv(pattern)
                    file_type = "CSV"
                
                # Count rows
                row_count = df.count()
                
                if row_count > 0:
                    total_rows += row_count
                    files_processed += 1
                    
                    file_stats.append({
                        'pattern': pattern,
                        'type': file_type,
                        'rows': row_count
                    })
                    
                    print(f"  ✅ {file_type}: {row_count:,} rows")
                
            except Exception as e:
                # Not all patterns may exist - this is normal
                if "Path does not exist" not in str(e) and "No such file" not in str(e):
                    print(f"  ⚠️ Warning for {pattern}: {str(e)[:100]}...")
                continue
        
        # Display final statistics
        print("\n" + "="*60)
        print("📈 FINAL STATISTICS")
        print("="*60)
        
        if files_processed > 0:
            print(f"📁 Files/patterns processed: {files_processed}")
            print(f"📊 Total number of rows: {total_rows:,}")
            
            print(f"\n📋 Breakdown by file type:")
            for stat in file_stats:
                print(f"  • {stat['type']}: {stat['rows']:,} rows")
                print(f"    └─ {stat['pattern']}")
        else:
            print("❌ No files found or accessible in specified bucket")
            print(f"   Check path: {bucket_path}")
            print("   Ensure bucket contains .txt, .csv or .parquet files")
        
        return {
            'total_rows': total_rows,
            'files_processed': files_processed,
            'file_stats': file_stats
        }
        
    except Exception as e:
        print(f"❌ Error counting rows: {str(e)}")
        return {
            'total_rows': 0,
            'files_processed': 0,
            'file_stats': [],
            'error': str(e)
        }

# ────────────────────────────────────────────────────────────────────
# MAIN EXECUTION
# ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    
    print("🚀 STARTING S3 BUCKET ROW COUNT ANALYSIS")
    print("="*60)
    print(f"🎯 Target bucket: {TARGET_BUCKET}")
    
    # Create Spark session
    spark = create_spark_session_for_analysis()
    print(f"✅ Spark session created: {spark.sparkContext.master}")
    
    try:
        # Perform analysis
        result = count_rows_in_bucket(spark, TARGET_BUCKET)
        
        # Generate report
        print(f"\n📋 Creating report...")
        report_result = generate_report(result, TARGET_BUCKET)
        
        # Final output
        if result['total_rows'] > 0:
            print(f"\n🎉 RESULT: {result['total_rows']:,} rows in bucket")
        else:
            print(f"\n⚠️ RESULT: No rows found")
            if 'error' in result:
                print(f"   Error: {result['error']}")
        
        if report_result.get('success'):
            print(f"\n✅ Reports successfully created in directory: {REPORT_OUTPUT_DIR}")
        else:
            print(f"\n❌ Report creation error: {report_result.get('error', 'Unknown error')}")
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
    
    finally:
        # Close Spark session
        print(f"\n🛑 Closing Spark session...")
        spark.stop()
        print("✅ Done!")