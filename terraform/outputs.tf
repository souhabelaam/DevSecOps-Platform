output "app_url" {
  description = "Where the app answers (only from the allowed IP)"
  value       = "http://${aws_instance.app.public_ip}:8000"
}

output "instance_id" {
  description = "Instance id, to find it in the console"
  value       = aws_instance.app.id
}
