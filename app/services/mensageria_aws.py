"""
Wrapper simples para publicação em SNS. Faz fallback para log local se AWS não configurada.
Exige AWS credentials via env vars (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION)
"""
import os
import json
import logging

logger = logging.getLogger("mensageria")
logger.setLevel(logging.INFO)

try:
    import boto3
    AWS_AVAILABLE = True
except Exception:
    AWS_AVAILABLE = False

TOPIC_ARN = os.getenv("SNS_TOPIC_ARN", "")

def publish_alert(subject: str, message: str):
    if AWS_AVAILABLE and TOPIC_ARN:
        client = boto3.client("sns", region_name=os.getenv("AWS_REGION", "us-east-1"))
        client.publish(TopicArn=TOPIC_ARN, Subject=subject, Message=json.dumps({"default": message}), MessageStructure='json')
        logger.info("Publicado no SNS: %s", subject)
    else:
        # fallback simples
        logger.info("FALLBACK publish: %s - %s", subject, message)
