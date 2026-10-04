variable "aws_region" {
  description = "AWS region for the server"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance size"
  type        = string
  default     = "t3.micro"
}

variable "image" {
  description = "Image to run, pinned by digest (registry/name@sha256:...)"
  type        = string

  # a tag can move, a digest cannot
  validation {
    condition     = can(regex("@sha256:[0-9a-f]{64}$", var.image))
    error_message = "image must be pinned by digest (name@sha256:<64 hex>)."
  }
}

variable "registry_host" {
  description = "Container registry host"
  type        = string
  default     = "registry.gitlab.com"
}

variable "registry_user" {
  description = "Deploy token username (read_registry only)"
  type        = string
}

# set with the env var TF_VAR_registry_token, never in a file
variable "registry_token" {
  description = "Deploy token password (read_registry only)"
  type        = string
  sensitive   = true
}

variable "my_ip_cidr" {
  description = "Allowed client address, a single IP in /32 form (e.g. 203.0.113.25/32)"
  type        = string

  # never allow the whole internet
  validation {
    condition     = var.my_ip_cidr != "0.0.0.0/0" && endswith(var.my_ip_cidr, "/32")
    error_message = "my_ip_cidr must be a single address ending in /32, not 0.0.0.0/0."
  }
}
