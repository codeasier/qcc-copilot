from __future__ import annotations

import json
import tempfile
from pathlib import Path

from qcc_copilot import commands as C

FIX = Path(__file__).parent / "fixtures"


def fixture(name):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def fixture_path(name):
    return FIX / name


def new_base():
    return tempfile.mkdtemp(prefix="qcc-test-")


def call(cmd, base=None, topic_id=None, **kw):
    r = dict(kw)
    if base is not None:
        r["workspace"] = base
    if topic_id is not None:
        r["topic_id"] = topic_id
    return C.HANDLERS[cmd](r)


def init_topic(base, topic_id="t1", **kw):
    return call("workspace.init", base, topic_id=topic_id, **kw)


def read(path, name):
    return (Path(path) / name).read_text(encoding="utf-8")
