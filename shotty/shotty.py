import boto3
import click

session = boto3.Session(profile_name='pylearn')
ec2 = session.resource('ec2')

#helper functions
def filter_instances(project):
    instances = []
    if project:
        filters = [{'Name': 'tag:Project', 'Values': [project]}]
        instances = ec2.instances.filter(Filters=filters)
    else:
        instances = ec2.instances.all()

    return instances

#main group
@click.group()
def cli():
    """Shotty manages EC2 snapshots"""

#snapshots
@cli.group('snapshots')
def snapshots():
    """Commands for snapshots"""

@snapshots.command('list')
@click.option('--project', default=None,
              help="Only snapshots for project (tag Project:<name>)")
def list_snapshots(project):
    """List EC2 snapshots"""

    instances = filter_instances(project)

    for i in instances:
        for v in i.volumes.all():
            for s in v.snapshots.all():
                print(', '.join((
                    s.id,
                    v.id,
                    i.id,
                    s.state,
                    s.progress,
                    s.start_time.strftime("%c")
                )))

    return


#volumes
@cli.group('volumes')
def volumes():
    """Commands for volumes"""

@volumes.command('list')
@click.option('--project', default=None,
              help="Only volumes for project (tag Project:<name>)")
def list_volumes(project):
    "List EC2 volumes"

    instances = filter_instances(project)

    for i in instances:
        for v in i.volumes.all():
            print(', '.join((
                v.id,
                i.id,
                v.state,
                str(v.size) + "GiB",
                v.encrypted and "Encrypted" or "Not Encrypted"
            )))

    return


#instances
@cli.group('instances')
def instances():
    """Commands for instances"""


@instances.command('snapshot',
                   help="Create snapshot of all volumes")
@click.option('--project', default=None,
              help="Only instances for project (tag Project:<name>)")
def create_snapshots(project):
    """Create snapshots for EC2 instances"""

    print("Starting snapshots...")

    instances = filter_instances(project)

    for i in instances:
        print("   Stopping instance {0}".format(i.id))
        i.stop()
        i.wait_until_stopped()

        for v in i.volumes.all():
            print("      Creating snapshot of {0}".format(v.id))
            v.create_snapshot(Description="Created by pylearn")

        print("   Starting instance {0}".format(i.id))
        i.start()
        i.wait_until_running()

    print("All done!")

    return


@instances.command('list')
@click.option('--project', default=None,
              help="Only instances for project (tag Project:<name>)")
def list_instances(project):
    "List EC2 instances"

    instances = filter_instances(project)

    for i in instances:
        tags = {t['Key']: t['Value'] for t in i.tags or []}
        print(', '.join((
            i.id,
            i.instance_type,
            i.placement['AvailabilityZone'],
            i.state['Name'],
            i.public_dns_name,
            tags.get('Project', '<no project>')
        )))
    return


@instances.command('stop')
@click.option('--project', default=None,
              help="Only instances for project (tag Project:<name>)")
def stop_instances(project):
    "Stop instances for project"

    instances = filter_instances(project)

    for i in instances:
        print("Stopping {0}...".format(i.id))
        i.stop()


@instances.command('start')
@click.option('--project', default=None,
              help="Only instances for project (tag Project:<name>)")
def stop_instances(project):
    "Start instances for project"

    instances = filter_instances(project)

    for i in instances:
        print("Starting {0}...".format(i.id))
        i.start()


if __name__ == '__main__':
    cli()
