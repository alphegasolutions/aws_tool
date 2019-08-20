from datetime import datetime

from shutil import copyfile

import logging
import json
import os, sys, random, string

import boto3
import botocore

from .aws_session import AWSSession
from .aws_cf import CFStackTool


class EKSClusterDeployer(object):

    @staticmethod
    def create(stack, vpc_stack_name, cf_tool=CFStackTool()):
        try:

            if not cf_tool.stack_exists(vpc_stack_name):
                raise Exception("VPC stack: {} does not exist".format(vpc_stack_name))

            vpc_info = cf_tool.get_stack(vpc_stack_name)

            stack.set_parameter("VpcId", vpc_info.outputs["VpcId"])
            stack.set_parameter("SubnetIds", vpc_info.outputs["SubnetIds"])

            return cf_tool.create_stack(stack)
        except Exception as ex:
            raise ex


    @staticmethod
    def list(cf_tool):

        print()

    @staticmethod
    def delete(stack_name, cf_tool):
        cf_tool.delete_stack(stack_name)


class EKSBastionDeployer(object):

    @staticmethod
    def create(stack, vpc_stack_name, eks_stack_name, cf_tool=CFStackTool()):

        if not cf_tool.stack_exists(vpc_stack_name):
            raise Exception("VPC stack: {} does not exist".format(vpc_stack_name))

        if not cf_tool.stack_exists(eks_stack_name):
            raise Exception("EKS stack: {} does not exist".format(eks_stack_name))

        vpc_info = cf_tool.get_stack(vpc_stack_name)
        eks_info = cf_tool.get_stack(eks_stack_name)

        stack.set_parameter("VpcId", vpc_info.outputs["VpcId"])
        stack.set_parameter("SubnetIds", vpc_info.outputs["SubnetIds"])
        stack.set_parameter("ControlPlane", eks_info.outputs[""])
        stack.set_parameter("BastionRole", eks_info.outputs[""])
        stack.set_parameter("BastionSecurityGroup", eks_info.outputs[""])

        cf_tool.create_stack(stack)

    @staticmethod
    def list(cf_tool):
        print()

    @staticmethod
    def delete(stack_name, cf_tool):
        cf_tool.delete_stack(stack_name)


class EKSWorkerNodeDeployer(object):

    @staticmethod
    def create(stack_name, vpc_stack_name, eks_stack_name, cf_tool=CFStackTool()):

        if not cf_tool.stack_exists(vpc_stack_name):
            raise Exception("VPC stack: {} does not exist".format(vpc_stack_name))

        if not cf_tool.stack_exists(eks_stack_name):
            raise Exception("EKS stack: {} does not exist".format(eks_stack_name))

    @staticmethod
    def list(scf_tool):
        print()

    @staticmethod
    def delete(stack_name, cf_tool):
        cf_tool.delete_stack(stack_name)