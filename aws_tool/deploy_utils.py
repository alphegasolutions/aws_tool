
from .aws_session import AWSSession
from .aws_cf import CFStackTool


class AWSDeployTool(object):

    @staticmethod
    def set_arg_options(parser):
        parser.add_argument("--project", help="Project Name", default="zcash")
        parser.add_argument("--name", help='Stack Name')
        parser.add_argument("--environment", help="Deployment Environment", default="test")
        parser.add_argument("--artifact-location", help="Location of template files", default="templates")


    @staticmethod
    def get_stack_name(options, deploy_type):
        if options.name is None or not options.name:
            return "{}-{}-{}".format(options.project, deploy_type, options.environment)
        else:
            return options.name

    @staticmethod
    def create_session(options):
        return AWSSession.create_aws_session(options)

    @staticmethod
    def create_cf_tool(options):
        aws_session = AWSSession.create_aws_session(options)
        return CFStackTool(aws_session)

    @staticmethod
    def print_stack_summary(stack_list):

        if len(stack_list) == 0:
            print("No resources found!")
        else:
            print('{:20s} | {:20s}'.format('Stack Name', 'Stack Status'))
            for stack in stack_list:
                print('{:20s} | {:20s}'.format(stack.stack_name, stack.stack_status))

    @staticmethod
    def print_stack_detail(stack_info):
        if stack_info is None:
            print("No resources found!")
        else:
            print("{:20s} : {:20s}".format("Stack Name", stack_info.stack_name))
            print("{:20s} : {:20s}".format("Stack Status", stack_info.stack_status))
            for output in stack_info.outputs.items():
                print("{:20s} : {:20s}".format(output[0], output[1]) )
