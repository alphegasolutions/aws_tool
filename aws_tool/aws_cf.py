from datetime import datetime

from shutil import copyfile

import logging
import json
import os, sys, random, string

import boto3
import botocore

from .aws_session import AWSSession


FAILURE_TYPES = ['DO_NOTHING', 'ROLLBACK', 'DELETE']
CAPABILITIES = ["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM", "CAPABILITY_AUTO_EXPAND"]


class CFStackResult(object):

    def __init__(self, stack):

        self.stack_id = stack['StackId']
        self.stack_name = stack['StackName']
        self.creation_time = stack['CreationTime']
        self.stack_status = stack['StackStatus']

        if 'StackStatusReason' in stack.keys():
            self.status_description = stack['StackStatusReason']
        else:
            self.status_description = ''

        if 'LastUpdatedTime' in stack.keys():
            self.last_updated_time = stack['LastUpdatedTime']
        else:
            self.last_updated_time = self.creation_time

        self.outputs = {}
        if 'Outputs' in stack.keys():
            for output in stack['Outputs']:
                self.outputs[output['OutputKey']] = output['OutputValue']

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        data = {}
        data["stack_id"] = self.stack_id
        data["stack_name"] = self.stack_name
        data["creation_time"] = str(self.creation_time)
        data["stack_status"] = self.stack_status
        data["outputs"] = self.outputs

        return str(data)

    @staticmethod
    def print_list(stack_list):

        if stack_list is None or len(stack_list) == 0:
            print("No stacks available")
        else:
            for stack in stack_list:
                print(stack)


class CFStackTemplate(object):

    def __init__(self, stack_name, template_location, parameter_location=None):
        self.__stack_name = stack_name

        self.__template_body = load_file(template_location)
        if parameter_location is not None:
            self.__params = load_json_file(parameter_location)

        self.__capabilities = []
        self.__on_failure = "DELETE"
        self.__tags = []

    def set_parameter(self, key, value):
#        Found = False
        for param in self.__params:
            if param["ParameterKey"] == key:
                param["ParameterValue"] = value
                return

 #       if not Found:
        self.__params.append({"ParameterKey": key, "ParameterValue": value})

    def add_capability(self, capability):
        if capability not in CAPABILITIES:
            raise Exception("Invalid capability: {}".format(capability))

        if capability not in self.capabilities:
            self.__capabilities.append(capability)

    def set_failure_behavior(self, behavior):
        if behavior not in FAILURE_TYPES:
            raise Exception("Invalid behavior type for failure: {}".format(behavior))

        self.__on_failure = behavior

    def add_tag(self, key, value):
        for tag in self.__tags:
            if tag["Key"] == key:
                tag["Value"] = value
                return

        self.__tags.append({"Key": key, "Value": value})

    def __str__(self):
        return str({
            "Template Body: " : self.__template_body,
            "Parameters": self.__params,
            "capabilities": self.__capabilities,
            "on_failure": self.__on_failure,
            "tags": self.__tags
        })

    def __repr__(self):
        return self.__str__()

    @property
    def name(self):
        return self.__stack_name

    @property
    def has_parameters(self):
        return self.__template_body is not None

    @property
    def template_body(self):
        return self.__template_body

    @property
    def parameters(self):
        return self.__params

    @property
    def capabilities(self):
        return self.__capabilities

    @property
    def on_failure(self):
        return self.__on_failure

    @property
    def tags(self):
        return self.__tags


class CFStackTool(object):

    def __init__(self, session=AWSSession()):
        try:
            self.__cf = session.get_client("cloudformation")
        except Exception as ex:
            print(ex)
            raise ex

    def stack_exists(self, stack_name):
        return _cf_stack_exists(self.__cf, stack_name)

    def get_stack_list(self):
        stacks = _get_stack_list(self.__cf)
        return [CFStackResult(stack) for stack in stacks]

    def get_stack(self, stack_name):

        response = _get_stack_info(self.__cf, stack_name)
        print(response)
        for stack in response['Stacks']:
            if stack_name == stack['StackName']:
                return CFStackResult(stack)

        raise Exception("Stack with name {} not found".format(stack_name))

    def validate(self, stack=CFStackTemplate):

        response = self.__cf.validate_template(TemplateBody=stack.template_body)
