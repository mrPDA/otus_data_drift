# 🚀 Yandex Cloud DataProc ML Pipeline

**Automated infrastructure and ML data processing pipeline for large-scale fraud detection on Yandex Cloud DataProc clusters**

[![Terraform](https://img.shields.io/badge/Terraform-v1.0+-623CE4?logo=terraform)](https://terraform.io)
[![Spark](https://img.shields.io/badge/Apache_Spark-3.0+-E25A1C?logo=apache-spark)](https://spark.apache.org)
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python)](https://python.org)
[![Yandex Cloud](https://img.shields.io/badge/Yandex_Cloud-DataProc-FF0000)](https://cloud.yandex.com)

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Quick Start](#-quick-start)
- [Infrastructure](#-infrastructure)
- [Data Pipeline](#-data-pipeline)
- [Jupyter Notebooks](#-jupyter-notebooks)
- [Configuration](#-configuration)
- [Usage Examples](#-usage-examples)
- [Contributing](#-contributing)

## 🎯 Overview

This project provides a complete infrastructure-as-code solution for deploying and managing Apache Spark clusters on Yandex Cloud DataProc for large-scale ML data processing. It includes automated cluster deployment, SSH tunneling, Jupyter Notebook integration, and optimized data pipelines for fraud detection datasets.

### Key Statistics
- **Processed Dataset**: 1.5+ billion rows (120+ GB)
- **Processing Performance**: Optimized for 64GB cluster memory
- **Data Retention**: 94%+ after cleaning and feature engineering
- **Class Distribution**: Handles imbalanced datasets (5.76% fraud cases)

## ✨ Features

### 🏗️ Infrastructure Automation
- **One-command cluster deployment** with Terraform
- **Auto-configured networking** with NAT Gateway and Security Groups
- **Resource optimization** for cost-effective ML workloads
- **Automatic cleanup** and cluster management

### 🔧 Development Tools
- **SSH tunnel management** for secure access
- **Jupyter Notebook** with pre-installed ML libraries
- **Real-time monitoring** and logging
- **Interactive data exploration** capabilities

### 📊 ML Data Pipeline
- **Memory-efficient processing** for large datasets
- **Automated data quality analysis** with sampling
- **Feature engineering** for fraud detection
- **Parquet optimization** with Snappy compression

### 🔒 Security & Performance
- **S3A integration** with Yandex Object Storage
- **HDFS auto-configuration** for distributed storage
- **Adaptive query execution** for optimal performance
- **Resource monitoring** and optimization

## 🚀 Quick Start

### Prerequisites
- Yandex Cloud account with DataProc access
- Terraform installed
- `yc` CLI configured with credentials
- SSH key pair generated

### 1. Clone and Configure
```bash
git clone <repository-url>
cd otus_data_drift

# Copy and edit configuration
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your credentials
```

### 2. Deploy Infrastructure
```bash
# Collect existing resource IDs
./collect_cluster_info.sh

# Deploy cluster (10-15 minutes)
./quick_deploy.sh
```

### 3. Access Jupyter
```bash
# Create SSH tunnel
./tunnel_helper.sh jupyter

# Open Jupyter in browser
open http://localhost:8888
```

### 4. Run Data Pipeline
```python
# In Jupyter notebook, run the ML pipeline
exec(open('/home/ubuntu/ml_pipeline.py').read())
```

## 🏗️ Infrastructure

### Cluster Configuration
- **Master Node**: s3-c2-m8 (4 vCPU, 16GB RAM, 40GB SSD)
- **Compute Nodes**: 2× s3-c4-m16 (8 vCPU, 32GB RAM, 128GB SSD)
- **Data Node**: s3-c2-m8 (4 vCPU, 16GB RAM, 100GB SSD)
- **Total Resources**: 20 vCPU, 96GB RAM, 396GB SSD

### Network Architecture
```
Internet → NAT Gateway → Private Subnet → DataProc Cluster
                ↓
         Security Groups (SSH, HTTPS, Jupyter)
                ↓
      S3 Object Storage (Data & Results)
```

### File Structure
```
otus_data_drift/
├── 🏗️ Infrastructure
│   ├── main.tf                 # Terraform configuration
│   ├── variables.tf            # Variable definitions
│   └── terraform.tfvars        # Your configuration
├── 🚀 Deployment Scripts
│   ├── quick_deploy.sh         # One-command deployment
│   ├── collect_cluster_info.sh # Resource discovery
│   └── start_jupyter.sh        # Jupyter setup
├── 🔧 Development Tools
│   ├── tunnel_helper.sh        # SSH tunnel management
│   └── create_tunnel.sh        # Tunnel creation
├── 📊 Data Processing
│   ├── ml_correction_public.py # ML pipeline template
│   └── ml_report_public.py     # Analysis and reporting
└── 📚 Documentation
    └── JUPYTER_TUNNEL_STATUS.md # SSH tunnel status
```

## 📊 Data Pipeline

### Supported Data Formats
- **CSV/TXT**: Transaction logs, time series data
- **Parquet**: Optimized columnar storage
- **JSON**: Semi-structured data processing

### Pipeline Stages

#### 1. Data Quality Analysis
```python
# Efficient sampling for large datasets
analyze_data_quality_efficient(df, sample_size=1000000)

# NULL/NA analysis with statistics
# Outlier detection with percentile-based filtering
```

#### 2. Data Cleaning
```python
# Multi-stage validation
step1_df = df.filter(basic_validation_rules)
step2_df = remove_statistical_outliers(step1_df)
step3_df = step2_df.dropDuplicates(["transaction_id"])
step4_df = validate_fraud_logic(step3_df)
```

#### 3. Feature Engineering
```python
# Temporal features
.withColumn("tx_hour", hour("tx_timestamp"))
.withColumn("is_weekend", weekend_logic)
.withColumn("is_business_hours", business_hours_logic)

# Amount categorization
.withColumn("amount_category", amount_binning)
.withColumn("tx_amount_log", log_transformation)
```

#### 4. Optimized Storage
```python
# Partition by target variable for ML
.partitionBy("tx_fraud")
.option("compression", "snappy")
.option("maxRecordsPerFile", 1000000)
.parquet(output_path)
```

### Performance Metrics
- **Input Processing**: 1.9B+ rows
- **Memory Efficiency**: Adaptive partitioning (50-200 partitions)
- **Compression Ratio**: ~70% reduction with Snappy
- **Processing Time**: ~2-3 hours for full dataset

## 📓 Jupyter Notebooks

### Pre-installed Libraries
```python
# Data Processing
pandas, numpy, pyarrow

# Machine Learning  
scikit-learn, scipy

# Visualization
matplotlib, seaborn, plotly

# Big Data
pyspark, hadoop-client
```

### Example Notebooks
- **Data Exploration**: Interactive dataset analysis
- **Pipeline Testing**: Step-by-step processing verification
- **Model Training**: Distributed ML with MLlib
- **Visualization**: Statistical plots and distributions

### Access Methods
```bash
# Local tunnel (recommended)
./tunnel_helper.sh jupyter
open http://localhost:8888

# Direct access (less secure)
open http://YOUR_CLUSTER_IP:8888
```

## ⚙️ Configuration

### Required Variables (`terraform.tfvars`)
```hcl
# Yandex Cloud
cloud_id           = "your-cloud-id"
folder_id          = "your-folder-id"
service_account_id = "your-service-account-id"

# Networking
network_id    = "your-network-id"
subnet_id     = "your-subnet-id"  # Optional
security_group_id = "your-security-group-id"  # Optional

# SSH Access
public_key_path = "~/.ssh/id_rsa.pub"

# Cluster
cluster_name = "your-cluster-name"
zone         = "ru-central1-a"
```

### S3 Configuration
```python
# Update in ml_correction_public.py
S3A_ACCESS_KEY = "your-access-key"
S3A_SECRET_KEY = "your-secret-key"
S3A_ENDPOINT = "storage.yandexcloud.net"
```

## 💡 Usage Examples

### 1. Row Counting Analysis
```python
# Count rows in S3 bucket
python ml_report_public.py

# Results:
# ✅ Total rows: 1,563,638,244
# 📁 Files processed: 1
# 🎯 Fraud detection dataset ready
```

### 2. Tunnel Management
```bash
# Check tunnel status
./tunnel_helper.sh status

# Create Jupyter tunnel
./tunnel_helper.sh jupyter

# Stop all tunnels
./tunnel_helper.sh stop
```

### 3. Custom Data Processing
```python
# Initialize Spark with auto-configuration
spark = create_optimized_spark_session()

# Read your data
df = spark.read.csv("s3a://your-bucket/data.csv")

# Apply ML pipeline
ml_ready_df = create_ml_features_efficient(df)

# Save results
ml_ready_df.write.parquet("s3a://your-bucket/results/")
```

### 4. Cluster Management
```bash
# Deploy new cluster
./quick_deploy.sh

# Check cluster status
yc dataproc cluster get your-cluster-id

# Destroy cluster (save costs)
terraform destroy
```

## 🛠️ Advanced Features

### Auto-Detection Capabilities
- **HDFS Namenode**: Automatic discovery from cluster configuration
- **Resource Optimization**: Dynamic partition calculation
- **Network Configuration**: Auto-generated security groups
- **Environment Setup**: Platform-specific PySpark configuration

### Monitoring & Debugging
```bash
# Check Spark UI
open http://localhost:4040

# View YARN Resource Manager  
open http://localhost:8088

# Monitor HDFS
open http://localhost:9870

# Application logs
ssh ubuntu@cluster-ip "tail -f /var/log/hadoop-yarn/..."
```

### Memory Optimization
- **Adaptive Query Execution**: Automatic partition coalescing
- **Memory-Efficient Sampling**: Statistical analysis on subsets
- **Garbage Collection**: Automatic cache management
- **Resource Allocation**: Dynamic executor scaling

## 🚨 Important Notes

### Cost Management
- **Remember to destroy clusters** after use: `terraform destroy`
- Monitor resource usage in Yandex Cloud Console
- Use `quick_deploy.sh` for rapid development cycles

### Security
- SSH keys are required for cluster access
- Security groups allow specific ports only
- S3 credentials should be kept secure
- Use private subnets for production deployments

### Performance Tips
- Increase cluster size for larger datasets (>500GB)
- Use Parquet format for better compression
- Enable S3A fast upload for large writes
- Monitor memory usage during processing

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open Pull Request**

### Development Setup
```bash
# Install development dependencies
pip install terraform-compliance pytest

# Run tests
pytest tests/

# Validate Terraform
terraform plan -detailed-exitcode
```

### Code Standards
- Follow PEP 8 for Python code
- Use descriptive variable names
- Add comments for complex logic
- Include error handling
- Document configuration options

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

- **Issues**: Report bugs and feature requests via GitHub Issues
- **Documentation**: Check the `archive/` folder for detailed guides
- **Community**: Join discussions in GitHub Discussions

## 🙏 Acknowledgments

- **Yandex Cloud** for DataProc platform
- **Apache Spark** community for optimization guides
- **Terraform** for infrastructure automation
- **OTUS** for educational support

---

**⭐ Star this repository if it helped you build ML pipelines on Yandex Cloud!**

*Last updated: June 13, 2025*
