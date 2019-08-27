import logging
import json
from .log_util import *


from .aws_session import AWSSession
from .aws_cf import CFStackTool, CFStackTemplate, CFStackResult
from .deploy_utils import AWSDeployTool

CREATE_IAM_ACTION = "create"
LIST_IAM_ACTION = "list"
DELETE_IAM_ACTION = "delete"
FIND_IAM_ACTION = "find"
ATTACH_IAM_ACTION = "attach"
IAM_ACTIONS = [CREATE_IAM_ACTION, LIST_IAM_ACTION, DELETE_IAM_ACTION, FIND_IAM_ACTION, ATTACH_IAM_ACTION]

log_name = "aws_tool.aws_iam"

logger = logging.getLogger(log_name)

iam = None


class AWSRole(object):

    def __init__(self, role):
        self.name = role['RoleName']
        self.id = role['RoleId']
        self.arn = role['Arn']

    def __str__(self):
        return str({
            "name": self.name,
            "id": self.name,
            "arn": self.arn
        })


class EKSRoleDeployer(object):

    global logger

    @staticmethod
    def get_role(role_name):
        return AWSRole(_get_iam_role(role_name))

    @staticmethod
    def init(session):
        global iam

        iam = session.get_client("iam")


def _get_iam_role(role_name):
    try:
        log_enter(log_name, "get_iam_role")
        response = iam.get_role(RoleName=role_name)

        if 'Role' in response.keys():
            return response['Role']

        return None
    except Exception as ex:
        raise ex

    finally:
        log_exit(log_name, "get_iam_role")


# def iam_actions(action):
#     import argparse
#
#     action = action.lower()
#     if action not in IAM_ACTIONS:
#         raise argparse.ArgumentTypeError("{} is not a valid eks cluster deployment action. Specify one of {}"
#                                          .formation(action, ','.join(IAM_ACTIONS)))
#     return action
#


# def create_iam_role(role_name, role_description, trust_policy, max_duration=3600, tags=[]):
#     try:
#         logger.debug("ENTER: aws_iam.create_role()")
#         response = iam.create_role(
#             Path="/",
#             RoleName=role_name,
#             AssumeRolePolicyDocument=json.dumps(trust_policy),
#             Description=role_description,
#             MaxSessionDuration=max_duration,
#             Tags=tags
#         )
#
#         print(response)
#
#         if 'Role' in response.keys():
#             return response['Role']
#         else:
#             raise Exception("unable to create role: {}".format(role_name))
#
#     except Exception as ex:
#
#         raise ex
#
#     finally:
#
#         logger.debug("EXIT: aws_iam.create_role()")


# def create_iam_policy(policy_name, policy_statement, policy_description):
#     try:
#         logger.debug("ENTER: aws_iam.create_policy()")
#         response = iam.create_policy(
#             PolicyName=policy_name,
#             Path="/",
#             PolicyDocument=json.dumps(policy_statement),
#             Description=policy_description
#         )
#
#         print(response)
#
#         if 'Policy' in response.keys():
#             return response['Policy']
#         else:
#             raise Exception("unable to create role: {}".format(policy_name))
#
#     except Exception as ex:
#         raise ex
#
#     finally:
#         logger.debug("EXIT: aws_iam.create_policy()")


# def attach_iam_role_policy(role_name, policy_arn):
#     try:
#         log_enter(log_name, "attach_iam_policy")
#         response = iam.attach_role_policy
#     except Exception as ex:
#         raise ex
#     finally:
#         log_exit(log_name, "attach_iam_policy")