#        print(response)

        parameters = []
        for param in response["Parameters"]:
            parameters.append({"ParameterKey": param["ParameterKey"], "ParameterValue": param["DefaultValue"]})

        capabilities = response["Capabilities"]

        for capability in capabilities:
            stack.add_capability(capability)

        #print(parameters)
        #print(capabilities)

        return parameters, capabilities

    def create_stack(self, stack=CFStackTemplate):

        self.__cf.validate_template(TemplateBody=stack.template_body)

        try:

            data = dict()
            data['StackName'] = stack.name
            data['TemplateBody'] = stack.template_body

            if stack.has_parameters:
                data['Parameters'] = stack.parameters
            data['Capabilities'] = stack.capabilities
            data['Tags'] = stack.tags

            if _cf_stack_exists(self.__cf, stack.name):
                stack_result = self.__cf.update_stack(**data)
                status_var = 'stack_update_complete'
            else:
                data['OnFailure'] = stack.on_failure
                stack_result = self.__cf.create_stack(**data)
                status_var = 'stack_create_complete'

            logging.info("Stack Result")
            logging.info(stack_result)

            waiter = self.__cf.get_waiter(status_var)
            logging.info('waiting for stack {} to be ready'.format(stack.name))

            waiter.wait(StackName=stack.name)

        except botocore.exceptions.ClientError as ex:
            error_message = ex.response['Error']['Message']

            if error_message == 'No updates are to be performed.':
                logging.info(error_message)

                stacks = self.__cf.describe_stacks(StackName=stack.name)
                logging.info(stacks)
                stack = stacks['Stacks'][0]

            else:
                logging.error(error_message)
                raise ex
        else:
            stacks = self.__cf.describe_stacks(StackName=stack_result['StackId'])
            logging.info(stacks)

            stack = stacks['Stacks'][0]
        finally:

            logging.info(stack)
            return CFStackResult(stack)

    def delete_stack(self, stack_name):
        _delete_cf_stack(self.__cf, stack_name)


def _parse_cf_template(cf, template):
    try:
        with open(template) as template_fileobj:
            template_data = template_fileobj.read()

        cf.validate_template(TemplateBody=template_data)
    except Exception as ex:
        raise ex
    else:
        return template_data


def _get_stack_list(cf):

    try:
        stacks = []
        paginator = cf.get_paginator('list_stacks')
        for page in paginator.paginate():

            for stack in page['StackSummaries']:
                if stack["StackStatus"] != "DELETE_COMPLETE":
                    stacks.append(stack)
    except Exception as ex:
        logging.error("Error while listing stacks: " + str(ex))
        raise ex
    else:
        return stacks


def _get_stack_info(cf, stack_name):
    try:
        response = cf.describe_stacks(StackName=stack_name)
        return response
#        cf_logger.info(response)

        info = {}
#        info['Outputs'] = {}

        # for stack in response['Stacks']:
        #     if stack_name == stack['StackName']:
        #         info['StackId'] = stack['StackId']
        #         info['StackName'] = stack['StackName']
        #         info['CreationTime'] = stack['CreationTime']
        #         # info['LastUpdatedTime'] = stack['LastUpdatedTime']
        #         info['StackStatus'] = stack['StackStatus']
        #
        #         outputs = info['Outputs']
        #         for output in stack['Outputs']:
        #             outputs[output['OutputKey']] = output['OutputValue']
        #
        #         return info

    except Exception as ex:
        logging.error("Error while describing stack: " + str(ex))
        raise ex
    else:
        raise Exception("Stack {} does not exist".format(stack_name))


def _cf_stack_exists(cf, stack_name):
    try:
        paginator = cf.get_paginator('list_stacks')
        for page in paginator.paginate():

            for stack in page['StackSummaries']:
                if stack['StackStatus'] == 'DELETE_COMPLETE':
                    continue
                if stack_name == stack['StackName']:
                    return True
        return False
    except Exception as ex:
        logging.error("Error while listing stacks: " + str(ex))
        raise ex


def _delete_cf_stack(cf, stack_name):
    try:
        cf.delete_stack(StackName=stack_name)
        waiter = cf.get_waiter('stack_delete_complete')
        logging.info('waiting for stack {} to be deleted'.format(stack_name))

        waiter.wait(StackName=stack_name)

    except Exception as ex:
        logging.error("Error while deleting stack: " + str(ex))
        raise ex


