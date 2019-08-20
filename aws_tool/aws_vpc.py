from datetime import datetime

from shutil import copyfile

import logging
import json
import os, sys, random, string

import boto3
import botocore

from .aws_session import AWSSession

from .aws_cf import CFStackTool, CFStackResult, CFStackTemplate
from .aws_efs import *


class VPCDeployer(object):

    @staticmethod
    def create(stack, cf_tool=CFStackTool()):

        try:
            stack.add_capability("CAPABILITY_NAMED_IAM")
            return cf_tool.create_stack(stack)
        except Exception as ex:
            raise ex

    @staticmethod
    def list(cf_tool=CFStackTool()):
        print()

    @staticmethod
    def delete(stack_name, cf_tool=CFStackTool()):

        try:
#            stack_result = cf_tool.get_stack(stack_name)
            cf_tool.delete_stack(stack_name)

#            if "EFSId" in stack_result.outputs:
#                delete_file_system(stack_result.outputs["EFSId"])

        except Exception as ex:
            raise ex
