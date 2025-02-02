import boto3
from botocore.exceptions import ClientError
import json
import logging

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


class EC2Manager:
    def __init__(self, region=None):
        self.region = region or config.get('default_region', 'us-east-1')
        self.ec2 = boto3.resource('ec2', region_name=self.region)
        self.client = boto3.client('ec2', region_name=self.region)
        self.username_tag_key = config.get('username_tag_key', 'CreatedByCLIUser')
        self.username = config.get('username')  # Read username from config

    def create_instance(self, instance_type, ami_id, subnet_id, name):
        try:
            if self._count_running_instances() >= config.get('max_running_instances', 2):
                logger.error('Instance limit reached.')
                raise Exception('Instance limit reached.')

            instances = self.ec2.create_instances(
                InstanceType=instance_type,
                ImageId=ami_id,
                SubnetId=subnet_id,
                MinCount=1,
                MaxCount=1,
                TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [
                            {'Key': self.username_tag_key, 'Value': self.username},
                            {'Key': 'Name', 'Value': name}
                        ]
                    }
                ]
            )
            instance_id = instances[0].id
            logger.info(f'Created instance {instance_id}')
            return instance_id
        except ClientError as e:
            logger.error(f'Error creating instance: {e}')
            return None

    def start_instance(self, name=None, instance_id=None):
        instance_id = instance_id or self.get_instance_id_by_name(name)
        if not instance_id:
            logger.error(f'No instance found with name {name} or ID {instance_id}.')
            return

        instance = self.ec2.Instance(instance_id)
        if self._validate_instance(instance):
            try:
                instance.start()
                logger.info(f'Started instance {instance_id}')
            except ClientError as e:
                logger.error(f'Error starting instance {instance_id}: {e}')
        else:
            logger.error(f'Instance {instance_id} does not belong to {self.username} or was not created by CLI.')

    def stop_instance(self, name=None, instance_id=None):
        instance_id = instance_id or self.get_instance_id_by_name(name)
        if not instance_id:
            logger.error(f'No instance found with name {name} or ID {instance_id}.')
            return

        instance = self.ec2.Instance(instance_id)
        if self._validate_instance(instance):
            try:
                instance.stop()
                logger.info(f'Stopped instance {instance_id}')
            except ClientError as e:
                logger.error(f'Error stopping instance {instance_id}: {e}')
        else:
            logger.error(f'Instance {instance_id} does not belong to {self.username} or was not created by CLI.')

    def list_instances(self):
        try:
            instances = self.client.describe_instances(
                Filters=[
                    {'Name': 'tag:CreatedByCLIUser', 'Values': [self.username]}
                ]
            )
            instance_details = []
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    instance_id = instance['InstanceId']
                    # Get the instance name
                    name = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), 'Unnamed')
                    instance_details.append({'ID': instance_id, 'Name': name})

            logger.info(f'Listed instances: {instance_details}')
            return instance_details
        except ClientError as e:
            logger.error(f'Error listing instances: {e}')
            return []

    def get_instance_id_by_name(self, name):
        try:
            instances = self.client.describe_instances(
                Filters=[
                    {'Name': 'tag:Name', 'Values': [name]},
                    {'Name': 'tag:CreatedByCLIUser', 'Values': [self.username]}
                ]
            )
            instance_ids = [i['InstanceId'] for r in instances['Reservations'] for i in r['Instances']]
            if instance_ids:
                logger.info(f'Found instance ID {instance_ids[0]} for name {name}')
                return instance_ids[0]
            else:
                logger.error(f'No instance found with name {name}')
                return None
        except ClientError as e:
            logger.error(f'Error finding instance by name {name}: {e}')
            return None

    def _count_running_instances(self):
        """Count all instances that are running or stopped, excluding terminated instances."""
        try:
            # Describe all instances created by the CLI
            instances = self.client.describe_instances(
                Filters=[
                    {'Name': 'tag:CreatedByCLIUser', 'Values': [self.username]}
                ]
            )

            running_and_stopped_instances = 0
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    state = instance['State']['Name']
                    if state in ['running', 'stopped']:
                        running_and_stopped_instances += 1

            logger.info(f'Count of running and stopped instances: {running_and_stopped_instances}')
            return running_and_stopped_instances

        except ClientError as e:
            logger.error(f'Error counting instances: {e}')
            return 0

    def _validate_instance(self, instance):
        """Check if the instance exists and has the correct user tag."""
        tags = instance.tags or []
        user_tag = next((tag['Value'] for tag in tags if tag['Key'] == self.username_tag_key), None)
        return user_tag == self.username
