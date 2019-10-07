import boto3
from botocore import credentials
import botocore.session
from botocore.exceptions import (
    ClientError,
    ProfileNotFound,
    NoRegionError,
    EndpointConnectionError,
)

from PyInquirer import style_from_dict, Token, prompt
from examples import custom_style_2

import sys
import os
import argparse
import re
import json

# Use the credential cache path used by awscli
AWS_CREDENTIAL_CACHE_DIR = os.path.join(
    os.path.expanduser("~"), ".aws/cli/cache"
)


def build_aws_client(*args, **kwargs):
    """Build an AWS client using the awscli credential cache."""

    # Create a session with the credential cache
    session = botocore.session.get_session()
    provider = session.get_component("credential_provider").get_provider(
        "assume-role"
    )
    provider.cache = credentials.JSONFileCache(AWS_CREDENTIAL_CACHE_DIR)

    # Create boto3 client from session
    return boto3.Session(botocore_session=session).client(*args, **kwargs)


def get_instances(args):
    ec2_instances = []

    try:
        ec2client = build_aws_client("ec2", region_name=args.region)

        response = ec2client.describe_instances()
    except ProfileNotFound as e:
        print(e.message)
        print(
            "Make sure you defined and env var AWS_PROFILE "
            "pointing to your credentials"
        )
        sys.exit(1)
    except NoRegionError as e:
        print(e.message)
        print("You need to define a region in your profile")
        sys.exit(1)
    except EndpointConnectionError as e:
        print(e.message)
        print("Check your region name, seems it's not reachable")
        sys.exit(1)
    except KeyboardInterrupt:
        # in case of MFA the user can type CTRL-C instead of typing its code
        # just exit nicely
        sys.exit(0)
    except Exception:
        print("Unexpected error:", sys.exc_info()[0])
        raise

    for ins in response["Reservations"]:
        instance = ins["Instances"][0]
        instanceId = instance["InstanceId"]

        if "Tags" in instance:
            name = [k["Value"] for k in instance["Tags"] if k["Key"] == "Name"]
            if name == []:
                name = ""
            else:
                name = name[0]
        else:
            name = ""

        if "PublicIpAddress" in instance:
            publicAddress = instance["PublicIpAddress"]
        else:
            publicAddress = ""

        if "PrivateIpAddress" in instance:
            privateAddress = instance["PrivateIpAddress"]
        else:
            privateAddress = ""

        if "LaunchTime" in instance:
            launchtime = instance['LaunchTime'].strftime('%D %T')
        else:
            launchtime = ""

        entry = "%s - %s - %s - %s - %s " % (
            instanceId,
            "{:<15}".format(publicAddress),
            "{:<15}".format(privateAddress),
            "{:<17}".format(launchtime),
            name,
        )
        ec2_instances.append(entry)

    if args.name:
        r = re.compile(".* - .* - .* - .*" + args.name + ".*")
        ec2_instances = filter(r.match, ec2_instances)

    if args.instanceId:
        r = re.compile(".*" + args.instanceId + ".* - .* - .* - .*")
        ec2_instances = filter(r.match, ec2_instances)

    if args.address:
        r = re.compile(".* - .*" + args.address + ".* - .*")
        ec2_instances = filter(r.match, ec2_instances)

    return ec2_instances


def main():

    parser = argparse.ArgumentParser(
        description="AWS SSM console manager",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--region",
        "-r",
        default="eu-west-1",
        help="Region to retrieve instances from",
    )

    parser.add_argument(
        "--instanceId",
        "-i",
        required=False,
        help="Filter by instance id by applying .*arg.*",
    )

    parser.add_argument(
        "--name",
        "-n",
        required=False,
        help="Filter by instance name by applying .*arg.*",
    )

    parser.add_argument(
        "--address",
        "-a",
        required=False,
        help="IP address of the instance"
    )

    parser.add_argument(
        "--dryrun",
        "-d",
        action="store_true",
        required=False,
        help="Dry run, do not connec to the instance just list matchs"
    )

    args = parser.parse_args()
    instances = get_instances(args)

    if args.dryrun:
        print(json.dumps(instances, indent=4))
        return

    if len(instances) == 0:
        print(
            "Your search criteria did not match any running instance.\n"
            + "Exiting..."
        )
        sys.exit(1)

    prompt_list = [
        {
            "type": "list",
            "name": "instance",
            "message": "Select instance to connect",
            "choices": instances,
        }
    ]

    answers = prompt(prompt_list, style=custom_style_2)
    if answers:
        instanceId = answers["instance"].split(" - ")[0]
        os.execlp("aws", "aws", "ssm", "start-session", "--target", instanceId)


if __name__ == "__main__":
    main()
