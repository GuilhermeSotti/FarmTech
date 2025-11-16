import os
import boto3
from datetime import datetime

sns_arn = os.getenv("SNS_TOPIC_ARN", "arn:aws:sns:REGION:ACCOUNT:FarmTechAlerts")
aws_region = os.getenv("AWS_REGION", "us-east-1")

def publish_alert(message, subject="Alerta FarmTech"):
    try:
        client = boto3.client('sns', region_name=aws_region)
        response = client.publish(
            TopicArn=sns_arn,
            Message=message,
            Subject=subject
        )
        print(f"Alert published: {response['MessageId']}")
        return response
    except Exception as e:
        print(f"Error publishing alert: {e}")
        return None

if __name__ == '__main__':
    msg = f"Alerta crítico: Umidade baixa detectada às {datetime.now().isoformat()}"
    publish_alert(msg, "Alerta de Umidade - FarmTech")
