.PHONY: help init plan apply destroy clean fmt validate

# Default target
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

init: ## Initialize Terraform
	terraform init

fmt: ## Format Terraform files
	terraform fmt -recursive

validate: ## Validate Terraform configuration
	terraform validate

plan: ## Create Terraform plan
	terraform plan

apply: ## Apply Terraform configuration
	terraform apply

destroy: ## Destroy Terraform infrastructure
	terraform destroy

clean: ## Clean Terraform files
	rm -rf .terraform
	rm -f .terraform.lock.hcl
	rm -f terraform.tfstate*

setup: ## Setup environment (copy example files)
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env file. Please edit it with your values."; fi
	@if [ ! -f terraform.tfvars ]; then cp terraform.tfvars.example terraform.tfvars; echo "Created terraform.tfvars file. Please edit it with your values."; fi

check-env: ## Check if required environment variables are set
	@echo "Checking environment variables..."
	@if [ -z "$$TF_VAR_cloud_id" ]; then echo "❌ TF_VAR_cloud_id is not set"; exit 1; fi
	@if [ -z "$$TF_VAR_folder_id" ]; then echo "❌ TF_VAR_folder_id is not set"; exit 1; fi
	@if [ -z "$$TF_VAR_service_account_id" ]; then echo "❌ TF_VAR_service_account_id is not set"; exit 1; fi
	@echo "✅ All required environment variables are set"

deploy: check-env init plan apply ## Full deployment process

ssh-master: ## SSH to master node (requires cluster to be deployed)
	@echo "Getting master node IP..."
	@terraform output -raw cluster_id || echo "Cluster not deployed yet"
