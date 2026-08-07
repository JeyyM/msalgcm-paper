# Team setup — get an identical environment before running anything

**Read this before running any experiment.** The goal of this file is that everyone on the
team — and everyone's AI assistant — ends up with the **exact same package versions**, so
results are comparable across machines. Skipping the pinned versions below is the most likely
way to silently produce numbers that don't match anyone else's.

If you're pasting this to an AI agent (Cursor, Claude, Copilot, etc.) to set this up for you,
paste the whole file — the [instructions for AI agents](#instructions-for-ai-agents) section at
the bottom has explicit guardrails it needs to follow.

---

## 0. What you need before starting

| Tool | Required version | Check with |
|---|---|---|
| Python | **3.13.x** (project supports 3.11+, but 3.13.5 is what produced the current results) | `python --version` |
| Node.js | **20.x** | `node --version` |
| npm | **10.x** | `npm --version` |
| git | any recent version | `git --version` |

If your Python/Node major version differs, say so before continuing — don't silently proceed on
a different version.

---

## 1. Clone and check out the right commit

```bash
git clone <GIT_REMOTE_URL> msalgcm-paper
cd msalgcm-paper
git checkout <BRANCH_OR_COMMIT>
```

> Whoever pushes should replace `<GIT_REMOTE_URL>` and `<BRANCH_OR_COMMIT>` above with the real
> values before sharing this file.

Confirm you're on the right commit:

```bash
git log -1 --oneline
git status
```

`git status` should say **"nothing to commit, working tree clean"**. If it doesn't, stop —
you're not looking at the same code everyone else is.

---

## 2. Create an isolated Python environment

**Do not install into your global/system Python.** Use a fresh virtual environment every time —
this project was previously running from a global install with 300+ unrelated packages mixed in,
which is exactly the kind of thing that causes "works on my machine" bugs.

```bash
# from the project root
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

Confirm the venv is active — your shell prompt should show `(.venv)`, and:

```bash
python -c "import sys; print(sys.prefix)"
```

should point **inside** the project folder, not a system Python path.

---

## 3. Install exact pinned Python versions

Do **not** run `pip install -e ".[dev,web,ml,viz]"` directly for a fresh setup — that resolves
whatever the *latest* versions matching the loose bounds in `pyproject.toml` happen to be today,
which will drift over time and across machines. Instead:

```bash
pip install -r requirements-lock.txt
pip install -e . --no-deps
```

`requirements-lock.txt` pins the exact versions verified against the current TSP results
(see `audit_checklist.md`). `--no-deps` on the editable install prevents pip from trying to
"helpfully" resolve/upgrade anything from `pyproject.toml`.

Verify:

```bash
pip show numpy scikit-learn pandas pydantic typer fastapi
```

Every version shown must match `requirements-lock.txt` exactly. If pip couldn't satisfy a pin
(e.g. wrong Python version, platform issue), **stop and report it** — don't let it install a
substitute version silently.

---

## 4. Install Node dependencies from the lockfile

```bash
npm ci
npm ci --prefix web/frontend
```

Use `npm ci`, **not** `npm install` — `ci` installs exactly what's in `package-lock.json`;
`install` can bump versions within semver ranges.

---

## 5. Confirm datasets are present

Most datasets are committed to git and will already be there after cloning. Confirm:

```bash
python -c "
from pathlib import Path
checks = [
    'datasets/tsp/instances/kroA100.tsp',
    'datasets/scheduling/jsp/instances/ft10.txt',
    'datasets/feature_selection/ew/BreastEW.csv',
]
for p in checks:
    print(p, '->', 'OK' if Path(p).exists() else 'MISSING')
"
```

If anything is `MISSING` (most likely `MadelonEW.csv`, which is gitignored due to size), run:

```bash
python scripts/download_datasets.py
```

---

## 6. Verify the environment before running anything real

This is the step that actually catches version drift. Run both:

```bash
pytest -q
```

**Expected: `56 passed`.** If you get a different number, stop — do not proceed to run
experiments, report the exact output back first.

```bash
python scripts/audit_tsp_results.py --all-canonical
```

**Expected: all three folders report `CLEAN`, `Total failures across all folders: 0`.** This
recomputes tour distances, gap percentages, and validates every existing TSP result from scratch
using your local numpy — if your environment matched, this will still be clean. This is the
closest thing to a checksum that "your setup matches the setup that produced these results."

Only move on to running new experiments once both checks pass exactly as described.

---

## 7. Running an experiment

### Single config via CLI (recommended for scripted/batch work)

```bash
optimize validate --config config/examples/tsp_kroA100_comparison.json
optimize run --config config/examples/tsp_kroA100_comparison.json
```

Output goes to a new timestamped folder under `results/`.

### Via the web dashboard (recommended for exploring/visual work)

```bash
npm run dev
```

Open http://127.0.0.1:5173 — pick a domain, instance/dataset, and algorithm, then "Run
experiment."

### List what's available

```bash
optimize list
```

---

## 8. Sending results back

`results/` is intentionally excluded from git (see `.gitignore`) — experiment output isn't
meant to bloat the repo automatically. After a run:

1. Find your new folder under `results/` (named `<timestamp>_<experiment_name>`).
2. Zip just that folder.
3. Send it to `<WHOEVER_IS_MERGING>` via `<SHARED_DRIVE_OR_CHANNEL>`, **or** if told to commit it
   directly, use `git add -f results/<folder_name>` (the `-f` is required since `results/` is
   gitignored — only do this for folders you've been told are final).

Do **not** merge someone else's results folder into your own run of the *same*
instance+algorithm pair unless you're deliberately replacing it — the run system treats one
folder per pair as canonical.

---

## 9. Task assignment

Fill in before splitting work. Check `documentation v1.md` and `audit_checklist.md` first —
TSP is already complete; nothing there needs to be rerun. **JSP and FS are now also tuned and
frozen** (as of 2026-08-07 — see `documentation v1.md`), so all three domains are ready for the
final 30-run comparison benchmarks: `config/examples/jsp_ft10_comparison.json` on
ta31/ta51/ta71, and `config/examples/fs_breastew_comparison.json` on
BreastEW/WineEW/LymphographyEW/SpectEW/MadelonEW. Use `optimize list` to see everything
available. Do not touch the tuning instances/datasets (ft10, ta01, ta21 for JSP; ZooEW,
IonosphereEW, SonarEW for FS) for final comparisons — those were used to pick the frozen
parameters and would leak tuning effort into the reported results.

| Person | Domain | Instance(s) / dataset(s) | Algorithm(s) | Status |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |

---

## Instructions for AI agents

If you are an AI coding assistant executing this setup on behalf of a teammate, follow these
rules exactly. They exist because "helpful" deviations here silently break cross-machine
reproducibility, which is the entire point of this file.

1. **Never substitute versions.** If `requirements-lock.txt` pins `numpy==2.3.5` and that exact
   wheel isn't available for the user's platform/Python version, **stop and report the error**.
   Do not install the "closest" version, do not upgrade, do not edit the lock file to make it
   pass.
2. **Never edit `pyproject.toml` bounds** to resolve a dependency conflict. If installation
   fails, report the exact pip error back to the user instead of loosening/tightening version
   constraints.
3. **Never run `pip install --upgrade`** on anything in this project, for any reason, during
   setup.
4. **Always create and activate a fresh virtual environment first.** Never install into a
   global/system Python, even if one is already set up and "would be faster."
5. **Always run the Section 6 verification (`pytest -q` and
   `python scripts/audit_tsp_results.py --all-canonical`) before running any real experiment**,
   and report the literal output back to the user. If either check doesn't match the expected
   result exactly (`55 passed`; all three folders `CLEAN`), stop there — do not attempt to fix
   test failures by changing project code or versions on your own initiative, and do not proceed
   to run experiments on an unverified environment.
6. **Never modify files under `results/tuning/`, `config/examples/*_comparison.json`, or
   `config/tuning/`** unless the user explicitly asked you to change tuning parameters. These
   are the frozen, paper-final settings.
7. **Never delete or overwrite another teammate's result folder** under `results/`. If a task
   assigns you a specific `(instance, algorithm)` pair, only touch that pair's output.
8. **If `git status` shows unexpected uncommitted changes** after cloning, stop and tell the
   user rather than committing, discarding, or stashing them yourself.
9. **When done, report:** the exact commit hash you're on, the exact output of the Section 6
   verification, and the path of any new `results/` folder you produced. Do not summarize this
   as "everything worked" without showing the literal command output.
