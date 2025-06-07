terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
}

provider "yandex" {
  service_account_key_file = var.service_account_key_file
  cloud_id                 = var.cloud_id
  folder_id               = var.folder_id
  zone                    = var.zone
}

resource "yandex_vpc_security_group" "dataproc_security_group" {
  name       = "dataproc-security-group"
  folder_id  = var.folder_id
  network_id = var.network_id

  ingress {
    protocol       = "TCP"
    description    = "Allow SSH connections"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 22
  }

  ingress {
    protocol       = "TCP"
    description    = "Allow HTTPS connections"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 443
  }

  ingress {
    protocol       = "ANY"
    description    = "Allow all cluster internal traffic"
    predefined_target = "self_security_group"
    from_port      = 0
    to_port        = 65535
  }

  egress {
    protocol       = "ANY"
    description    = "Allow all cluster internal traffic"
    predefined_target = "self_security_group"
    from_port      = 0
    to_port        = 65535
  }

  egress {
    protocol       = "UDP"
    description    = "Allow NTP connections"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 123
  }

  egress {
    protocol       = "ANY"
    description    = "Allow outgoing connections to specific Yandex Cloud services"
    v4_cidr_blocks = [
      "84.201.181.26/32",    # Data Processing status and jobs
      "158.160.59.216/32",   # Monitoring and autoscaling
      "213.180.193.243/32",  # Object Storage
      "84.201.181.184/32"    # Cloud Logging
    ]
    from_port      = 0
    to_port        = 65535
  }
}

resource "yandex_vpc_gateway" "nat_gateway" {
  name = "nat-gateway"
  shared_egress_gateway {}
}

resource "yandex_vpc_route_table" "nat_route_table" {
  name       = "nat-route-table"
  network_id = var.network_id

  static_route {
    destination_prefix = "0.0.0.0/0"
    gateway_id        = yandex_vpc_gateway.nat_gateway.id
  }
}

resource "yandex_vpc_subnet" "dataproc_subnet" {
  name           = "dataproc-subnet"
  network_id     = var.network_id
  v4_cidr_blocks = ["10.131.0.0/24"]  # Changed to avoid overlap with existing subnets
  zone           = var.zone
  route_table_id = yandex_vpc_route_table.nat_route_table.id
}

resource "yandex_dataproc_cluster" "spark_cluster" {
  name                = var.cluster_name
  description         = "Spark cluster for data processing"
  folder_id          = var.folder_id
  service_account_id = var.service_account_id
  security_group_ids = [yandex_vpc_security_group.dataproc_security_group.id]

  cluster_config {
    version_id = "2.0"

    hadoop {
      ssh_public_keys = [
        file(var.public_key_path)
      ]
    }

    subcluster_spec {
      name = "master"
      role = "MASTERNODE"
      resources {
        resource_preset_id = "s3-c2-m8"
        disk_type_id      = "network-ssd"
        disk_size         = 40
      }
      subnet_id   = yandex_vpc_subnet.dataproc_subnet.id  # Updated to use the new subnet
      hosts_count = 1
      assign_public_ip = true
    }

    subcluster_spec {
      name = "data"
      role = "DATANODE"
      resources {
        resource_preset_id = "s3-c4-m16"
        disk_type_id      = "network-ssd"
        disk_size         = 128
      }
      subnet_id   = yandex_vpc_subnet.dataproc_subnet.id
      hosts_count = 3
      assign_public_ip = true
    }

  }
}