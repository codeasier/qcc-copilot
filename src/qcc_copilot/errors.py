from __future__ import annotations


class QccError(Exception):
    """所有工具错误的基类；以结构化 code/message 表达，不与成功混淆。"""

    code = "qcc_error"

    def __init__(self, message: str, *, details=None):
        super().__init__(message)
        self.message = message
        self.details = details or []

    def as_dict(self):
        return {"code": self.code, "message": self.message, "details": list(self.details)}


class ContractError(QccError):
    """契约校验失败：缺必要标识、错误类型或未知格式版本。"""

    code = "contract_error"


class UnknownFormatVersion(ContractError):
    """未知/不受支持的格式版本，需要迁移，不以空白课题处理。"""

    code = "unknown_format_version"


class WorkspaceError(QccError):
    code = "workspace_error"


class WorkspaceNotFound(WorkspaceError):
    code = "workspace_not_found"


class AmbiguousWorkspace(WorkspaceError):
    """多课题歧义：目标明确前不允许覆盖任何档案。"""

    code = "ambiguous_workspace"


class DamagedWorkspace(WorkspaceError):
    """档案损坏或格式不受支持，保留原内容并报告迁移要求。"""

    code = "damaged_workspace"


class RevisionConflict(QccError):
    """读取后外部修改或并发写入：保留现有文件，停止本次覆盖。"""

    code = "revision_conflict"


class CapabilityError(QccError):
    """缺少可选依赖导致某步骤受限；不影响可执行步骤继续。"""

    code = "capability_limited"


class NotComputable(QccError):
    """缺少必要输入、口径不可比或零分母等，不输出无依据结果。"""

    code = "not_computable"
