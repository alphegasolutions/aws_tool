
import logging
from .aws_cf import CFStackTool
from .aws_session import AWSSession
from .deploy_utils import AWSDeployTool

CLUSTER_LOGS = ['api', 'audit', 'authenticator', 'controllerManager', 'scheduler']

session = None
eks = None
cf_tool = None


class EKSClusterDetail(object):

    def __init__(self, c_info):

        self.publicAccess = c_info['resourcesVpcConfig']['endpointPublicAccess']
        self.privateAccess = c_info['resourcesVpcConfig']['endpointPrivateAccess']
        self.version = c_info['version']
        self.platformVersion = c_info['platformVersion']
        self.status = c_info['status']
        self.certificateAuthority = c_info['certificateAuthority']

        clusterLogging = c_info['logging']['clusterLogging'][0]
        self.loggingEnabled = clusterLogging['enabled']
        self.logTypes = clusterLogging['types']


class EKSClusterDeployer(object):

    logger = logging.getLogger("aws_tool.EKSClusterDeployer")

    CREATE = "create"
    LIST = "list"
    DELETE = "delete"
    FIND = "find"
    UPDATE = "update"
    UPGRADE = "upgrade"
    ROLES = "roles"
    ACTIONS = [CREATE, LIST, DELETE, FIND, UPGRADE, ROLES]
    VERSIONS = ['1.11', '1.12', '1.13']

    @staticmethod
    def create_cluster(stack, vpc_stack_name):
        try:

            if not cf_tool.stack_exists(vpc_stack_name):
                raise Exception("VPC stack: {} does not exist".format(vpc_stack_name))

            vpc_info = cf_tool.get_stack(vpc_stack_name)

            stack.set_parameter("VpcId", vpc_info.outputs["VpcId"])
            stack.set_parameter("SubnetIds", vpc_info.outputs["SubnetIds"])

            logging.info("EKS Parameters: " + str(stack.parameters))

            cf_tool.validate(stack)

            result = cf_tool.create_stack(stack)

            cluster_name = result.outputs['ControlPlane']
            cluster_detail = get_eks_detail(cluster_name=cluster_name)

            if not cluster_detail.privateAccess:
                set_eks_access(cluster_name=cluster_name, private_access=True)

            if not cluster_detail.loggingEnabled:
                set_eks_cluster_logging(cluster_name=cluster_name, cluster_logging=True, cluster_logs=CLUSTER_LOGS)

            return result

        except Exception as ex:
            logging.info("Error while creating Cluster: " + str(ex) )
            raise ex

    @staticmethod
    def list_clusters():
        stack_list = cf_tool.get_stack_list()
        stack_list = [stack for stack in stack_list if '-eks-' in stack.stack_name]
        AWSDeployTool.print_stack_summary(stack_list)

    @staticmethod
    def find_cluster(stack_name):
        stack = cf_tool.get_stack(stack_name)
        AWSDeployTool.print_stack_detail(stack)

    @staticmethod
    def delete_cluster(stack_name):
        cf_tool.delete_stack(stack_name)

    @staticmethod
    def set_arg_options(parser):
        parser.add_argument("--action", help='action type', default="create", type=eks_cluster_actions)
        parser.add_argument("--cluster-version", help="EKS Cluster version", default="1.12", type=eks_cluster_version)
        parser.add_argument("--vpc-stack", help="Name of the vpc stack to deploy EKS cluster")
#        parser.add_argument("--private-access", help="setting for private access to cluster")
#        parser.add_argument("--public-access", help="setting for public access to cluster")
#        parser.add_argument("--cluster-logging", help="list of logs to enable")

        EKSClusterDeployer.logger.info("setting session argument options")
        AWSSession.set_arg_options(parser)

        EKSClusterDeployer.logger.info("setting deploy tool argument options")
        AWSDeployTool.set_arg_options(parser)

    @staticmethod
    def set_stack_options(options, cf_stack):

        if options.action == EKSClusterDeployer.CREATE:

            cf_stack.set_parameter("ClusterVersion", options.cluster_version)
            cf_stack.add_tag("environment", options.environment)
            cf_stack.add_tag("resource-type", "eks-cluster")
            cf_stack.add_tag("vpc-stack", options.vpc_stack)

    @staticmethod
    def get_stack_name(options):
        return AWSDeployTool.get_stack_name(options, "eks")


    @staticmethod
    def update_cluster(options):


        print()

    @staticmethod
    def init(options):

        global session, cf_tool, eks

        session = AWSDeployTool.create_session(options)
        cf_tool = CFStackTool(session)
        eks = session.get_client("eks")


