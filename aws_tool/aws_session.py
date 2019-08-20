from datetime import datetime

from shutil import copyfile

import logging
import json
import os, sys, random, string

import boto3
import botocore


class AWSSession(object):

    def __init__(self, profile_name=None, access_key=None, secret_access_key=None, role_arn=None):

        if profile_name is not None:
            self.__session = boto3.Session(profile_name=profile_name)

        elif access_key is not None:
            self.__session = boto3.Session(aws_access_key_id=access_key, aws_secret_access_key=secret_access_key)

        elif role_arn is not None:
            session = boto3.Session()
            sts = session.client("sts")
            response = sts.assume_role(RoleArn=role_arn, RoleSessionName="resource")

            self.__session = boto3.Session(aws_access_key_id=response['Credentials']['AccessKeyId'],
                              aws_secret_access_key=response['Credentials']['SecretAccessKey'],
                              aws_session_token=response['Credentials']['SessionToken'])
        else:
            self.__session = boto3.Session()

    def get_available_services(self):
        return self.__session.get_available_services()

    def get_available_resources(self):
        return self.__session.get_available_resources()

    def get_client(self, client_name):
        return self.__session.client(client_name)

    def get_resource(self, resource_name):
        return self.__session.get_resource(resource_name)

    @staticmethod
    def add_session_params(parser):

        parser.add_argument("--region", help="AWS Region")
        parser.add_argument("--profile", help="AWS session profile")
        parser.add_argument("--role-arn", help="AWS role to assume")
        parser.add_argument("--access-key", help="AWS access key")
        parser.add_argument("--secret-access-key", help="AWS secret key")


