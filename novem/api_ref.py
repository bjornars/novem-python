import sys
import urllib.request
from typing import Dict

import requests

from novem.types import Config, TokenResponse

from .version import __version__


def get_ua(is_cli: bool) -> Dict[str, str]:
    name = "NovemCli" if is_cli else "NovemLib"
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    return {
        "User-Agent": f"{name}/{__version__} Python/{py_version}",
    }


class NovemException(Exception):
    pass


class Novem404(NovemException):
    def __init__(self, message: str):

        # 404 errors can occur if users are not authenticated, let them know
        # future improvement: consider requesting a fixed endpoint (like
        # whoami) and notify if not authenticated
        message = f"Resource not found: {message} (Are you authenticated?)"

        super().__init__(message)


class Novem403(NovemException):
    pass


class Novem401(NovemException):
    pass


class NovemAPI:
    """
    Novem API class

    * Read config file
    * Communicate with api.novem.no
    """

    def __init__(self, config: Config) -> None:
        """ """
        self._session = requests.Session()
        self._session.headers.update(get_ua(config.is_cli))
        self._session.proxies = urllib.request.getproxies()

        if config.ignore_ssl_warn:
            # supress ssl warnings
            self._session.verify = False
            import urllib3

            urllib3.disable_warnings()

        self._api_root = config.api_root
        self._api_root = self._api_root.rstrip("/") + "/"

        if config.token:
            self.token = config.token
            self._session.auth = ("", self.token)
        else:
            print(
                """\
Novem config file is missing.  Either specify config file location with
the config_path parameter, or setup a new token using
$ python -m novem --init
"""
            )
            sys.exit(0)


    def create_token(self, params: Dict[str, str]) -> TokenResponse:
        r = self._session.post(
            f"{self._api_root}token",
            auth=None,
            json=params,
        )

        if not r.ok:
            resp = r.json()
            if r.status_code == 401:
                raise Novem401(resp["message"])
        resp: TokenResponse = r.json()
        return resp

    def delete(self, path: str) -> bool:

        r = self._session.delete(
            f"{self._api_root}{path}",
        )

        if not r.ok:
            resp = r.json()
            if r.status_code == 404:
                raise Novem404(resp["message"])
            else:
                print(r.json())

        return r.ok

    def read(self, path: str) -> str:

        r = self._session.get(
            f"{self._api_root}{path}",
        )

        if not r.ok:
            resp = r.json()
            if r.status_code == 404:
                raise Novem404(resp["message"])

        return r.text

    def write(self, path: str, value: str) -> None:

        r = self._session.post(
            f"{self._api_root}{path}",
            headers={
                "Content-type": "text/plain",
            },
            data=value.encode("utf-8"),
        )

        if not r.ok:
            resp = r.json()
            if r.status_code == 404:
                raise Novem404(resp["message"])
            else:
                print(r.json())

    def create(self, path: str) -> None:

        r = self._session.put(
            f"{self._api_root}{path}",
        )

        if not r.ok:
            resp = r.json()
            if r.status_code == 404:
                raise Novem404(resp["message"])
            else:
                print(r.json())
