# Which Terraform and which AWS plugin (provider) this blueprint needs.
terraform {
  # Refuse to run with a Terraform older than 1.9.
  required_version = ">= 1.9"

  required_providers {
    aws = {
      # The official AWS plugin, downloaded from the HashiCorp registry.
      source = "hashicorp/aws"
      # Any 6.x version, never a new major version by surprise.
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  # Learner Lab works in us-east-1.
  region = var.aws_region
}
