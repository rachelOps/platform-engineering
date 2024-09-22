import boto3
import uuid
import json
import logging
import re
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load configuration
with open('config.json') as f:
    config = json.load(f)

default_region = config['default_region']
created_by = config['username']
default_vpc_id = config['default_vpc_id']


def is_valid_ip(ip):
    """Validate an IPv4 address."""
    pattern = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    return re.match(pattern, ip) is not None


class Route53Manager:
    def __init__(self):
        self.zones_file = 'created_zones.json'
        self.created_zones = self.load_zones()

        # Load configuration
        with open('config.json') as config_file:
            config = json.load(config_file)
            self.region = config.get('default_region', 'us-east-1')
            self.username = config.get('username', 'unknown')
            self.default_vpc_id = config.get('default_vpc_id', None)

        # Initialize the Route 53 client
        self.client = boto3.client('route53')

    def load_zones(self):
        if os.path.exists(self.zones_file):
            with open(self.zones_file) as f:
                return json.load(f)
        return []

    def save_zones(self):
        with open(self.zones_file, 'w') as f:
            json.dump(self.created_zones, f)

    def create_zone(self, name, zone_type, vpc_id=None):
        kwargs = {
            'Name': name,
            'CallerReference': str(uuid.uuid4()),
            'HostedZoneConfig': {
                'Comment': f'Created by {self.username}',
                'PrivateZone': zone_type == 'private'
            }
        }

        if zone_type == 'private' and vpc_id:
            kwargs['VPC'] = {
                'VPCId': vpc_id,
                'VPCRegion': self.region
            }

        response = self.client.create_hosted_zone(**kwargs)
        zone_id = response['HostedZone']['Id']
        self.created_zones.append({'Id': zone_id, 'Name': name})
        self.save_zones()  # Persist changes
        logger.info(f"Zone created: {name} with ID: {zone_id}")  # Logging
        return zone_id

    def list_zones(self):
        """List zones created by this user."""
        logger.info("Listing created zones.")
        return [{"Name": zone['Name'], "Id": zone['Id']} for zone in self.created_zones]

    def get_zone_id_by_name(self, zone_name):
        for zone in self.created_zones:
            if zone['Name'] == zone_name:
                return zone['Id']
        return None

    def create_record(self, zone_id, record_name, record_type, record_value):
        if not any(zone['Id'] == zone_id for zone in self.created_zones):
            raise ValueError(f"Zone ID {zone_id} is not allowed. It must be created by you via the CLI.")

        record_set = {
            'Name': record_name,
            'Type': record_type,
            'TTL': 300,
            'ResourceRecords': [{'Value': record_value}]
        }

        response = self.client.change_resource_record_sets(
            HostedZoneId=zone_id,
            ChangeBatch={
                'Changes': [{
                    'Action': 'CREATE',
                    'ResourceRecordSet': record_set
                }]
            }
        )

        return response

    def update_record(self, zone_id, record_name, record_type, new_value, new_ttl):
        # Check if the zone_id is in the created_zones list
        if not any(zone['Id'] == zone_id for zone in self.created_zones):
            logger.error(f"Zone ID {zone_id} is not managed by this CLI.")
            return False

        change_batch = {
            'Changes': [
                {
                    'Action': 'UPSERT',  # To update, we use UPSERT
                    'ResourceRecordSet': {
                        'Name': record_name,
                        'Type': record_type,
                        'TTL': new_ttl,
                        'ResourceRecords': [{'Value': new_value}]
                    }
                }
            ]
        }

        response = self.client.change_resource_record_sets(
            HostedZoneId=zone_id,
            ChangeBatch=change_batch
        )

        return response['ChangeInfo']['Status'] == 'PENDING'

    def list_records(self, zone_id):
        """List all records in a given hosted zone."""
        response = self.client.list_resource_record_sets(HostedZoneId=zone_id)
        return response['ResourceRecordSets']

    def delete_record(self, zone_id, record_name, record_type, record_value):
        # Check if the zone ID is in the list of managed zones
        if not any(zone['Id'] == zone_id for zone in self.created_zones):
            logger.error(f"Zone ID {zone_id} is not managed by this CLI.")
            return False

        # Prepare the resource record set for deletion
        change_batch = {
            'Changes': [
                {
                    'Action': 'DELETE',
                    'ResourceRecordSet': {
                        'Name': record_name,
                        'Type': record_type,
                        'TTL': 300,  # You can keep a standard TTL value here
                        'ResourceRecords': [{'Value': record_value}]  # Use the actual value for deletion
                    }
                }
            ]
        }

        response = self.client.change_resource_record_sets(
            HostedZoneId=zone_id,
            ChangeBatch=change_batch
        )

        return response['ChangeInfo']['Status'] == 'PENDING'