# def create_cf_stack_from_file(stack_name, template_file, parameters, capabilities=None):
#     data = {'StackName': stack_name}
#
#     template_body = parse_cf_template(template_file)
#     # parameters = load_json_file(params_file)
#
#     data['TemplateBody'] = template_body
#     data['Parameters'] = parameters
#
#     if capabilities is not None:
#         data['Capabilities'] = capabilities
#
#     try:
#
#         if cf_stack_exists(stack_name):
#             stack_result = cf.update_stack(**data)
#             status_var = 'stack_update_complete'
#         else:
#             data['OnFailure'] = ON_FAILURE
#             stack_result = cf.create_stack(**data)
#             status_var = 'stack_create_complete'
#
#         cf_logger.info("Stack Result")
#         cf_logger.info(stack_result)
#
#         waiter = cf.get_waiter(status_var)
#         cf_logger.info('waiting for stack {} to be ready'.format(stack_name))
#
#         waiter.wait(StackName=stack_name)
#
#     except botocore.exceptions.ClientError as ex:
#         error_message = ex.response['Error']['Message']
#
#         if error_message == 'No updates are to be performed.':
#             cf_logger.info(error_message)
#
#             stacks = cf.describe_stacks(StackName=stack_name)
#             cf_logger.info(stacks)
#             stack = stacks['Stacks'][0]
#
#         else:
#             cf_logger.error(error_message)
#             raise ex
#     else:
#         stacks = cf.describe_stacks(StackName=stack_result['StackId'])
#         cf_logger.info(stacks)
#
#         stack = stacks['Stacks'][0]
#     finally:
#         # data = json.dumps(
#         #    cf.describe_stacks(StackName=stack_result['StackId']),
#         #    indent=2,
#         #    default=json_serial
#         # )
#
#         cf_logger.info(stack)
#
#         output = {}
#         for item in stack['Outputs']:
#             output[item["OutputKey"]] = item["OutputValue"]
#
#         return output


# def create_cf_stack(stack_name, template_url, params_file, capabilities=None):
#     data = {'StackName': stack_name, 'TemplateURL': template_url}
#
#     parameters = load_json_file(params_file)
#     if capabilities is not None:
#         data['Capabilities'] = capabilities
#
#     try:
#
#         if stack_exists(stack_name):
#             stack_result = cf.update_stack(**data)
#             status_var = 'stack_update_complete'
#         else:
#             data['OnFailure'] = ON_FAILURE
#             stack_result = cf.create_stack(**data)
#             status_var = 'stack_create_complete'
#
#         cf_logger.info("Stack Result")
#         cf_logger.info(stack_result)
#
#         waiter = cf.get_waiter(status_var)
#         cf_logger.info('waiting for stack {} to be ready'.format(stack_name))
#
#         waiter.wait(StackName=stack_name)
#     except botocore.exceptions.ClientError as ex:
#         error_message = ex.response['Error']['Message']
#
#         if error_message == 'No updates are to be performed.':
#             cf_logger.info(error_message)
#         else:
#             cf_logger.error(error_message)
#             raise
#     else:
#         stacks = cf.describe_stacks(StackName=stack_result['StackId'])
#         cf_logger.info(stacks)
#
#         stack = stacks['Stacks'][0]
#
#         output = {}
#         for item in stack['Outputs']:
#             output[item["OutputKey"]] = item["OutputValue"]
#
#         return output



def load_file(file_path):
    try:
        with open(file_path) as fileobj:
            data = fileobj.read()

    except Exception as ex:
        logging.error("Error while loading json file: " + str(ex) )
        raise ex
    else:
        return data


def load_json_file(file_path):
    try:
        with open(file_path, "rb") as fileobj:
            data = json.load(fileobj)
    except Exception as ex:
        logging.error("Error while loading json file: " + str(ex) )
        raise ex
    else:
        return data


def save_json_file(file_path, contents):
    try:

        with open(file_path, "w", encoding='utf-8') as out_file:
            json.dump(contents, out_file, ensure_ascii=False, indent=4)

    except Exception as ex:
        logging.error("Error while saving json file: " + str(ex) )
        raise ex
