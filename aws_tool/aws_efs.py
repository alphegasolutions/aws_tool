import logging


def get_file_systems(efs, file_system_id=None):
    try:
        params = dict()
        if file_system_id is not None:
            params['FileSystemId'] = file_system_id

        response = efs.describe_file_systems(**params)
        logging.info(response)
        items = []

        if 'FileSystems' in response.keys():
            for file_system in response['FileSystems']:
                items.append(file_system['FileSystemId'])

    except Exception as ex:
        logging.error("Error while retrieving file systems: " + str(ex) )
        raise ex
    else:
        return items


def get_file_system(efs, file_system_id):
    try:
        response = efs.describe_file_systems(FileSystemId=file_system_id)

        if 'FileSystems' in response.keys():
            for file_system in response['FileSystems']:
                if file_system['FileSystemId'] == file_system_id:
                    return file_system
        else:
            return None

    except Exception as ex:
        logging.error("Error while retrieving file systems: " + str(ex) )
        raise ex


def delete_file_system(efs, file_system_id):
    try:
        efs.delete_file_system(FileSystemId=file_system_id)
    except Exception as ex:
        logging.error("Error while deleting file system: " + str(ex) )
        raise ex
