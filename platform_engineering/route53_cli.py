import click
import logging
from route53_manager import Route53Manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """Main CLI command."""
    pass


@cli.group()
def route53():
    """Route53 management commands."""
    logger.info("Route53 command registered")


@route53.command(name='create-zone')
@click.argument('name')
@click.option('--type', type=click.Choice(['public', 'private']), default='public', help='Type of DNS zone')
@click.option('--vpc-id', default=None, help='The ID of the VPC (if private zone)')
def create_zone(name, type, vpc_id):
    """Create a Route 53 DNS zone."""
    manager = Route53Manager()

    if type == 'private':
        vpc_id = vpc_id or manager.default_vpc_id

    zone_id = manager.create_zone(name, type, vpc_id)
    click.echo(f'Created zone with ID: {zone_id}')


@route53.command(name='list-zones')
def list_zones():
    """List all zones created by the user."""
    manager = Route53Manager()
    zones = manager.list_zones()

    if not zones:  # If no zones exist
        click.echo("No zones found created by you.")
    else:
        click.echo("Zones created by you:")
        for zone in zones:
            click.echo(f"{zone['Name']} - {zone['Id']}")


@route53.command(name='create-record')
@click.option('--zone-id', required=True, help='The ID of the zone.')
@click.option('--name', required=True, help='Name of the DNS record.')
@click.option('--type', type=click.Choice(['A', 'CNAME', 'TXT']), required=True, help='Type of DNS record.')
@click.option('--value', required=True, help='Value of the DNS record.')
def create_record(zone_id, name, type, value):
    """Create a DNS record."""
    manager = Route53Manager()
    try:
        result = manager.create_record(zone_id, name, type, value)
        click.echo(f'Created record {name} of type {type} in zone {zone_id} with value {value}.')
    except Exception as e:
        click.echo(f"Error: {str(e)}")


@route53.command(name='update-record')
@click.option('--zone-id', required=True, help='The ID of the hosted zone.')
@click.option('--name', required=True, help='Name of the DNS record.')
@click.option('--type', type=click.Choice(['A', 'CNAME', 'TXT']), required=True, help='Type of DNS record.')
@click.option('--value', required=True, help='New value of the DNS record.')
@click.option('--ttl', type=int, default=300, help='TTL for the DNS record.')
def update_record(zone_id, name, type, value, ttl):
    """Update an existing DNS record."""
    manager = Route53Manager()

    try:
        status = manager.update_record(zone_id, name, type, value, ttl)
        click.echo(f'Updated record {name} of type {type} in zone {zone_id} with new value {value}. Status: {status}.')
    except Exception as e:
        click.echo(f"Error updating record: {e}")


@route53.command(name='list-records')
@click.argument('zone_id')  # Change this to a positional argument
def list_records(zone_id):
    """List all records in the specified hosted zone."""
    manager = Route53Manager()
    records = manager.list_records(zone_id)

    if not records:
        click.echo("No records found.")
        return

    click.echo("Records in zone:")
    for record in records:
        click.echo(f"Name: {record['Name']}, Type: {record['Type']}, Value: {[r['Value'] for r in record['ResourceRecords']]}")


@route53.command(name='delete-record')
@click.argument('zone_id')
@click.argument('name')
@click.argument('type')
@click.argument('value')  # Keep value as an argument
def delete_record(zone_id, name, type, value):
    """Delete a record from the specified hosted zone."""
    manager = Route53Manager()
    try:
        success = manager.delete_record(zone_id, name, type, value)

        if success:
            click.echo(f"Record {name} of type {type} deleted successfully.")
        else:
            click.echo(f"Error deleting record: {name} of type {type}.")
    except Exception as e:
        click.echo(f"Error deleting record: {e}")


if __name__ == '__main__':
    cli()
