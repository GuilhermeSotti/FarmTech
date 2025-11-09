cd infra/terraform
terraform init
terraform apply -auto-approve -var="aws_region=us-east-1"
