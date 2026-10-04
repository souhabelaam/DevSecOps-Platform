# Latest Amazon Linux 2023 image, looked up instead of hard-coding an ID.
data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
}

# The firewall: who may talk to the server.
resource "aws_security_group" "app" {
  name        = "task-tracker-sg"
  description = "Task Tracker: app port from my IP only"

  # Incoming: only YOUR address, only the app port.
  ingress {
    description = "Task Tracker app from my IP only"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = [var.my_ip_cidr]
  }

  # Outgoing: only HTTPS (to download updates / pull the image).
  egress {
    description = "HTTPS out"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# The server itself.
resource "aws_instance" "app" {
  # checkov:skip=CKV2_AWS_41: the app never calls AWS APIs, so no role (least privilege); Learner Lab also forbids custom roles
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.instance_type
  vpc_security_group_ids = [aws_security_group.app.id]

  # Extra security monitoring and disk performance (Checkov asks for these).
  monitoring    = true
  ebs_optimized = true

  # IMDSv2 only: blocks a classic credential-theft trick (SSRF).
  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  # Encrypted disk.
  root_block_device {
    encrypted = true
  }

  tags = {
    Name = "task-tracker"
  }
}
