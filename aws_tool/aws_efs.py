from datetime import datetime

from shutil import copyfile

import logging
import json
import os, sys, random, string

import boto3
import botocore


def get_file_systems(efs):
    try:
        response = efs.describe_file_systems()
        items = []

        for file_system in response['FileSystems']:
            items.append[file_system['FileSystemId']]

    except Exception as ex:
        logging.error("Error while retrieving file systems: " + str(ex) )
        raise ex
    else:
        return items


def get_file_system(efs, file_system_id):
    try:
        response = efs.describe_file_systems(FileSystemId=file_system_id)
        items = []

        for file_system in response['FileSystems']:
            if file_system['FileSystemId'] == file_system_id:
                return file_system

    except Exception as ex:
        logging.error("Error while retrieving file systems: " + str(ex) )
        raise ex


def delete_file_system(efs, file_system_id):
    try:
        efs.delete_file_system(FileSystemId=file_system_id)
    except Exception as ex:
        logging.error("Error while deleting file system: " + str(ex) )
        raise ex
