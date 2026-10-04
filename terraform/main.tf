# Latest Amazon Linux 2023 image
data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
}

resource "aws_security_group" "app" {
  name        = "task-tracker-sg"
  description = "Task Tracker: app port from one IP only"

  ingress {
    description = "Task Tracker app from my IP only"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = [var.my_ip_cidr]
  }

  # HTTPS only, enough to pull updates and the image
  egress {
    description = "HTTPS out"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "app" {
  # checkov:skip=CKV2_AWS_41: the app makes no AWS API calls, so no role (least privilege); Learner Lab blocks custom roles anyway
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.instance_type
  vpc_security_group_ids = [aws_security_group.app.id]

  # first-boot script: installs Docker and starts the app
  user_data = templatefile("${path.module}/user_data.sh.tftpl", {
    registry_host  = var.registry_host
    registry_user  = var.registry_user
    registry_token = var.registry_token
    image          = var.image
  })
  # a changed script means a new server, not a stale one
  user_data_replace_on_change = true

  monitoring    = true
  ebs_optimized = true

  # IMDSv2 only
  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  root_block_device {
    encrypted = true
  }

  tags = {
    Name = "task-tracker"
  }
}
