import boto3
import config
import io
from flask import send_file


# Initialize boto3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=config.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
    region_name=config.AWS_REGION
)

def list_buckets():
    response = s3_client.list_buckets()
    return response.get('Buckets', [])

def create_bucket(bucket_name):
    s3_client.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={'LocationConstraint': config.AWS_REGION}
    )

def delete_bucket(bucket_name):
    # List and delete all objects in the bucket first
    paginator = s3_client.get_paginator('list_objects_v2')
    try:
        for page in paginator.paginate(Bucket=bucket_name):
            objects = page.get('Contents', [])
            if objects:
                delete_keys = [{'Key': obj['Key']} for obj in objects]
                s3_client.delete_objects(Bucket=bucket_name, Delete={'Objects': delete_keys})
        # Now delete the bucket
        s3_client.delete_bucket(Bucket=bucket_name)
    except Exception as e:
        raise Exception(f"Failed to delete bucket '{bucket_name}': {e}")

def list_objects(bucket_name, prefix=""):
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    return response.get('Contents', [])

def upload_file(bucket_name, file_obj, key):
    s3_client.upload_fileobj(file_obj, bucket_name, key)

def delete_file(bucket_name, key):
    s3_client.delete_object(Bucket=bucket_name, Key=key)

def copy_file(src_bucket, src_key, dest_bucket, dest_key):
    copy_source = {'Bucket': src_bucket, 'Key': src_key}
    s3_client.copy_object(CopySource=copy_source, Bucket=dest_bucket, Key=dest_key)

def move_file(src_bucket, src_key, dest_bucket, dest_key):
    copy_file(src_bucket, src_key, dest_bucket, dest_key)
    delete_file(src_bucket, src_key)

def generate_presigned_url(bucket_name, key, expiration=3600):
    return s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket_name, 'Key': key},
        ExpiresIn=expiration
    )

def download_file(bucket_name, key):
    file_stream = io.BytesIO()
    s3_client.download_fileobj(bucket_name, key, file_stream)
    file_stream.seek(0)
    return send_file(file_stream, as_attachment=True, download_name=key)

def create_folder(bucket_name, folder_key):
    # Create a zero-byte object with a trailing slash to represent a folder
    s3_client.put_object(Bucket=bucket_name, Key=folder_key)

def list_objects_grouped(bucket_name, prefix=""):
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix, Delimiter="/")
    folders = response.get('CommonPrefixes', [])
    files = response.get('Contents', [])
    return folders, files


