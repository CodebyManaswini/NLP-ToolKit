terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_security_group" "nlp_toolkit_sg" {
  name        = "nlp-toolkit-sg"
  description = "Allow SSH and app ports for NLP Toolkit"

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Frontend"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Service ports (sentiment/grammar/summarize/languagetool)"
    from_port   = 8000
    to_port     = 8010
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "nlp-toolkit-sg"
  }
}

resource "aws_instance" "nlp_toolkit" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.nlp_toolkit_sg.id]

  user_data = <<-EOF
              #!/bin/bash
              set -e

              # Add 2GB swap — t3.micro only has 1GB RAM, not enough for
              # 3 ML services running together without this
              fallocate -l 2G /swapfile
              chmod 600 /swapfile
              mkswap /swapfile
              swapon /swapfile
              echo '/swapfile none swap sw 0 0' >> /etc/fstab

              apt-get update -y
              apt-get install -y git

              curl -fsSL https://get.docker.com -o get-docker.sh
              sh get-docker.sh
              usermod -aG docker ubuntu

              git clone ${var.github_repo_url} /home/ubuntu/NLP-ToolKit
              cd /home/ubuntu/NLP-ToolKit
              docker compose -f docker-compose.prod.yml up -d
              EOF

  tags = {
    Name = "nlp-toolkit"
  }
}