from boto3 import client
from botocore.exceptions import ClientError, ProfileNotFound

from PyInquirer import style_from_dict, Token, prompt
from examples import custom_style_2

import sys
import subprocess


def get_instances():
    ec2_instances = []

    try:
        ec2client = client('ec2')
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

        privateAddress = instance['PrivateIpAddress']
        entry = "%s - %s - %s - %s " % (instanceId,
                                        '{:<15}'.format(publicAddress),
                                        '{:<15}'.format(privateAddress),
                                        name)
        ec2_instances.append(entry)

    return ec2_instances


def main():
    prompt_list = [
      {
        'type': 'list',
        'name': 'instance',
        'message': 'Select instance to connect',
        'choices': get_instances()
      }]

    answers = prompt(prompt_list, style=custom_style_2)
    instanceId = answers['instance'].split(' - ')[0]
    subprocess.call(["aws", "ssm", "start-session", "--target", instanceId])


if __name__ == '__main__':
    main()
