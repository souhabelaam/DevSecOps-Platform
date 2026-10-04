# The settings of the blueprint. Values are given in terraform.tfvars.

variable "aws_region" {
  description = "AWS region where the server is created"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "Size of the server (small and cheap)"
  type        = string
  default     = "t3.micro"
}

variable "my_ip_cidr" {
  description = "Your public IP followed by /32 (one single address), e.g. 203.0.113.25/32"
  type        = string

  # Safety net: Terraform itself refuses 'the whole internet'.
  validation {
    condition     = var.my_ip_cidr != "0.0.0.0/0" && endswith(var.my_ip_cidr, "/32")
    error_message = "my_ip_cidr must be one single address ending in /32, never 0.0.0.0/0."
  }
}
