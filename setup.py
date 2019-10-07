import os
import setuptools


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setuptools.setup(
    name="awscon",
    version="0.0.8",
    author="Sergio Pena",
    author_email="isergiopena@gmail.com",
    description=("Wrapper that displays all available EC2 instances " +
                 "and launchs an SSM console session for the selected one"),
    license="BSD",
    keywords="aws ec2 ssm console ssh",
    url="https://www.github.com/sergiopena/awscon",
    packages=setuptools.find_packages(),
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    entry_points={
        'console_scripts': [
            'awscon = awscon.awscon:main'
        ]
    },
    install_requires=[
        'boto3>=1.9.154',
        'botocore>=1.12.154',
        'PyInquirer>=1.0.3'
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
)
