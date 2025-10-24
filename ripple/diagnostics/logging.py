import logging
from functools import partial

from blinker import Signal

from . import signals


logger = logging.getLogger("ripple")
logger.setLevel(logging.INFO)


def format_addr(addr):
    return f"{addr.host}:{addr.port}"


def log(signal, sender, **kwargs):
    # print(signal, sender, kwargs)
    originator = ""
    if sender.__class__.__name__ == "ReliableConnection":
        cfg = sender.endpoint.cfg
        originator = (
            f"{format_addr(cfg.local_addr)}->{format_addr(cfg.remote_addr)} "
        )
    line = f"{originator}{signal}: {kwargs}"
    logger.info(line)


def setup_logging():
    for member_name in dir(signals):
        member = getattr(signals, member_name)
        if isinstance(member, Signal):
            member.connect(partial(log, member_name), weak=False)