class EKSBastionDeployer(object):

    logger = logging.getLogger("aws_tool.EKSBastionDeployer")

    CREATE = "create"
    LIST = "list"
    DELETE = "delete"
    FIND = "find"
    ACTIONS = [CREATE, LIST, DELETE, FIND]

    @staticmethod
    def create_instance(stack, vpc_stack_name, eks_stack_name):

        if not cf_tool.stack_exists(vpc_stack_name):
            raise Exception("VPC stack: {} does not exist".format(vpc_stack_name))

        if not cf_tool.stack_exists(eks_stack_name):
            raise Exception("EKS stack: {} does not exist".format(eks_stack_name))

        vpc_info = cf_tool.get_stack(vpc_stack_name)
        eks_info = cf_tool.get_stack(eks_stack_name)

        cf_tool.validate(stack)

        stack.set_parameter("VpcId", vpc_info.outputs["VpcId"])
        stack.set_parameter("SubnetIds", vpc_info.outputs["PublicSubnetIds"])
        stack.set_parameter("ControlPlane", eks_info.outputs["ControlPlane"])
        stack.set_parameter("BastionRole", eks_info.outputs["BastionRole"])
        stack.set_parameter("BastionSecurityGroup", eks_info.outputs["BastionSecurityGroup"])

        cf_tool.create_stack(stack)

    @staticmethod
    def list_instances():
        stack_list = cf_tool.get_stack_list()
        stack_list = [stack for stack in stack_list if '-bastion-' in stack.stack_name]
        AWSDeployTool.print_stack_summary(stack_list)

    @staticmethod
    def find_instance(stack_name):
        stack = cf_tool.get_stack(stack_name)
        AWSDeployTool.print_stack_detail(stack)

    @staticmethod
    def delete_instance(stack_name):
        cf_tool.delete_stack(stack_name)

    @staticmethod
    def set_arg_options(parser):
        parser.add_argument("--action", help='action type', default="create", type=eks_bastion_actions)
        parser.add_argument("--vpc-stack", help="Name of the vpc stack to deploy EKS Worker node instances")
        parser.add_argument("--eks-stack", help="Name of the eks cluster stack for the EKS Bastion instances")
        parser.add_argument("--key-pair", help="Name of the key pair for the bastion instance")

        EKSBastionDeployer.logger.info("setting session argument options")
        AWSSession.set_arg_options(parser)

        EKSBastionDeployer.logger.info("setting deploy tool argument options")
        AWSDeployTool.set_arg_options(parser)

    @staticmethod
    def set_stack_options(options, cf_stack):

        if options.action == EKSBastionDeployer.CREATE:
            if options.key_pair is not None:
                cf_stack.set_parameter("KeyPairName", options.key_pair)
            cf_stack.add_tag("environment", options.environment)
            cf_stack.add_tag("resource-type", "eks-bastion")

            cf_stack.add_tag("vpc-stack", options.vpc_stack)
            cf_stack.add_tag("eks-stack", options.eks_stack)

    @staticmethod
    def get_stack_name(options):
        return AWSDeployTool.get_stack_name(options, "bastion")


