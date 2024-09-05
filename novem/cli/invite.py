import datetime
import email.utils as eut
import json
from typing import Any, Dict, List, Optional

from novem.exceptions import Novem404
from novem.types import Config

from ..api_ref import NovemAPI
from ..utils import cl, pretty_format


def list_invites(api: NovemAPI, *, list: bool) -> None:
    """
    List pending invites
    """

    try:
        ilist = json.loads(api.read("/admin/invites/"))
    except Novem404:
        ilist = []

    ilist = sorted(ilist, key=lambda x: x["name"])

    if list:
        # print to terminal
        for p in ilist:
            print(p["name"])

        return

    flist = []

    for i in ilist:
        res = {}
        nm = i["name"]
        # let's populate our final list with info
        res["name"] = nm
        res["id"] = nm

        gt = "unkown"
        user = ""
        group = ""
        org = ""
        if nm[0] == "+" and "~" in nm:
            gt = "organisation group"
            spl = nm[1:].split("~")
            org = spl[0]
            group = spl[1]
        elif nm[0] == "@" and "~" in nm:
            gt = "user group"
            spl = nm[1:].split("~")
            user = spl[0]
            group = spl[1]
        elif nm[0] == "+" and "~" not in nm:
            gt = "organisation"
            org = nm[1:]
        else:
            gt = "unkown"

        res["group"] = group
        if org:
            res["org_user"] = f"+{org}"
        else:
            res["org_user"] = f"@{user}"

        res["type"] = gt
        res["created"] = i["created_on"]

        flist.append(res)

    ppo: List[Dict[str, Any]] = [
        {
            "key": "id",
            "header": "Invitation ID",
            "type": "text",
            "overflow": "keep",
        },
        # {
        #    "key": "id",
        #    "header": "ID",
        #    "type": "text",
        #    "overflow": "keep",
        # },
        {
            "key": "type",
            "header": "Type",
            "type": "text",
            "clr": cl.OKCYAN,
            "overflow": "keep",
        },
        {
            "key": "group",
            "header": "Group",
            "type": "text",
            "overflow": "truncate",
        },
        {
            "key": "org_user",
            "header": "Org / User",
            "type": "text",
            "overflow": "truncate",
        },
        {
            "key": "created",
            "header": "Created",
            "type": "date",
            "overflow": "keep",
        },
    ]

    for p in flist:
        nd = datetime.datetime(*eut.parsedate(p["created"])[:6])
        p["created"] = nd.strftime("%Y-%m-%d %H:%M")

    ppl = pretty_format(flist, ppo)

    print(ppl)


def invite(
    config: Config,
    *,
    invite: Optional[str] = None,
    accept: bool = False,
    reject: bool = False,
) -> None:
    config.is_cli = True
    novem = NovemAPI(config, is_cli=True)


    if invite is None:
        # we need to list plots
        list_invites(config, novem)
        return

    # check if
    if accept:
        novem.write(f"/admin/invites/{invite}/accept", "yes")

    elif reject:
        novem.write(f"/admin/invites/{invite}/accept", "no")
