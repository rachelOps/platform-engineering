CLI Commands Overview
General Commands
python cli.py: The main command for the AWS CLI tool.
EC2 Management Commands
python cli.py ec2 create: Create a new EC2 instance.

Options:
--type: Type of EC2 instance.
--ami: AMI ID for the EC2 instance (default from config).
--subnet: Subnet ID for the EC2 instance (default from config).
--name: Name for the EC2 instance (default: Rachel's_instance).
python cli.py ec2 start: Start an EC2 instance.

Options:
--name: Name of the EC2 instance.
--instance-id: ID of the EC2 instance.
python cli.py ec2 stop: Stop an EC2 instance.

Options:
--name: Name of the EC2 instance.
--instance-id: ID of the EC2 instance.
python cli.py ec2 list_instances: List all EC2 instances.

S3 Management Commands
python cli.py s3 create: Create a new S3 bucket.

Options:
--name: Name of the S3 bucket.
--public/--private: Specify if the bucket should be public or private.
python cli.py s3 upload: Upload a file to an S3 bucket.

Options:
--bucket: Name of the S3 bucket.
--file: Path to the file to upload.
python cli.py s3 list: List all S3 buckets created by you.

Route 53 Commands
Create Zone

Command: create-zone
Description: Create a Route 53 DNS zone.
Arguments:
name: Name of the zone.
Options:
--type: Type of DNS zone (public or private).
--vpc-id: The ID of the VPC (if it’s a private zone).
List Zones

Command: list-zones
Description: List all zones created by the user.
Create Record

Command: create-record
Description: Create a DNS record.
Arguments:
--zone-id: The ID of the zone.
--name: Name of the DNS record.
--type: Type of DNS record (A, CNAME, TXT).
--value: Value of the DNS record.
Update Record

Command: update-record
Description: Update an existing DNS record.
Arguments:
--zone-id: The ID of the hosted zone.
--name: Name of the DNS record.
--type: Type of DNS record (A, CNAME, TXT).
--value: New value of the DNS record.
--ttl: TTL for the DNS record (default: 300).
List Records

Command: list-records
Description: List all records in the specified hosted zone.
Arguments:
zone_id: The ID of the hosted zone.
Delete Record

Command: delete-record
Description: Delete a record from the specified hosted zone.
Arguments:
zone_id: The ID of the zone.
name: Name of the DNS record.
type: Type of DNS record (A, CNAME, TXT).
value: Value of the DNS record.


help: python route53_cli.py route53 <command> --help