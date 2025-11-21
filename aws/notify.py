# aws/notify.py
import os, re, uuid
import boto3
from botocore.exceptions import ClientError
from datetime import datetime

SNS_ARN = (os.getenv("SNS_TOPIC_ARN") or "").strip()
AWS_REGION = (os.getenv("AWS_REGION") or "sa-east-1").strip()
ARN_RE = re.compile(r"^arn:aws:sns:[a-z0-9-]+:\d{12}:[A-Za-z0-9-_\.]+$")

def validate_arn(arn: str):
    return bool(arn and ARN_RE.match(arn))

def publish_alert(message: str, subject: str = "Alerta FarmTech", message_group_id: str = None):
    if not validate_arn(SNS_ARN):
        raise ValueError("SNS_TOPIC_ARN inválido ou não configurado")

    client = boto3.client("sns", region_name=AWS_REGION)
    is_fifo = SNS_ARN.lower().endswith(".fifo")

    kwargs = {"TopicArn": SNS_ARN, "Message": message, "Subject": subject[:100]}
    if is_fifo:
        kwargs["MessageGroupId"] = message_group_id or f"farmtech-{datetime.utcnow().strftime('%Y%m%d')}"
        kwargs["MessageDeduplicationId"] = str(uuid.uuid4())

    try:
        resp = client.publish(**kwargs)
        return resp
    except ClientError as e:
        raise
