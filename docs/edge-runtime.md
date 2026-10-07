# Edge runtime repair

## Configuration and execution

Run from the repository root. Python 3.10+ is required. Real-device dependencies
remain in `edge/requirements.txt`; Jetson.GPIO and a JetPack-compatible camera /
YOLO runtime must be installed on the device. Importing `edge.detector` does not
load a model, import device libraries, create directories, or open GPIO/cameras.

```bash
cp edge/.env.example edge/.env
# Edit edge/.env, then export its variables in a POSIX shell:
set -a
. edge/.env
set +a
python edge/detector.py
```

The script reads exported environment variables; it does not automatically load
`.env`. Keep `edge/.env` untracked. `MAILBOX_CAMERA` accepts an integer camera index
or an OpenCV-supported source string. GPIO uses BOARD pin numbering. Model and
save-directory relative paths are relative to the current working directory.
Without a save-directory setting, captures go into `edge/captured`.

- `--once`: one real capture/inference/upload, without GPIO polling.
- Default: real GPIO polling. Missing device dependencies cause an explicit failure;
  there is no automatic switch into simulation.
- Empty `GEMINI_API_KEY`: cloud analysis disabled. `MAILBOX_GEMINI_MODEL` is configurable;
  the inherited model default and SDK have not been live-validated in this repair.

## Offline simulation

Supply a local JPEG fixture. No camera, GPIO, YOLO, cloud analysis, or server is
used. The generated classification is explicitly labelled `simulation` and is
not evidence of real detection accuracy.

```bash
python edge/detector.py --simulate --once --image /path/to/test.jpg
```

Omit `--once` to repeat at approximately ten-second intervals; Ctrl+C stops it.
Add `--send` only to deliberately upload the simulated record to
`MAILBOX_SERVER_URL`. This can trigger the existing backend's Telegram behavior.

## Verification

```bash
python -m compileall -q backend edge tests
python -m unittest discover -s tests -p 'test_*.py' -v
```

Tests cover dependency-free import, configuration validation, camera release and
write failures, fake model output, pipeline decisions, HTTP payload/file cleanup,
optional-analysis failure, and explicit offline simulation. They do not validate
Jetson GPIO, actual camera capture, model accuracy, Gemini, PostgreSQL, or Telegram.
The existing highest-confidence-object classification and GPIO repeat behavior
are retained; mail-specific classification/debouncing and durable retries are
separate work items.
