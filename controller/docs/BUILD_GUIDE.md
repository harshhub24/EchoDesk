# Build Guide (PyInstaller)

This project ships an `EchoDeskController.spec` file (Phase 15) that
already accounts for PySide6/pyqtgraph's non-trivial packaging needs, so
building is a one-liner once dependencies are installed.

## Build

```bash
pip install -r requirements.txt   # includes pyinstaller
pyinstaller EchoDeskController.spec
```

Output: `dist/EchoDeskController/EchoDeskController.exe` (Windows) plus its
supporting files in the same folder (`--onedir` build, not `--onefile` —
see "Why onedir, not onefile" below).

## Verified

This spec was actually run through PyInstaller end-to-end (Linux build, for
validation — Windows builds require building on Windows) and the resulting
frozen binary was launched and confirmed to start cleanly: config loads,
logging initializes, the Qt app constructs, and session restore runs. One
real packaging bug was found and fixed this way: `pkg_resources`' runtime
hook needs `platformdirs`, which nothing in this app imports directly, so
PyInstaller's static analysis never bundled it — added explicitly to the
spec's `hiddenimports` (and to `requirements.txt`) rather than left as a
"works until it doesn't" gap.

## What the spec handles

- **PySide6 plugins.** Qt platform plugins (`qwindows.dll` etc.) and image
  format plugins aren't picked up by PyInstaller's default import analysis
  since they're loaded by Qt itself at runtime, not via a Python `import`.
  The spec explicitly collects `PySide6`'s plugin directories via
  `PyInstaller.utils.hooks.collect_data_files`.
- **pyqtgraph.** Needs its data files (icon/config resources) collected the
  same way (`collect_data_files("pyqtgraph")`).
- **python-socketio / engineio.** Pull in their packet/payload/async-client
  submodules dynamically; the spec's `hiddenimports` list covers the ones
  that PyInstaller's static analysis can miss.
- **pywin32.** `pywin32` ships COM-registration-style modules
  (`win32timezone`, etc.) that PyInstaller's hook already knows how to
  collect on Windows — no extra spec work needed there, but it does mean
  building must happen ON Windows (PyInstaller doesn't cross-compile).
- **`.env.example`** is bundled as a data file so a fresh install has a
  template to copy from, but the app always looks for the real `.env` next
  to the executable — never bundles your actual backend URL/secrets into
  the build.

## Why onedir, not onefile

`--onefile` extracts itself to a temp directory on every launch, which is
slower to start and has caused intermittent antivirus false-positives with
PySide6 apps in the wild. `--onedir` (the spec's default) starts instantly
and is easier to code-sign per-file if you take that step later. Switch by
passing `--onefile` on the command line if you specifically want a single
executable and accept the tradeoffs.

## Icon / version info

Replace `app/assets/icon.ico` with your own icon before building (a
minimal placeholder is included so the build succeeds out of the box).
Version metadata (company name, product version) is set via
`version_info.txt`, referenced from the spec's `version=` argument — edit
that file to update what shows in the .exe's Properties dialog on Windows.

## Signing (optional, recommended for distribution)

PyInstaller doesn't sign binaries itself. After building:

```powershell
signtool sign /f your-cert.pfx /p your-password /t http://timestamp.digicert.com dist\EchoDeskController\EchoDeskController.exe
```

Unsigned builds will trigger a Windows SmartScreen warning on first run for
end users — expected, not a bug.

## Clean rebuild

```bash
pyinstaller --clean EchoDeskController.spec
```

Removes PyInstaller's build cache first — worth doing after upgrading
PySide6/pyqtgraph or if you hit a stale-import error after a dependency change.
