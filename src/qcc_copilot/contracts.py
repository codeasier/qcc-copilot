from __future__ import annotations

from importlib import resources

from .errors import ContractError, UnknownFormatVersion
from .util import load_json_resource

# 契约资源即"版本化数据契约"的唯一真实源，放在包内以便分发后仍可加载。
# 规范语法：required/optional 的值为类型标记；enums 为字段取值约束。
_TYPE_TOKENS = {"str", "int", "number", "bool", "list", "dict", "any"}


def _load_specs():
    specs = {}
    base = resources.files("qcc_copilot").joinpath("resources/schemas")
    for entry in base.iterdir():
        if entry.name.endswith(".json"):
            data = load_json_resource(f"schemas/{entry.name}")
            specs[data["type"]] = data
    return specs


SPECS = _load_specs()
KNOWN_TYPES = sorted(SPECS)


def schema_version_for(ctype: str):
    return SPECS[ctype]["version"]


def get_spec(ctype: str):
    if ctype not in SPECS:
        raise ContractError(f"unknown contract type '{ctype}'")
    return SPECS[ctype]


def _type_ok(value, token: str) -> bool:
    if token == "any":
        return True
    if token == "str":
        return isinstance(value, str)
    if token == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if token == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if token == "bool":
        return isinstance(value, bool)
    if token == "list":
        return isinstance(value, list)
    if token == "dict":
        return isinstance(value, dict)
    return False


def _check_field(obj, field, token, problems, where=""):
    if field not in obj:
        problems.append(f"missing required field '{field}'{where}")
        return
    if not _type_ok(obj[field], token):
        problems.append(
            f"field '{field}'{where} has wrong type: expected {token}, "
            f"got {type(obj[field]).__name__}"
        )


def validate(ctype: str, obj):
    """校验并返回对象；失败时给出明确、可区分的错误。"""
    spec = get_spec(ctype)
    if not isinstance(obj, dict):
        raise ContractError(f"'{ctype}' must be a dict, got {type(obj).__name__}")

    version = obj.get("schema_version")
    if version is None:
        raise ContractError(f"'{ctype}' missing required field 'schema_version'")
    if version != spec["version"]:
        raise UnknownFormatVersion(
            f"'{ctype}' unknown format version '{version}' (supported: {spec['version']}); "
            "migration required, not treated as a blank topic",
            details=[ctype, str(version), spec["version"]],
        )

    problems = []
    id_field = spec.get("id_field")
    if id_field and not obj.get(id_field):
        problems.append(f"missing required identifier '{id_field}'")

    for field, token in spec.get("required", {}).items():
        if field == "schema_version":
            continue
        _check_field(obj, field, token, problems)

    for field, token in spec.get("optional", {}).items():
        if field in obj and not _type_ok(obj[field], token):
            problems.append(
                f"field '{field}' has wrong type: expected {token}, "
                f"got {type(obj[field]).__name__}"
            )

    for field, allowed in spec.get("enums", {}).items():
        if field in obj and obj[field] not in allowed:
            problems.append(
                f"field '{field}' value '{obj[field]}' not in {allowed}"
            )

    if problems:
        raise ContractError(f"'{ctype}' validation failed: " + "; ".join(problems), details=problems)
    return obj


def blank(ctype: str, **fields):
    """构造带正确 schema_version 的最小对象骨架（供工具创建记录）。"""
    obj = {"schema_version": schema_version_for(ctype)}
    obj.update(fields)
    return obj