class EKSWorkerNodeDeployer(object):

    logger = logging.getLogger("aws_tool.EKSWorkerNodeDeployer")

    CREATE = "create"
    LIST = "list"
    DELETE = "delete"
    FIND = "find"
    ACTIONS = [CREATE, LIST, DELETE, FIND]

    @staticmethod
    def create_node(stack, vpc_stack_name, eks_stack_name):

        if not cf_tool.stack_exists(vpc_stack_name):
            raise Exception("VPC stack: {} does not exist".format(vpc_stack_name))

        if not cf_tool.stack_exists(eks_stack_name):
            raise Exception("EKS stack: {} does not exist".format(eks_stack_name))

        vpc_info = cf_tool.get_stack(vpc_stack_name)
        eks_info = cf_tool.get_stack(eks_stack_name)

        cf_tool.validate(stack)

        stack.set_parameter("VpcId", vpc_info.outputs["VpcId"])
        stack.set_parameter("SubnetIds", vpc_info.outputs["PrivateSubnetIds"])
        stack.set_parameter("ControlPlane", eks_info.outputs["ControlPlane"])
        stack.set_parameter("NodeRole", eks_info.outputs["NodeRole"])
        stack.set_parameter("ControlPlaneSecurityGroup", eks_info.outputs["ControlPlaneSecurityGroup"])
        stack.set_parameter("NodeSecurityGroup", eks_info.outputs["NodeSecurityGroup"])

        print(stack.parameters)
        return cf_tool.create_stack(stack)

    @staticmethod
    def list_nodes():
        stack_list = cf_tool.get_stack_list()
        stack_list = [stack for stack in stack_list if '-nodes-' in stack.stack_name]
        AWSDeployTool.print_stack_summary(stack_list)

    @staticmethod
    def find_node(stack_name):
        stack = cf_tool.get_stack(stack_name)
        AWSDeployTool.print_stack_detail(stack)

    @staticmethod
    def delete_node(stack_name):
        cf_tool.delete_stack(stack_name)

    @staticmethod
    def set_arg_options(parser):
        parser.add_argument("--action", help='action type', default="create", type=eks_nodes_actions)
        parser.add_argument("--cluster-version", help="EKS Cluster version", default="1.12", type=eks_cluster_version)
        parser.add_argument("--vpc-stack", help="Name of the vpc stack to deploy EKS Worker node instances")
        parser.add_argument("--eks-stack", help="Name of the eks cluster stack for the EKS Bastion instances")
        parser.add_argument("--key-pair", help="Name of the key pair for the bastion instance")

        EKSWorkerNodeDeployer.logger.info("setting session argument options")
        AWSSession.set_arg_options(parser)

        EKSWorkerNodeDeployer.logger.info("setting deploy tool argument options")
        AWSDeployTool.set_arg_options(parser)

    @staticmethod
    def set_stack_options(options, cf_stack):

        if options.action == EKSWorkerNodeDeployer.CREATE:
            if options.key_pair is not None:
                cf_stack.set_parameter("KeyPairName", options.key_pair)
            cf_stack.set_parameter("ClusterVersion", options.cluster_version)
            cf_stack.add_tag("environment", options.environment)
            cf_stack.add_tag("resource-type", "eks-node")

            cf_stack.add_tag("vpc-stack", options.vpc_stack)
            cf_stack.add_tag("eks-stack", options.eks_stack)

    @staticmethod
    def get_stack_name(options):
        return AWSDeployTool.get_stack_name(options, "nodes")


def eks_cluster_actions(action):
    import argparse

    action = action.lower()
    if action not in EKSClusterDeployer.ACTIONS:
        raise argparse.ArgumentTypeError("{} is not a valid eks cluster deployment action. Specify one of {}".formation(action, ','.join(EKSClusterDeployer.ACTIONS)))
    return action


def eks_cluster_version(version):
    import argparse

    if version not in EKSClusterDeployer.VERSIONS:
        raise argparse.ArgumentTypeError("{} is not a valid eks cluster version. Specify one of {}".formation(version, ','.join(EKSClusterDeployer.VERSIONS)))
    return version


def eks_bastion_actions(action):
    import argparse

    action = action.lower()
    if action not in EKSBastionDeployer.ACTIONS:
        raise argparse.ArgumentTypeError("{} is not a valid eks cluster deployment action. Specify one of {}".formation(action, ','.join(EKSBastionDeployer.ACTIONS)))
    return action


def eks_nodes_actions(action):
    import argparse

    action = action.lower()
    if action not in EKSWorkerNodeDeployer.ACTIONS:
        raise argparse.ArgumentTypeError("{} is not a valid eks cluster deployment action. Specify one of {}".formation(action, ','.join(EKSWorkerNodeDeployer.ACTIONS)))
    return action


