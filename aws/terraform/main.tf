terraform {
  required_version = ">= 1.0"
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

resource "aws_sns_topic" "farmtech_alerts" {
  name = "FarmTechAlerts"
  tags = {
    Project = "FarmTech"
  }
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.farmtech_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

output "sns_topic_arn" {
  value = aws_sns_topic.farmtech_alerts.arn
}
