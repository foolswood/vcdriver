import copy
import functools
import getpass
import os
from six.moves import configparser, input


_config = {
    'Vsphere Session': {
        'vcdriver_host': '',
        'vcdriver_port': '443',
        'vcdriver_username': '',
        'vcdriver_password': ''
    },
    'Virtual Machine Deployment': {
        'vcdriver_resource_pool': '',
        'vcdriver_data_store': '',
        'vcdriver_data_store_threshold': '0',
        'vcdriver_folder': ''
    },
    'Virtual Machine Remote Management': {
        'vcdriver_vm_ssh_username': '',
        'vcdriver_vm_ssh_password': '',
        'vcdriver_vm_winrm_username': '',
        'vcdriver_vm_winrm_password': ''
    }
}

SECRETS = {
    'vcdriver_password',
    'vcdriver_vm_ssh_password',
    'vcdriver_vm_winrm_password'
}


def _get_input_function(key):
    if key in SECRETS:
        return getpass.getpass
    else:
        return input


def read():
    """
    Read the state of the config dictionary
    :return: A deep copy (Which acts as read only) of the config dictionary
    """
    global _config
    return copy.deepcopy(_config)


def load(path=None):
    """
    Will load the configuration from a INI file or the environment
    :param path: The configuration file path
    """
    global _config
    if path:
        config = configparser.RawConfigParser()
        config.read(path)
    for section_key, section_content in _config.items():
        for config_key in section_content.keys():
            if path:
                _config[section_key][config_key] = config.get(
                    section_key, config_key
                ) or os.getenv(config_key, '')
            else:
                _config[section_key][config_key] = os.getenv(config_key, '')


def configurable(section_keys):
    """
    Ensure that a configuration value is present in the kwargs or the config
    :param section_keys: An iterable of the required section-key pairs

    :return: The decorated function
    """
    global _config

    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            missing_keys = []
            for section, key in section_keys:
                if not kwargs.get(key, None):
                    config_section = _config.get(section)
                    if config_section:
                        config_value = config_section.get(key)
                    else:
                        config_value = None
                    if config_value:
                        kwargs[key] = config_value
                    else:
                        missing_keys.append(key)
            for key in missing_keys:
                kwargs[key] = _get_input_function(key)('{}: '.format(key))
            return function(*args, **kwargs)
        return wrapper
    return decorator
