import logging, logging.config, os, yaml
import pkgutil


def log_enter(name, func):
    logger = logging.getLogger(name)
    logger.debug("ENTER: {}.{}".format(name,func))


def log_exit(name, func):
    logger = logging.getLogger(name)
    logger.debug("EXIT: {}.{}".format(name,func))


try:

    log_dir = "/tmp/aws-tool"
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except Exception:
            raise OSError("can't create destination directory {}!".format(log_dir))

    log_config = yaml.safe_load(pkgutil.get_data(__package__, 'logging.yaml').decode('utf-8'))
    logging.config.dictConfig(log_config)
except Exception as ex:
    print(ex)
    print('Error in Logging Configuration. Using default configs')
    logging.basicConfig(level=logging.DEBUG)


