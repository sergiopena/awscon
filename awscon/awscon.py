from boto3 import client
from botocore.exceptions import ClientError, ProfileNotFound, NoRegionError, EndpointConnectionError

from PyInquirer import style_from_dict, Token, prompt
from examples import custom_style_2

import sys
import subprocess
import argparse
import re

def get_instances(args):
    ec2_instances = []

    try:
        ec2client = client('ec2',region_name=args.region)
        response = ec2client.describe_instances()
    except ProfileNotFound as e:
        print e.message
        print("Make sure you defined and env var " +
              "AWS_PROFILE pointing to your credentials")
        sys.exit(1)
    except NoRegionError as e:
        print e.message
        print "You need to define a region in your profile"
        sys.exit(1)
    except EndpointConnectionError as e:
        print e.message
        print "Check your region name, seems it's not reachable"
        sys.exit(1)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        raise

    for ins in response['Reservations']:
        instance = ins['Instances'][0]
        instanceId = instance['InstanceId']

        if 'Tags' in instance:
            name = [k['Value'] for k in instance['Tags'] if k['Key'] == 'Name']
            if name == []:
                name = ''
            else:
                name = name[0]
        else:
            name = ''

        if 'PublicIpAddress' in instance:
            publicAddress = instance['PublicIpAddress']
        else:
            publicAddress = ''

    	if 'PrivateIpAddress' in instance:
	        privateAddress = instance['PrivateIpAddress']
    	else:
	        privateAddress = ''

        entry = "%s - %s - %s - %s " % (instanceId,
                                        '{:<15}'.format(publicAddress),
                                        '{:<15}'.format(privateAddress),
                                        name)
        ec2_instances.append(entry)

    if args.name != None:
        r = re.compile('.* - .* - .* - .*'+args.name+'.*')
        ec2_instances = filter(r.match, ec2_instances)

    return ec2_instances


def main():

    parser = argparse.ArgumentParser(
        description='AWS SSM console manager',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument('--region', '-r', default='eu-west-1',
                        help='Region to retrieve instances from')

# TODO
#    parser.add_argument('--instance', '-i', required=False,
#                        help='Filter by instance id by applying .*arg.*')

    parser.add_argument('--name', '-n', required=False,
                        help='Filter by instance name by applying .*arg.*')

    args = parser.parse_args()

    prompt_list = [
      {
        'type': 'list',
        'name': 'instance',
        'message': 'Select instance to connect',
        'choices': get_instances(args)
      }]

    answers = prompt(prompt_list, style=custom_style_2)
    instanceId = answers['instance'].split(' - ')[0]
    subprocess.call(["aws", "ssm", "start-session", "--target", instanceId])


if __name__ == '__main__':
    main()
