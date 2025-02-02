import click
import logging
from plat_manager import EC2Manager
import json
from s3_manager import S3Manager
from route53_manager import Route53Manager


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load configuration
with open('/var/lib/jenkins/workspace/pip/platform-engineering/platform_engineering/config.json') as config_file:
    config = json.load(config_file)


default_ami = config.get('default_ami', 'ubuntu')
default_subnet_id = config.get('default_subnet_id', None)
instance_types = config.get('instance_types', [])
default_region = config.get('default_region', 'us-east-1')
default_instance_name = "Rachel's_instance"
username = config.get('username', 'default_user')
username_tag_key = config.get('username_tag_key', 'CreatedByCLIUser')


@click.group()
def cli():
    """AWS CLI Tool"""
    pass


# EC2 Commands
@cli.group()
def ec2():
    """EC2 management commands"""
    pass


@ec2.command()
@click.option('--type', prompt='Instance type', help='Type of EC2 instance.')
@click.option('--ami', default=default_ami, help='AMI ID for the EC2 instance (default: from config).')
@click.option('--subnet', default=default_subnet_id, help='Subnet ID for the EC2 instance (default: from config).')
@click.option('--name', default=default_instance_name, help='Name for the EC2 instance (default: Rachel\'s_instance).')
def create(type, ami, subnet, name):
    """Create a new EC2 instance"""
    ec2_manager = EC2Manager(region=default_region)

    # Validate instance type
    if type not in instance_types:
        logger.error(f"Invalid instance type: {type}")
        click.echo(f"Invalid instance type: {type}")
        return

    # Validate AMI ID
    ami_id = config['ami_ids'].get(ami, ami) if ami in config['ami_ids'] else ami

    if ami_id not in config['ami_ids'].values():
        logger.error(f"Invalid AMI ID: {ami_id}")
        click.echo(f"Invalid AMI ID: {ami_id}")
        return

    instance_id = ec2_manager.create_instance(type, ami_id, subnet, name)
    if instance_id:
        logger.info(f'Created instance {instance_id}')
        click.echo(f'Created instance {instance_id}')
    else:
        logger.error('Failed to create instance.')


@ec2.command()
@click.option('--name', help='Name of the EC2 instance.')
@click.option('--instance-id', help='ID of the EC2 instance.')
def start(name, instance_id):
    """Start an EC2 instance"""
    ec2_manager = EC2Manager(region=default_region)
    ec2_manager.start_instance(name=name, instance_id=instance_id)


@ec2.command()
@click.option('--name', help='Name of the EC2 instance.')
@click.option('--instance-id', help='ID of the EC2 instance.')
def stop(name, instance_id):
    """Stop an EC2 instance"""
    ec2_manager = EC2Manager(region=default_region)
    ec2_manager.stop_instance(name=name, instance_id=instance_id)


@ec2.command()
def list_instances():
    """List EC2 instances"""
    ec2_manager = EC2Manager(region=default_region)
    instances = ec2_manager.list_instances()
    for instance in instances:
        click.echo(f"ID: {instance['ID']}, Name: {instance['Name']}")


@cli.group()
def s3():
    """S3 management commands"""
    pass


@s3.command()
@click.option('--name', prompt='Bucket name', help='Name of the S3 bucket.')
@click.option('--public/--private', default=False, help='Specify if the bucket should be public or private.')
def create(name, public):
    """Create a new S3 bucket"""
    s3_manager = S3Manager(region=default_region)

    # Prompt for username
    user = click.prompt('Your name', default=username, type=str)

    bucket_name = s3_manager.create_bucket(name, public, user)
    if bucket_name:
        logger.info(f'Bucket created: {bucket_name}')
        click.echo(f'Bucket created: {bucket_name}')
    else:
        logger.error('Failed to create bucket.')
        click.echo('Failed to create bucket.')


@s3.command()
@click.option('--bucket', prompt='Bucket name', help='Name of the S3 bucket.')
@click.option('--file', prompt='Path to the file', help='Path to the file to upload.')
def upload(bucket, file):
    """Upload a file to an S3 bucket"""
    s3_manager = S3Manager(region=default_region)
    success = s3_manager.upload_file(bucket, file)
    if success:
        click.echo(f'Uploaded file {file} to bucket {bucket}')
    else:
        click.echo('Failed to upload file.')


@s3.command()
def list():
    """List S3 buckets"""
    s3_manager = S3Manager(region=default_region)
    buckets = s3_manager.list_buckets()
    if buckets:
        click.echo("Buckets created by you:")
        for bucket in buckets:
            click.echo(bucket)
    else:
        click.echo("No buckets found or no buckets created by you.")


@click.group()
def cli():
    """CLI for managing AWS services."""


if __name__ == '__main__':
    cli()
