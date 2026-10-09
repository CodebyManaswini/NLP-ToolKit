variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}


variable "instance_type" {
  description = "EC2 instance size"
  type        = string
  default     = "t3.micro"
}

variable "key_name" {
  description = "Name of the existing EC2 key pair"
  type        = string
  default     = "ubuntu-key"
}

variable "github_repo_url" {
  description = "HTTPS URL of the GitHub repo to clone on the instance"
  type        = string
  default     = "https://github.com/CodebyManaswini/NLP-ToolKit.git"
}