def wait_for_cluster_active(eks, cluster_name):

    try:
        logger = logging.getLogger("aws_tool.aws_eks_cluster")
        waiter = eks.get_waiter('cluster_active')
        logger.info('waiting for cluster {} to become active'.format(cluster_name))
        waiter.wait(cluster_name)

        logger.info('cluster {} update completed'.format(cluster_name))
    except Exception as ex:
        logger.error(ex)
        raise ex


def set_eks_access(cluster_name, private_access=False, public_access=True):

    try:
        # check status before updating

        logger = logging.getLogger("aws_tool.aws_eks_cluster")
        logger.info("setting private access to {} and public access to {} for EKS cluster {}".format(private_access,
                                                                                             public_access, cluster_name))

        result = eks.update_cluster_config(name=cluster_name,
                                           resourcesVpcConfig={'endpointPrivateAccess': private_access,
                                                               'endpointPublicAccess': public_access})
        logger.info(result)
        c_info = result['update']
        status = c_info['status']

        if status == 'Failed':
            raise Exception("Attempt to update cluster access failed!")

        waiter = eks.get_waiter('cluster_active')
        logger.info('waiting for cluster {} to become active'.format(cluster_name))
        waiter.wait(cluster_name)
        logger.info('cluster {} update completed'.format(cluster_name))

    except Exception as ex:
        logger.error(ex)
        raise ex


def set_eks_cluster_logging(cluster_name, cluster_logging=True, cluster_logs=CLUSTER_LOGS):

    try:
        logger = logging.getLogger("aws_tool.aws_eks_cluster")
        logger.info("updating Log configuration for EKS cluster {}: logging={}, types={}".format(cluster_name,
                                                                                                 cluster_logging,
                                                                                                 cluster_logs))

        result = eks.update_cluster_config(name=cluster_name, logging={
            'clusterLogging': [{'enabled': cluster_logging, 'types': cluster_logs}]})

        logger.info(result)
        c_info = result['update']
        status = c_info['status']

        if status == 'Failed':
            raise Exception("Attempt to update cluster logging failed!")

        waiter = eks.get_waiter('cluster_active')
        logger.info('waiting for cluster {} to become active'.format(cluster_name))
        waiter.wait(cluster_name)
        logger.info('cluster {} update completed'.format(cluster_name))

    except Exception as ex:
        logger.error(ex)
        raise ex


def get_eks_detail(cluster_name):

    try:
        logger = logging.getLogger("aws_tool.aws_eks_cluster")
        result = eks.describe_cluster(name=cluster_name)
        logger.info(result)
        c_info = result['cluster']

        return EKSClusterDetail(c_info)

    except Exception as ex:
        logger.error(ex)
        raise ex


def create_aws_auth_cm(node_role, roles, users):

    auth_cfg = dict()
    auth_cfg['metadata'] = dict()
    auth_cfg['data'] = dict()

    auth_cfg['apiVersion'] = 'v1'
    auth_cfg['kind'] = 'ConfigMap'

    auth_cfg['metadata']['name'] = 'aws-auth'
    auth_cfg['metadata']['namespace'] = 'kube-system'

    auth_cfg['data']['mapRoles'] = []
    auth_cfg['data']['mapRoles'].append({'rolearn': '',
                                         'username': 'system:node:{{EC2PrivateDNSName}}'})

    auth_cfg['data']['mapRoles'].append( __create_entity('rolearn', node_role, 'system:node{{EC2PrivateDNSName}}'), ['bootstrappers', 'nodes'])

    if len(roles) > 0:
        for role in roles.items():
            auth_cfg['data']['mapUsers'].append( __create_entity('userarn', role[0], role[1], ['masters']) )

    if len(users) > 0:
        auth_cfg['data']['mapUsers'] = []
        for user in users.items():
            auth_cfg['data']['mapUsers'].append( __create_entity('userarn', user[0], user[1], ['masters']) )

    return auth_cfg


def __create_entity(arn_type, arn, username, groups):

    e = dict()
    e[arn_type] = arn
    e['username'] = username
    e['groups'] = []

    for group in groups:
        e['groups'].append({'system': group})

    return e