
import logging

from .aws_cf import CFStackTool, CFStackResult, CFStackTemplate
from .aws_efs import *
from .aws_iam import EKSRoleDeployer
from .deploy_utils import AWSDeployTool
from .aws_session import AWSSession

session = None
efs = None
cf_tool = None


class VPCDeployer(object):

    logger = logging.getLogger("aws_tool.VPCDeployer")

    CREATE = "create"
    LIST = "list"
    DELETE = "delete"
    GET = "get"
    FIND = "find"
    ACTIONS = [CREATE, LIST, DELETE, FIND, GET]

    @staticmethod
    def create_vpc(stack):

        try:
            VPCDeployer.logger.info("Parameters: " + str(stack.parameters) )
            cf_tool.validate(stack)
            return cf_tool.create_stack(stack)
        except Exception as ex:
            raise ex

    @staticmethod
    def list_vpc():
        stack_list = cf_tool.get_stack_list()
        stack_list = [stack for stack in stack_list if '-vpc-' in stack.stack_name]
        AWSDeployTool.print_stack_summary(stack_list)

    @staticmethod
    def find_vpc(stack_name):
        stack = cf_tool.get_stack(stack_name)
        AWSDeployTool.print_stack_detail(stack)

    @staticmethod
    def delete_vpc(stack_name):

        try:
            cf_tool.delete_stack(stack_name)
        except Exception as ex:
            raise ex

    @staticmethod
    def set_arg_options(parser):

        parser.add_argument("--action", help='vpc action type', default=VPCDeployer.CREATE, type=vpc_actions)
        parser.add_argument("--file-system-id", help="Existing EFS File system ID")
        parser.add_argument("--find-file-system", help="Use pre-existing file system if available", default="true", type=str2bool)

        VPCDeployer.logger.info("setting session argument options")
        AWSSession.set_arg_options(parser)
        print(parser)

        VPCDeployer.logger.info("setting deploy tool argument options")
        AWSDeployTool.set_arg_options(parser)
        print(parser)

    @staticmethod
    def set_stack_options(options, cf_stack):

        if options.action == VPCDeployer.CREATE:
            #if options.file_system_id is not None:
            #    cf_stack.set_parameter("fileSystemID", options.file_system_id)

            if options.find_file_system:
                VPCDeployer.logger.info("Searching for existing EFS file systems!")
                file_systems = get_file_systems(efs, options.file_system_id)
                if len(file_systems) > 0:
                    VPCDeployer.logger.info("Using existing File system: " + file_systems[0])
                    cf_stack.set_parameter("fileSystemID", file_systems[0])

            cf_stack.add_tag("environment", options.environment)
            cf_stack.add_tag("resource-type", "vpc")

    @staticmethod
    def get_stack_name(options):
        return AWSDeployTool.get_stack_name(options, "vpc")

    @staticmethod
    def create_cf_tool(options):
        return AWSDeployTool.create_cf_tool(options)

    @staticmethod
    def init(options):

        global session, cf_tool, efs

        session = AWSDeployTool.create_session(options)
        cf_tool = CFStackTool(session)
        efs = session.get_client("efs")


def vpc_actions(action):
    import argparse

    action = action.lower()
    if action not in VPCDeployer.ACTIONS:
        raise argparse.ArgumentTypeError("{} is not a valid vpc action. Specify one of {}".formation(action, ','.join(VPCDeployer.ACTIONS)))
    return action


def str2bool(v):
    if isinstance(v, bool):
        return v

    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True

    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        import argparse
        raise argparse.ArgumentTypeError('Boolean value expected.')
