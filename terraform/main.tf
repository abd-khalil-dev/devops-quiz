terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

provider "aws" {
  region = "ap-south-1"
}

variable "my_ip" {
  description = "My public IP in CIDR form, for SSH"
  type        = string
}

data "aws_vpc" "default" {
  default = true
}

resource "aws_security_group" "quiz" {
  name        = "quiz-sg"
  description = "Quiz app: SSH from my IP, web from anywhere"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH from my IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
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
    Name    = "quiz-sg"
    Project = "devops-quiz"
  }
}

output "security_group_id" {
  value = aws_security_group.quiz.id
}

variable "instance_type" {
  description = "EC2 size. k3s plus Postgres needs about 2 GB RAM."
  type        = string
  default     = "t3.small"
}

variable "public_key_path" {
  type    = string
  default = "~/.ssh/quiz-aws.pub"
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }
}

resource "aws_key_pair" "quiz" {
  key_name   = "quiz-key"
  public_key = file(pathexpand(var.public_key_path))
}

resource "aws_instance" "quiz" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.quiz.key_name
  vpc_security_group_ids = [aws_security_group.quiz.id]

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  metadata_options {
    http_tokens = "required"
  }

  tags = {
    Name    = "quiz-server"
    Project = "devops-quiz"
  }
}

output "public_ip" {
  value = aws_instance.quiz.public_ip
}

output "ssh_command" {
  value = "ssh -i ~/.ssh/quiz-aws ubuntu@${aws_instance.quiz.public_ip}"
}
