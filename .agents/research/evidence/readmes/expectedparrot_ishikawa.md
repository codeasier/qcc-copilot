# Ishikawa

<p align="center">
  <img src="docs/assets/ishikawa-artwork.png" width="800" alt="Expected Parrot artwork: a green parrot drawing a fishbone diagram">
</p>

A Python package and CLI for structured cause-and-effect analysis and fishbone
diagrams. Define an observed problem, organize possible causes, trace why chains,
attach evidence, plan investigations, and export a diagram and report.

Like the neighboring Expected Parrot method packages, Ishikawa keeps its source
of truth in inspectable JSON files and emits JSON envelopes with suggested next
actions. The core workflow runs locally without API keys or rendering services.

![Example fishbone](examples/late-dispatch/fishbone.svg)

## Install and try

Requires Python 3.11 or newer. Install the CLI from GitHub:

```bash
uv tool install "git+https://github.com/expectedparrot/ishikawa.git"
ishikawa --help
ishikawa --project-dir ./dispatch-study example
ishikawa --project-dir ./dispatch-study report --output ./dispatch-report.html
```

For local development, clone the repository and install an editable copy:

```bash
git clone https://github.com/expectedparrot/ishikawa.git
cd ishikawa
uv venv
uv pip install -e '.[dev]'
uv run ishikawa --help
uv run ishikawa --project-dir ./dispatch-study example
uv run ishikawa --project-dir ./dispatch-study report --output ./dispatch-report.html
uv run ishikawa --project-dir ./dispatch-study diagram --output ./dispatch-fishbone.svg
```

Open `dispatch-report.html` in a browser. It contains a scrollable fishbone and
a searchable cause register with status filters, evidence, and actions. Clicking
a cause in the diagram opens its record. Everything is contained in one file;
there are no external scripts, fonts, or network requests. SVG diagrams can be
embedded in documents. Reports also support `.md` output.

With pip, use `python -m pip install -e '.[dev]'`, then invoke `ishikawa` directly.
`python -m ishikawa` works too. The committed [example report](examples/late-dispatch/report.html)
and [project JSON](examples/late-dispatch/project.json) use fictional data.

## Start an analysis

Global options go **before** the command. `--project-dir` identifies the project
root; it defaults to the current directory, or `ISHIKAWA_PROJECT_DIR` when set.
Output paths are relative to the current working directory.

```bash
ishikawa init --title "Late dispatch investigation" \
  --effect "18% of August orders missed the promised dispatch date" \
  --context "Warehouse acceptance to carrier handoff; target below 5%." \
  --template 6m

ishikawa category list
ishikawa cause add --category cat-3 \
  --label "Orders wait for one end-of-day release batch" \
  --mechanism "The batch is released after the carrier cutoff" --priority 5
ishikawa cause add --category cat-3 --parent cause-1 \
  --label "The batch schedule predates the earlier carrier cutoff"

ishikawa evidence add --cause cause-1 --relation supports \
  --observation "Late orders cluster in the final release batch" \
  --source "Warehouse event-log review, August sample"
ishikawa cause update cause-1 --status supported \
  --rationale "The log supports the mechanism; test an earlier release."

ishikawa action add --cause cause-1 \
  --description "Trial hourly batches for two weeks" --owner "Warehouse lead" \
  --success-criterion "Late dispatch rate below 5%, with order volume recorded"
ishikawa analyze
ishikawa diagram --output fishbone.svg
ishikawa report --output report.html
```

The observations above illustrate the command syntax; replace them with real
observations and traceable sources in an actual analysis. Record action results
with `action update action-1 --status done --outcome 'Observed result'`.

Templates provide starting categories that you can extend:

| Template | Categories |
| --- | --- |
| `6m` (default) | People, Machines, Methods, Materials, Measurement, Environment |
| `4s` | Surroundings, Suppliers, Systems, Skills |
| `8p` | Product, Price, Place, Promotion, People, Process, Physical evidence, Performance |
| `custom` | Empty; use `category add --name 'Your category'` |

## Analysis semantics

