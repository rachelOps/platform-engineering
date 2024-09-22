import boto3
import logging
from botocore.exceptions import ClientError
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
with open('config.json') as config_file:
    config = json.load(config_file)


class S3Manager:
    def __init__(self, region):
        self.region = region
        self.s3 = boto3.client('s3', region_name=region)
        logger.info(f"S3 Manager initialized for region: {region}")

    def create_bucket(self, name, public=False, user=None):
        try:
            # Create bucket with region configuration
            if self.region == 'us-east-1':
                response = self.s3.create_bucket(Bucket=name)
            else:
                response = self.s3.create_bucket(
                    Bucket=name,
                    CreateBucketConfiguration={
                        'LocationConstraint': self.region
                    }
                )

            if public:
                self.make_bucket_public(name)

            # Tag the bucket
            self.s3.put_bucket_tagging(
                Bucket=name,
                Tagging={
                    'TagSet': [
                        {'Key': 'CreatedBy', 'Value': user}
                    ]
                }
            )

            logger.info(f"Bucket created: {name}")
            return name
        except ClientError as e:
            logger.error(f"Error creating bucket: {e}")
            return None

    def make_bucket_public(self, name):
        # Set the bucket policy to make it public
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{name}/*"
                }
            ]
        }
        policy_string = json.dumps(bucket_policy)
        self.s3.put_bucket_policy(Bucket=name, Policy=policy_string)
        logger.info(f"Bucket {name} is now public")

    def list_buckets(self):
        buckets = self.s3.list_buckets().get('Buckets', [])
        user_tagged_buckets = []

        for bucket in buckets:
            bucket_name = bucket['Name']
            try:
                tags = self.s3.get_bucket_tagging(Bucket=bucket_name).get('TagSet', [])
                tags_dict = {tag['Key']: tag['Value'] for tag in tags}
                if tags_dict.get('CreatedBy') == config['username']:
                    user_tagged_buckets.append(bucket_name)
            except ClientError:
                # Ignore buckets that do not have tags
                continue

        return user_tagged_buckets

    def upload_file(self, bucket_name, file_path, object_name=None):
        """Upload a file to an S3 bucket"""
        if object_name is None:
            object_name = file_path

        try:
            self.s3.upload_file(file_path, bucket_name, object_name)
            logger.info(f"File {file_path} uploaded to bucket {bucket_name} as {object_name}")
            return True
        except ClientError as e:
            logger.error(f"Failed to upload file: {e}")
            return False
