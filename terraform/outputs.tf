output "instance_public_ip" {
  description = "Public IP of the EC2 instance"
  value       = aws_instance.nlp_toolkit.public_ip
}

output "frontend_url" {
  description = "URL to access the frontend"
  value       = "http://${aws_instance.nlp_toolkit.public_ip}:8080"
}