An Ishikawa diagram organizes **possible causes** of one effect into categories
and subcauses. This implementation follows the method described by
[ASQ](https://asq.org/quality-resources/fishbone) and the supplied
[Ishikawa diagram reference](https://en.wikipedia.org/wiki/Ishikawa_diagram).
Use a specific effect with scope and measurement, and describe mechanisms rather
than assigning blame. Ask why repeatedly where useful; there is no fixed depth.

- Causes begin as `hypothesis`. Assessments can be `supported`, `refuted`, or
  `inconclusive`. Supported and refuted assessments require a written rationale
  plus supporting or contradicting evidence, respectively.
- Evidence includes an observation, its source, and its relation to one cause.
  Conflicting observations remain visible. Counting observations does not produce
  a confidence score. The analyst is responsible for the quality of each source.
- Priority is an optional, user-assigned integer from 1 (low) to 5 (high), used
  to order investigations. It is not a probability, severity score, or causal rank.
- Leaf causes identify the ends of recorded why chains, not proven root causes.
  Supporting a child does not automatically support its parent, or vice versa.
- Actions are `investigation` or `corrective`, with owner, success criterion,
  status, and outcome. Completing an action requires an outcome and does not
  automatically change a cause's assessment.

`analyze` reports empty categories, causes lacking evidence, conflicting evidence,
leaf causes, open actions, and an investigation queue. It does not estimate causal
effects or infer a root cause automatically.

## Agent workflow and output

Tell a coding agent:

```text
Use the installed ishikawa CLI to facilitate a cause-and-effect analysis with me.
Start with `ishikawa agent-start`, inspect existing state, and follow next_actions.
Establish the observed effect and scope. Keep generated ideas as hypotheses.
Ask me for missing observations; never invent evidence or sources. Record why
chains, supporting and contradicting evidence, and testable investigations.
Finish with an SVG fishbone and an HTML report that preserves uncertainty.
```

Commands emit a single JSON envelope by default:

```json
{
  "schema_version": "1.0",
  "ok": true,
  "command": ["validate"],
  "data": {"valid": true},
  "warnings": [],
  "next_actions": []
}
```

Suggested actions are command fragments; prepend `ishikawa` and the same global
project options. They contain placeholders for the analyst to fill. `--human`
prints indented data and next steps. Help and version output are plain text.
Usage, validation, and filesystem errors emit `ok: false` with an `error` object
and a nonzero exit status.

Useful inspection commands: `project show`, `status`, `next`, `validate`, `schema`.
Use `--help` on any command or group for options.

## Files and Python API

The project is stored in `.ishikawa/project.json` under its root. Mutations
validate all references and the entire cause hierarchy before atomic replacement.
A temporary `.ishikawa/write.lock` directory rejects concurrent writers. If a
process is killed while writing, remove that empty directory after confirming
no writer remains. Individual mutations are atomic; there is no revision history.

```bash
ishikawa project export --output analysis.json
ishikawa --project-dir ./another-study project import analysis.json
ishikawa project update --effect "A more precisely defined observed problem"
```

Import validates first and refuses to replace existing state unless `--replace`
is supplied. Artifact exports refuse existing paths unless `--force` is supplied.
For bulk restructuring, renaming categories, deleting records, or changing parent
links, export, edit the JSON, validate it with the Python API or import into a new
project, and import with `--replace`. Dangling references, cross-category parents,
duplicate IDs, unsupported schema versions, and cycles are rejected.

```python
from pathlib import Path
from ishikawa import Analysis, render_svg, render_html

study = Analysis.new("Slow onboarding", "Median activation takes 12 days", template="4s")
cause = study.add_cause("cat-3", "Account approval waits for a weekly review", priority=5)
study.add_cause("cat-3", "Only one reviewer has approval access", parent_id=cause.id)
Path("onboarding.svg").write_text(render_svg(study), encoding="utf-8")
Path("onboarding.html").write_text(render_html(study), encoding="utf-8")

# Portable round trip; also validates hand-edited JSON.
restored = Analysis.model_validate_json(study.model_dump_json())
```

Prefer `add_*` and `update` methods to directly mutating model lists. Persisting
through `Store.save` always revalidates the project. Diagrams grow to accommodate
all causes and label wrapping; large investigations are best inspected in the
scrollable HTML report. PNG/PDF export, automatic AI/EDSL elicitation, statistical
causal inference, and multi-parent cause graphs are outside this initial release.

## Development

```bash
python -m pytest -q
ruff check ishikawa tests
python -m build
```

Tests cover the full CLI workflow, JSON round trips, invalid graphs and references,
failed-write preservation, assessment rules, report escaping, and SVG structure.
