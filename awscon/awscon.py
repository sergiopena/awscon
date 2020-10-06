import boto3
from botocore import credentials
import botocore.session
from botocore.exceptions import (
    ClientError,
    ProfileNotFound,
    NoRegionError,
    EndpointConnectionError,
)


import sys
import os
import argparse
import re
import json
from pyfzf.pyfzf import FzfPrompt

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
    except Exception:
        print("Unexpected error:", sys.exc_info()[0])
        raise

    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:

            instanceId = instance["InstanceId"]

            name = ""
            tags = instance.get("Tags")
            if tags:
                for name in (t["Value"] for t in tags if t["Key"] == "Name"):
                    pass

            publicAddress = instance.get("PublicIpAddress", "")

            privateAddress = instance.get("PrivateIpAddress", "")

            launchtime = instance.get("LaunchTime")
            if launchtime:
                launchtime = launchtime.strftime("%D %T")

            # Apply user filters, if any
            if args.name and args.name not in name:
                continue
            if (
                args.address
                and args.address not in publicAddress
                and args.address not in privateAddress
            ):
                continue
            if args.instanceId and args.instanceId not in instanceId:
                continue

            entry = "{} - {:<15} - {:<15} - {:<17} - {} ".format(
                instanceId, publicAddress, privateAddress, launchtime, name
            )
            ec2_instances.append(entry)

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

    if len(list(instances)) == 0:
        print(
            "Your search criteria did not match any running instance.\n"
            + "Exiting..."
        )
        sys.exit(1)

    fzf = FzfPrompt()
    option = fzf.prompt(instances)
    instanceId = option[0].split(" - ")[0]
    os.execlp("aws", "aws", "ssm", "start-session", "--target", instanceId)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit()
