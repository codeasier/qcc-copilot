# 分发包、依赖与能力检查（9.2）

## 分发包内容

```
src/qcc_copilot/skill/         Skill 文档（随 wheel 分发；qcc skill.export 导出）
  SKILL.md                     完整 Skill 指令与领域操作入口
  quickstart.md                成员快速开始
  lead-guide.md                负责人使用
  upgrade-rollback.md          升级回滚
  references/
    commands.md                命令与输入契约
    workspace.md / discovery.md / methods.md / benefits.md / reuse.md
    deliverables.md / summary.md / capability-check.md / support-matrix.md
  dist-manifest.json           版本、依赖、资源清单
src/qcc_copilot/               确定性内核 + 资源
  cli.py / commands.py / contracts.py / workspace.py / evidence.py / deliveries.py
  sources.py / discovery.py / methods.py / benefits.py / reuse.py
  deliverables.py / pptx.py / summary.py / capability.py / errors.py / util.py
  resources/
    schemas/*.json             版本化数据契约
    methods/method_profile_v1.json
    templates/*.tpl, neutral_theme.json
    manifest.json
pyproject.toml                 安装元数据（setuptools，src 布局）
tests/                         固定样例与验收测试
docs/                          实施基线、验收报告、校准记录、发布准备
```

## 依赖（可锁定）

| 类型 | 依赖 | 必需 | 缺失影响 |
|---|---|---|---|
| 运行时 | Python >= 3.11 标准库 | 是 | 无（核心零第三方依赖） |
| PPTX 生成 | 内置 stdlib OOXML | 是 | 始终可用 |
| `python-pptx`（可选 extra `pptx`） | 第三方 | 否 | 不使用；能力检查报告改用内置生成器 |
| 渲染核验 | LibreOffice/soffice 或 macOS Quick Look | 否 | 渲染检查 `not_run/受限`，不标通过 |

`pyproject.toml` 的 `dependencies=[]` 即"可锁定"配置：干净环境 `PYTHONPATH=src python3 -m qcc_copilot version` 即可运行；
`optional-dependencies` 仅作环境适配记录。也可 `pip install qcc-copilot`（入口 `qcc`），Skill 文档随 wheel 在包内 `qcc_copilot/skill/`。

## 从新目录安装后的资源检查

```bash
export QCC="PYTHONPATH=<包>/src python3 -m qcc_copilot"
$QCC version                 # 报告版本
$QCC capabilities            # 报告依赖与受限步骤
$QCC contract.types          # 加载契约资源
$QCC methods.profile         # 加载方法规则资源
$QCC deliverable.compile ... # 加载模板资源并产出文件包
```

- 资源通过 `importlib.resources` 从包内加载，不依赖当前工作目录或全局配置。
- `capabilities` 明确列出 `limited_steps`：缺生成或渲染依赖时报告**具体受限步骤**，不把未执行检查标为通过。

## 版本标识

- 内核版本：`0.1.0`（`qcc_copilot.__version__` / `$QCC version`）
- 契约版本：`1.0`；摘要格式版本：`1.0`
- 方法规则：`qcc-three-dimensions` v1.0；契约/模板/主题在 `dist-manifest.json` 列出

## 验证点（9.2 / 1.2）

- 干净环境可安装、报告版本，并加载规则、模板和契约资源。
- 从新目录安装后资源齐全；缺生成/渲染依赖报告具体受限步骤。
