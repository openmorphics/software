# Project Architecture Rules (Non-Obvious Only)

- Monorepo tight-coupling is intentional: the repo-local CLI ([ef.main()](eventflow-cli/ef.py:590)) dynamically loads sibling packages by relative file paths rather than imports from site-packages:
  - Validators loader: [validators](eventflow-cli/ef.py:85)
  - SAL loader: [sal](eventflow-cli/ef.py:97)
  - Backend registry loader: [registry](eventflow-cli/ef.py:109)
  - Comparator loader: [comparator](eventflow-cli/ef.py:121)
  Running outside the repository root will break these loaders.
- Dual CLI surface by design:
  - Repo-local “ef” (run via Python): tests and dev workflows depend on it honoring --json and deterministic exit codes ([flag handling](eventflow-cli/ef.py:682), [printer contract](eventflow-cli/ef.py:139)).
  - Installed “eventflow” console script is a slimmer entry ([project.scripts](eventflow-cli/pyproject.toml:19)) and not used by tests.
- eventflow-core provides both pure-Python and PyO3 native implementations; selection is deferred to import time behind the EF_NATIVE toggle with tolerant fallback. Forcing native does not hard-error on import failure; it warns and downgrades ([loader policy](eventflow-core/eventflow_core/_rust/__init__.py:51-58), [is_enabled()](eventflow-core/eventflow_core/_rust/__init__.py:60-69)).
- Performance validation is environment-gated and non-default: speedup “gates” only execute when EF_BENCH_GATE=1, and expectations are controlled via env thresholds ([bench gates](eventflow-core/README.md:90-104)). Architecture assumes CI opt-in rather than always-on perf gating.
- Packaging scope is purposely narrow in v0.1 to avoid accidental coupling to Python builders: the “build” handler copies only .eir JSON and must reject Python builder paths ([build.handle() rule](eventflow-cli/eventflow_cli/build.py:13-19)). Architecturally, planners/backends are loaded separately via the registry.
- CLI behavior contract is part of the architecture: stable exit codes and dual output mode across all commands to support both human and machine workflows ([validators exit](eventflow-cli/ef.py:199-204), [trace validate](eventflow-cli/ef.py:255-260), [profile](eventflow-cli/ef.py:393-399), [backend run](eventflow-cli/ef.py:562-566), [compare-traces](eventflow-cli/ef.py:580-585)).
- Subcommands must retain lazy-import boundaries to prevent import-time hard dependencies during argparse construction; handlers resolve heavy modules on demand ([run.handle()](eventflow-cli/eventflow_cli/run.py:4-11), [build.handle()](eventflow-cli/eventflow_cli/build.py:4-10), [validate.handle()](eventflow-cli/eventflow_cli/validate.py:4-11)).