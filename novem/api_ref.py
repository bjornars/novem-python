import sys
import urllib.request
from typing import Dict

import requests

from .exceptions import Novem401, Novem404
from .types_ import Config, TokenResponse
from .version import __version__


def get_ua(is_cli: bool) -> Dict[str, str]:
    name = "NovemCli" if is_cli else "NovemLib"
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    return {
        "User-Agent": f"{name}/{__version__} Python/{py_version}",
    }


class NovemAPI:
    """
    Novem API class

    * Read config file
    * Communicate with api.novem.no
    """

    def __init__(self, config: Config) -> None:
        """ """
        self.session = requests.Session()
        self.session.headers.update(get_ua(config.is_cli))
        self.session.proxies = urllib.request.getproxies()

        if config.ignore_ssl_warn:
            # supress ssl warnings
            self.session.verify = False
            import urllib3

            urllib3.disable_warnings()

        self.root = config.api_root
        self.root = self.root.rstrip("/") + "/"

        if config.token:
            self.token = config.token
            self.session.auth = ("", self.token)
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
        r = self.session.post(
            f"{self.root}token",
            auth=None,
            json=params,
        )

        if not r.ok:
            resp = r.json()
            if r.status_code == 401:
                raise Novem401(resp["message"])
        token: TokenResponse = r.json()
        return token

    def delete(self, path: str) -> bool:

        r = self.session.delete(
            f"{self.root}{path}",
        )

        if not r.ok:
            resp = r.json()
            if r.status_code == 404:
                raise Novem404(resp["message"])
            else:
                print(r.json())

        return r.ok

    def read(self, path: str) -> str:

        r = self.session.get(
            f"{self.root}{path}",
        )

        if not r.ok:
            resp = r.json()
            if r.status_code == 404:
                raise Novem404(resp["message"])

        return r.text

    def write(self, path: str, value: str) -> None:

        r = self.session.post(
            f"{self.root}{path}",
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

        r = self.session.put(
            f"{self.root}{path}",
        )

        if not r.ok:
            resp = r.json()
            if r.status_code == 404:
                raise Novem404(resp["message"])
            else:
                print(r.json())
