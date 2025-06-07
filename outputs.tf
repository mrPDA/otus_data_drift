output "cluster_id" {
  description = "ID of the created cluster"
  value       = yandex_dataproc_cluster.spark_cluster.id
}

output "cluster_master_host" {
  description = "Hostname of the master node"
  value       = yandex_dataproc_cluster.spark_cluster.cluster_config[0].subcluster_spec[0].name
}