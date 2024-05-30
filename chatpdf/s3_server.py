import boto3
import os
import tempfile
import logging

logger = logging.getLogger(__name__)

def download_from_s3(file_key):
    # Get environment variables
    S3_ACCESS_KEY_ID ="AKIAU6GDYRHUK3JNRTEE"
    S3_SECRET_ACCESS_KEY="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"
    S3_BUCKET_NAME="chatandpdf"
    S3_REGION_NAME="ap-southeast-2"

    # Log the environment variables
    logger.debug(f"AWS_S3_REGION_NAME: {S3_REGION_NAME}")
    logger.debug(f"AWS_ACCESS_KEY_ID: {S3_ACCESS_KEY_ID}")
    logger.debug(f"AWS_SECRET_ACCESS_KEY: {S3_SECRET_ACCESS_KEY}")
    logger.debug(f"AWS_STORAGE_BUCKET_NAME: {S3_BUCKET_NAME}")

    # Check if any environment variable is None
    if not S3_REGION_NAME or not S3_ACCESS_KEY_ID or not S3_SECRET_ACCESS_KEY or not S3_BUCKET_NAME:
        logger.error("One or more AWS environment variables are not set.")
        return None

    s3 = boto3.client(
        's3',
        region_name=S3_REGION_NAME,
        aws_access_key_id=S3_ACCESS_KEY_ID,
        aws_secret_access_key=S3_SECRET_ACCESS_KEY
    )

    try:
        # Ensure the file key is valid
        if not file_key:
            raise ValueError("file_key must be provided")

        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')

        # Download the file object from S3
        with open(temp_file.name, 'wb') as f:
            s3.download_fileobj(S3_BUCKET_NAME, file_key, f)
        
        logger.debug(f"File downloaded to temporary path: {temp_file.name}")
        return temp_file.name
    except Exception as e:
        logger.error(f"Error downloading from S3: {e}")
        return None
