"""Expose modem functionality to programs that would normally require browser use.

This module contains all the various Modem implementations, as well as a factory function capable of
retrieving the correct class via model name."""
import requests
from nononesdefaultdict import NoNonesDefaultDict
from abc import ABCMeta, abstractmethod
import functools
import datetime

def get(model, configurations):
    if model == "TG1682G":
        return ModemTG1682G(configurations)
    raise UnknownModemModelError

class ModemMeta(ABCMeta):
    pass

class Modem(metaclass=ModemMeta):
    """Abstract base class for modems.

    :param
        configurations: Optional dictionary of settings related to the modem. Only looking for
                        'ip_address' in this superclass.

    :properties
        ip_address: IP address of registered modem

    :class-properties
        TIMEOUT_LIMIT: time limit (in seconds) to wait for a response from the server
    """
    TIMEOUT_LIMIT = 10.0

    def __init__(self, configurations={}):
        self.ip_address = configurations.get('ip_address')

    @property
    def ip_address(self):
        return self._ip_address

    @ip_address.setter
    def ip_address(self, ip_address):
        self._ip_address = ip_address


class AuthModem(Modem, metaclass=ModemMeta):
    """Abstract class that represents a modem that requires authentication to perform certain actions.

    :param
        configurations: optional dictionary, looking for 'username', 'password', 'ignore_cert' keys

    :methods
        login(username, password)
        authenticate()
        is_authenticated()

    :class-methods
        requires_authentication(method)

    :class-properties
        session
        credentials
    """
    def __init__(self, configurations={}):
        super().__init__(configurations)
        self.ignore_cert = configurations.get('ignore_cert') or False
        self.session = requests.Session()
        self.credentials = {'username': configurations.get('username'), 'password': configurations.get('password')}

    def __del__(self):
        self.session.close()

    def login(self, username='', password=''):
        """Update user login information and attempt to authenticate to the modem."""
        if self.credentials['username'] != username or self.credentials['password'] != password:
            self.session.close()
            self.session = requests.Session()
            self.credentials = {'username': username, 'password': password}
        self.authenticate()

    @property
    def session(self):
        """A Requests.Session object pertaining to the current user."""
        return self._session

    @session.setter
    def session(self, s):
        self._session = s

    @property
    def credentials(self):
        return self._credentials

    @credentials.setter
    def credentials(self, c):
        """A dictionary containing 'username' and 'password' keys, set to empty string by default."""
        self._credentials = NoNonesDefaultDict(lambda: '')
        for key, val in c.items():
            self._credentials[key] = val

    @abstractmethod
    def authenticate(self):
        """Authentication mechanics must be implemented by subclasses."""
        raise NotImplementedError

    @abstractmethod
    def is_authenticated(self):
        """Mechanics for detecting whether a user is already authenticated must be provided by subclasses.

        Recommended method for doing so is inspecting the self.session object for relevant cookies.

        :return True if authenticated, False otherwise"""
        raise NotImplementedError

    @classmethod
    def requires_authentication(cls, method):
        """A decorator used to wrap any subclass methods that need authentication to work properly."""
        @functools.wraps(method)
        def authenticated_method(self, *args, **kwargs):
            if not self.is_authenticated():
                self.authenticate()
            return method(self, *args, **kwargs)
        return authenticated_method

    @classmethod
    def refresh_cookie(cls, cookiename, expires_in_x):
        """A decorator for any action that needs to update the expiration time of a cookie.

        :parameter cookiename: string name of the cookie to update.
        :parameter expires_in_x: the number of seconds that this cookie lasts for
        """
        # Actually, since this decorator takes a parameter, it is a factory function that returns a decorator,
        # which in turn returns the wrapped function that handles expiration update
        def refresh_decorator(method):
            @functools.wraps(method)
            def refreshing_method(self, *args, **kwargs):
                result = method(self, *args, **kwargs)
                for c in self.session.cookies:
                    if c.name == cookiename:
                        c.expires = (datetime.datetime.now() + datetime.timedelta(seconds=expires_in_x)).isoformat()
                return result
            return refreshing_method
        return refresh_decorator


# Bind names locally for convenience
requires_authentication = AuthModem.requires_authentication
refresh_cookie = AuthModem.refresh_cookie


class ModemTG1682G(AuthModem):
    """An class representation of the TG1682 Modem, intended to pass commands on to the real thing."""

    # The amount of time (in seconds) that the server will keep the authentication cookie alive for.
    # No, it doesn't just set a cookie-expiry response to the browser, that would be trivial to mess with.
    INTERNAL_COOKIE_EXPIRY = 10 * 60
    AUTHCOOKIE_NAME = 'PHPSESSID'

    def authenticate(self):
        """Authenticate to modem using prior username and password"""
        # Construct an HTTPS POST request to the login page of the modem with session credentials
        url = 'https://'.join(self.ip_address).join("/check.php")
        response = self.session.post(url, data=self.credentials, timeout=ModemTG1682G.TIMEOUT_LIMIT,
                                     verify=not self.ignore_cert)
        if response.ok and not self.is_authenticated():
            raise InvalidCredentialsError()

    def is_authenticated(self):
        """Determine whether user is authenticated to modem by looking for valid PHPSESSID cookie."""
        for c in self.session.cookies:
            if c.name == self.AUTHCOOKIE_NAME and not c.is_expired():
                return True
        return False

    @refresh_cookie(AUTHCOOKIE_NAME, INTERNAL_COOKIE_EXPIRY)
    @requires_authentication
    def reboot(self):
        url = 'https://'.join(self.ip_address).join('/actionHandler/ajaxSet_mta_Line_Diagnostics.php')
        data = {'get_statusx': 'false', 'restore_reboot': 'true'}
        header = {'Referer': 'https://'.join(self.ip_address).join('/restore_reboot.php')}
        response = self.session.post(url, data, header=header, verify=not self.ignore_cert)

    @refresh_cookie(AUTHCOOKIE_NAME, INTERNAL_COOKIE_EXPIRY)
    @requires_authentication
    def reset_wifi(self):
        """TODO: Reset just the wifi module, not the whole modem."""
        pass

    @refresh_cookie(AUTHCOOKIE_NAME, INTERNAL_COOKIE_EXPIRY)
    @requires_authentication
    def get_page(self, page):
        url = "https://".join(self.ip_address).join("/").join(page)
        response = self.session.get(url, verify=not self.ignore_cert)
        return response

    @refresh_cookie(AUTHCOOKIE_NAME, INTERNAL_COOKIE_EXPIRY)
    @requires_authentication
    def migrate_channel(self):
        """TODO: Scan for less congested bands and set modem wifi to use those."""
        pass

# Helper error classes
class UnknownModemModelError(Exception):
    """Raised when attempting to find a modem that there is no known implementation for."""

class InvalidCredentialsError(Exception):
    """Raised when authentication failed with provided credentials. Bad username/password."""
    # TODO: Include the response object in the exception, so any logging services can include the full response data
    pass
