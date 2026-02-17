# Migration Notes for v0.1.0

This guide covers practical updates needed when moving from pre-release snapshots to `v0.1.0`.

## 1. CLI Validation Commands

Use grouped `validate` targets instead of legacy alias commands.

- Before:
  - `validate-eir`
  - `validate-event`
  - `validate-dcd`
  - `validate-efpkg`
  - `validate-trace`
- After:
  - `eventflow --json validate --eir <path>`
  - `eventflow --json validate --event <path>`
  - `eventflow --json validate --dcd <path>`
  - `eventflow --json validate --efpkg <path>`
  - `eventflow --json validate --trace <path>`

## 2. Packaging Input Scope for `build`

`build` accepts EIR JSON input only in v0.1.

- Python builder path inputs must be treated as out-of-scope and error by design.

## 3. Backend Resource Expectations

Backend descriptors are packaged with distributions and loaded as package resources.

- If your tooling directly referenced unpacked repo files, switch to normal installed-package behavior and CLI/API loaders.

## 4. Dependency Expectations

When installing `eventflow-cli` from package artifacts, runtime package dependencies are now explicit and install automatically.

- `eventflow-core`
- `eventflow-sal`
- `eventflow-backends`
- `eventflow-hub`

## 5. Native Toggle Behavior

Native behavior remains environment controlled:

- `EF_NATIVE=1`: force native when importable; warn/fallback if import fails.
- `EF_NATIVE=0`: disable native.
- unset: auto mode.
