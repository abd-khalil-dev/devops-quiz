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
  iam_instance_profile   = aws_iam_instance_profile.quiz.name
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

resource "aws_iam_role" "ec2_ssm" {
  name = "quiz-ec2-ssm"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.ec2_ssm.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "quiz" {
  name = "quiz-ec2-ssm"
  role = aws_iam_role.ec2_ssm.name
}

output "instance_id" {
  value = aws_instance.quiz.id
}

variable "github_repo" {
  description = "GitHub repo allowed to deploy (owner/name)"
  type        = string
  default     = "abd-khalil-dev/devops-quiz"
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

resource "aws_iam_openid_connect_provider" "github" {
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}

resource "aws_iam_role" "github_deploy" {
  name = "quiz-github-deploy"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Federated = aws_iam_openid_connect_provider.github.arn }
      Action    = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          "token.actions.githubusercontent.com:sub" = var.github_sub
        }
      }
    }]
  })
}

resource "aws_iam_role_policy" "github_deploy" {
  name = "deploy-via-ssm"
  role = aws_iam_role.github_deploy.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["ec2:DescribeInstances", "ssm:GetCommandInvocation", "ssm:ListCommandInvocations", "ssm:DescribeInstanceInformation"]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = "ssm:SendCommand"
        Resource = [
          "arn:aws:ec2:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:instance/*",
          "arn:aws:ssm:${data.aws_region.current.region}::document/AWS-RunShellScript"
        ]
      }
    ]
  })
}

output "github_role_arn" {
  value = aws_iam_role.github_deploy.arn
}

variable "github_sub" {
  description = "OIDC subject GitHub sends (includes owner and repo IDs)"
  type        = string
  default     = "repo:abd-khalil-dev@318783742/devops-quiz@1414521964:ref:refs/heads/main"
}
