# CPS Command-Line Wrapper

This project provides the `cps` command as a thin Python wrapper around the
existing `CRESM_Preprocessing_System.py`. It does not contain or reimplement
the CRESM preprocessing workflow.

Authors: Omarjan Obulkasim; Shulei Zhang; Han Zhang; Hongjing Chen

## Installation

Install the wrapper with pip:

```bash
python -m pip install --no-build-isolation ./Resources/CLI
```

The wrapper itself uses only the Python standard library. The scientific
dependencies and external model tools remain those required by the existing
CPS installation.

## Usage

Change into the existing CPS `PrepScript/` directory. It must contain:

- `CRESM_Preprocessing_System.py`
- `Modules/`
- `env.ini`
- `case.ini`

Then use the wrapper exactly as you previously used the Python script:

```bash
cd /path/to/CPS/PrepScript
cps -h
cps -n CN_15km
```

Every argument is forwarded unchanged to
`CRESM_Preprocessing_System.py`. Therefore all options and configuration
validation remain defined by the current CPS source code.

Before launching the script, the wrapper reads `[Environment] CONDA_CRESM`
from the current `env.ini`. If the current Conda environment is different,
the wrapper invokes the existing script through `conda run` in the configured
environment. No shell launcher is required.

The aliases `CPS` and `python -m cps` are also provided. A source checkout of
this wrapper can be tested from an existing `PrepScript/` directory with:

```bash
PYTHONPATH=/home/wumej22/hydata/Codex_Works/CPS/PrepScript/Resources/CLI/src python -m cps -h
```

The wrapper's Python API is intentionally small:

```python
from cps import main

main(['-n', 'CN_15km'])
```

## Local development

The wrapper is installed directly from this local directory; no PyPI upload is required.

```bash
cd /home/wumej22/hydata/Codex_Works/CPS/PrepScript/Resources/CLI
python -m pip install --no-build-isolation -e .
python -m pytest -q
```

The package release version belongs to this wrapper. The CPS runtime version
shown by `cps -v` is produced by the existing
`PrepScript/Modules/Utils/Consts.py`.
