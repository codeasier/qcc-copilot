from __future__ import annotations

import argparse
import json
import os
import sys

from . import __version__
from .errors import QccError


def _load_request(path):
    if path and path != "-":
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        raw = path.strip()
        if raw.startswith(("{", "[")):
            return json.loads(raw)
        raise QccError(f"input file not found: {path}")
    if not sys.stdin.isatty():
        raw = sys.stdin.read().strip()
        if raw:
            return json.loads(raw)
    return {}


def main(argv=None):
    parser = argparse.ArgumentParser(prog="qcc", description="qcc-copilot 确定性内核：结构化输入输出")
    parser.add_argument("command", help="领域操作命令，见 src/qcc_copilot/skill/references/commands.md")
    parser.add_argument("--workspace", "-w", help="显式工作区根路径（.qcc 所在目录）")
    parser.add_argument("--input", "-i", help="结构化请求：JSON 文件路径、内联 JSON，或 - 读 stdin")
    parser.add_argument("--out", "-o", help="把结果 JSON 写入文件（仍打印到 stdout）")
    args = parser.parse_args(argv)

    try:
        request = _load_request(args.input)
        if args.workspace:
            request.setdefault("workspace", args.workspace)

        if args.command == "version":
            data = {"version": __version__, "python": sys.version.split()[0]}
        elif args.command == "capabilities":
            from . import capability

            data = capability.check()
        else:
            from . import commands

            handler = commands.HANDLERS.get(args.command)
            if handler is None:
                raise QccError(
                    f"unknown command '{args.command}'",
                    details=[f"available: {', '.join(sorted(commands.HANDLERS))}"],
                )
            data = handler(request)

        result = {"ok": True, "command": args.command, "data": data}
    except QccError as exc:
        result = {"ok": False, "command": args.command, "error": exc.as_dict()}
    except Exception as exc:  # 未预期错误也结构化返回，不静默当成功
        result = {
            "ok": False,
            "command": args.command,
            "error": {"code": "unexpected_error", "message": str(exc), "details": []},
        }

    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        from .util import write_text

        write_text(args.out, text + "\n")
    print(text)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
