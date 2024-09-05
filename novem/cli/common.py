from abc import abstractmethod
import os
import sys
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

from novem import Mail as ApiMail, Plot as ApiPlot
from novem.api_ref import Novem404, NovemAPI
from novem.cli.editor import edit
from novem.cli.setup import Share
from novem.cli.vis import list_vis, list_vis_shares
from novem.types import Config, VisType
from novem.utils import data_on_stdin
from novem.vis import NovemVisAPI


class VisBase:
    type: VisType

    def __init__(self, config: Config) -> None:
        self.config = config

    @abstractmethod
    def set_data(self, nva: NovemVisAPI, data: str) -> None:
        ...

    @abstractmethod
    def mk(self, name: str, user: Optional[str], create: bool, args: Dict[str, Any]) -> NovemVisAPI:
        ...

    @property
    def title(self) -> str:
        return self.type.name.capitalize()

    @property
    def fragment(self) -> str:
        return f"{self.type.name}s"

    def list(self) -> None:
        list_vis(self.config, self.type)

    def delete(self, name: str) -> None:
        # if delete flag is set, we need to delete it
        # creating a plot just to delete it seems wasteful
        # We'll just use the raw api
        novem = NovemAPI(self.config)

        try:
            novem.delete(f"vis/{self.fragment}/{name}")
            return
        except Novem404:
            print(f"{self.title} {name} did not exist")
            sys.exit(1)

    def dump(self, name: str, for_user: Optional[str], *, dump_path: str) -> None:
        vis = self.mk(name=name, user=for_user, create=False)
        print(f'Dumping api tree structure to "{dump_path}"')
        vis.api_dump(outpath=dump_path)

    def tree(
        self,
        name: str,
        *,
        for_user: Optional[str],
        tree: Optional[str],
    ) -> None:
        vis = self.mk(name=name, user=for_user)

        if tree:
            path = "/"

        ts = vis.api_tree(colors=True, relpath=path)
        print(ts)

    def edit(
        self,
        name: str,
        *,
        path: str,
        for_user: Optional[str],
        create: bool,
    ) -> NovemVisAPI:
        vis = self.mk(name=name, user=for_user, create=create)

        # if we have the -e or edit flag then this takes presedence over all other
        # inputs

        # fetch our target and warn if it doesn't exist
        ctnt = vis.api_read(f"/{path}")

        # get new content
        nctnt = edit(contents=ctnt, use_tty=True)

        if ctnt != nctnt:
            # update content
            vis.api_write(f"/{path}", nctnt)

        return vis

    def modify(
        self,
        name: str,
        *,
        for_user: Optional[str],
        create: bool,
        ptype: Optional[str],
        write: List[Tuple[str, Optional[str]]],
    ) -> NovemVisAPI:
        vis = self.mk(name=name, user=for_user, create=create)

        if ptype:
            vis.type = ptype

        found_stdin = False
        stdin_data = data_on_stdin()
        stdin_has_data = bool(stdin_data)

        # check if we have any explicit inputs [-w's]
        if len(write):
            # we have inputs
            for path, data in write:
                path = f"/{path}"

                if not data:
                    if stdin_has_data and not found_stdin:
                        assert stdin_data
                        ctnt = stdin_data

                        vis.api_write(path, ctnt)
                        found_stdin = True
                    elif found_stdin:
                        print("stdin can only be sent to a single destination per invocation")
                        sys.exit(1)
                    else:
                        print(f'No data found on stdin, "-w {path}" requires data to be supplied on stdin')
                        sys.exit(1)

                elif data.startswith("@"):
                    fname = os.path.expanduser(data[1:])
                    try:
                        with open(fname, "r") as f:
                            ctnt = f.read()
                            vis.api_write(path, ctnt)
                    except FileNotFoundError:
                        print(f'The supplied input file "{fname}" does not exist. Please review your options')
                        sys.exit(1)

                else:
                    ctnt = data
                    vis.api_write(path, ctnt)

        # check if we have standard input and not already "used" it
        if not found_stdin and stdin_has_data:
            assert stdin_data
            ctnt = stdin_data
            # got stdin data
            self.set_data(vis, ctnt)

        return vis

    def share(
        self,
        name: str,
        *,
        share: Tuple[Share, Optional[str]],
        list: bool,
    ) -> None:
        share_op, share_target = share
        if share_op is Share.CREATE:
            # add a share to the vis
            vis.shared += share_target  # type: ignore

        if share_op is Share.DELETE:
            # remove a share from the vis
            vis.shared -= share_target  # type: ignore

        if share_op is Share.LIST:
            # check if we should print our shares, we will not provide other outputs
            list_vis_shares(name, self.config, self.type, list=list)
            return

    def output(self, vis: NovemVisAPI, *, tc: bool, out: Optional[str]) -> None:
        # Output - we only allow a singular -o or -x and will return as soon as
        # we find one

        # -x takes presedence
        if tc:
            # get file endpoint
            if os.name == "nt":
                from colorama import just_fix_windows_console  # type: ignore
                just_fix_windows_console()
            print(vis.files.ansi, end="")  # type: ignore
            return

        # TODO: check if we are reading any valus from the plot [-r or -x]
        if out:
            outp = vis.api_read(f"/{out}")
            print(outp, end="")
            return


class CliMail(VisBase):
    type = VisType.mail

    def set_data(self, nva: NovemVisAPI, data: str) -> None:
        nva.content = data

    def mk(self, name: str, user: Optional[str], create: bool, args: Dict[str, Any]) -> ApiMail:
        return ApiMail(
            name,
            config=self.config,
            user=user,
            create=create,
            config_path=args["config_path"],
            to=args["to"],
            cc=args["cc"],
            bcc=args["bcc"],
            subject=args["subject"],
            qpr=args["qpr"],
            debug=args["debug"],
            profile=args["profile"],
            is_cli=True,
        )

        # E-mail needs sending/testing
    def test(self, vis: ApiMail) -> None:
        vis.test()

    def send(self, vis: ApiMail) -> None:
        vis._send()



class CliPlot(VisBase):
    type = VisType.plot

    def set_data(self, nva: NovemVisAPI, data: str) -> None:
        nva.data = data

    def mk(self, name: str, user: Optional[str], create: bool) -> ApiPlot:
        return ApiPlot(
            name,
            config=self.config,
            user=user,
            create=create,
        )
