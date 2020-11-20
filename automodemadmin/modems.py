"""Expose modem functionality to programs that would normally require browser use.

This module contains all the various Modem implementations, as well as a factory function capable of
retrieving the correct class via model name."""
import requests
from abc import ABCMeta, abstractmethod
from collections import defaultdict


def get(model, ip_address):
    if model == "TG1682G":
        return _ModemTG1682G(ip_address)
    raise UnknownModemModelError


class UnknownModemModelError(Exception):
    """Raised when attempting to find a modem that there is no known implementation for."""
    pass


class _Modem(metaclass=ABCMeta):
    """Abstract base modem class.

    :param
        ip_address: The ip address of the modem. Supports IPv4 and IPv6.
    """
    def __init__(self, ip_address):
        self.ip_address = ip_address

    @property
    def ip_address(self):
        return self._ip_address

    @ip_address.setter
    def ip_address(self, ip_address):
        self._ip_address = ip_address

    def do_action(self, action):
        pass

    def get_page(self, webpage):
        pass


def requires_authorization(method):
    def wrapper(self, *args, **kwargs):
        if not self.auth_info['authenticated']:
            self.authenticate(self.auth_info['username'], self.auth_info['password'])
        return self.method(*args, **kwargs)
    return wrapper


class _AuthModem(_Modem, metaclass=ABCMeta):
    """Abstract class that represents a modem that requires authentication to perform certain actions.

    :param
        ip_address: The IP address of the modem as a string
        auth_info: A dictionary of relevant authentication information, with keys like 'username'
            or 'password'. Empty strings will be provided for each if none is specified.

    :methods
        login(username, password: A proxy for 'authenticate' method.

        authenticate(username, password): Abstract method to authenticate to the modem. Must be
            implemented by subclasses.
    """
    def __init__(self, ip_address, username, password):
        super().__init__(ip_address)
        self.auth_info = {'username': username, 'password': password}

    @property
    def auth_info(self):
        return self._auth_info

    @auth_info.setter
    def auth_info(self, auth_info):
        self._auth_info = self._auth_info or defaultdict(lambda: '')
        if auth_info:
            for key, val in auth_info.items():
                self._auth_info[key] = val

    def login(self, username, password):
        self.auth_info['username'] = username
        self.auth_info['password'] = password
        return self.authenticate()

    @abstractmethod
    def authenticate(self):
        raise NotImplementedError

class _ModemTG1682G(_AuthModem):
    def authenticate(self, username, password):
        pass

    @requires_authorization
    def reboot(self):
        pass
