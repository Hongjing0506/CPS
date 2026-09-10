"""Locate and launch the CPS script in the environment configured by env.ini."""

import configparser
import os
import shutil
import sys
from pathlib import Path


BOOTSTRAP_MARKER = "CPS_WRAPPER_BOOTSTRAPPED"
RUNTIME_SCRIPT_NAME = "CRESM_Preprocessing_System.py"
RUNTIME_ENV_CONFIG_NAME = "env.ini"


def Get_Runtime_Arguments(argv=None):
    """Return command-line arguments without changing the underlying CPS CLI."""
    return list(sys.argv[1:] if argv is None else argv)


def Find_Runtime_Script():
    """Find the existing CPS script in the current PrepScript directory."""
    working_directory = Path.cwd()
    runtime_script = working_directory / RUNTIME_SCRIPT_NAME
    modules_directory = working_directory / "Modules"
    if not runtime_script.is_file() or not modules_directory.is_dir():
        sys.stderr.write(
            "cps must be run from the PrepScript directory containing "
            f"{RUNTIME_SCRIPT_NAME} and Modules/.\n"
        )
        raise SystemExit(2)
    return runtime_script


def Read_CRESM_Environment():
    """Read the target Conda environment from the current PrepScript env.ini."""
    env_config_path = Path.cwd() / RUNTIME_ENV_CONFIG_NAME
    config = configparser.ConfigParser(interpolation=None)
    loaded_files = config.read(env_config_path)
    if not loaded_files:
        sys.stderr.write(f"CPS configuration file not found: {env_config_path}\n")
        raise SystemExit(2)
    if not config.has_section("Environment"):
        sys.stderr.write(f"Missing [Environment] in {env_config_path}\n")
        raise SystemExit(2)
    if not config.has_option("Environment", "CONDA_CRESM"):
        sys.stderr.write(f"Missing CONDA_CRESM in {env_config_path}\n")
        raise SystemExit(2)

    conda_environment = config.get("Environment", "CONDA_CRESM").strip()
    if not conda_environment:
        sys.stderr.write(f"CONDA_CRESM is empty in {env_config_path}\n")
        raise SystemExit(2)
    return conda_environment


def _Current_Conda_Environment():
    current_name = os.environ.get("CONDA_DEFAULT_ENV", "").strip()
    if current_name:
        return current_name

    prefix = os.environ.get("CONDA_PREFIX", "").strip()
    if prefix:
        return Path(prefix).name
    return ""


def _Is_Target_Environment(conda_environment):
    if os.path.isabs(conda_environment):
        current_prefix = os.environ.get("CONDA_PREFIX", "").strip()
        if not current_prefix:
            return False
        return Path(current_prefix).resolve() == Path(conda_environment).expanduser().resolve()
    return _Current_Conda_Environment() == conda_environment


def Ensure_CRESM_Environment(argv=None):
    """Re-execute the existing CPS script in the CONDA_CRESM environment."""
    if os.environ.get(BOOTSTRAP_MARKER) == "1":
        return

    conda_environment = Read_CRESM_Environment()
    if _Is_Target_Environment(conda_environment):
        return

    conda_executable = os.environ.get("CONDA_EXE", "").strip() or shutil.which("conda")
    if not conda_executable:
        sys.stderr.write("The conda executable was not found.\n")
        raise SystemExit(127)

    runtime_script = Find_Runtime_Script()
    arguments = Get_Runtime_Arguments(argv)
    os.environ[BOOTSTRAP_MARKER] = "1"
    environment_option = "-p" if os.path.isabs(conda_environment) else "-n"
    command = [
        conda_executable,
        "run",
        "--no-capture-output",
        environment_option,
        conda_environment,
        "python",
        str(runtime_script),
        *arguments,
    ]
    os.execvpe(conda_executable, command, os.environ)


def Run_CPS(argv=None):
    """Call the existing CRESM_Preprocessing_System.py without reimplementing it."""
    runtime_script = Find_Runtime_Script()
    Ensure_CRESM_Environment(argv)
    arguments = Get_Runtime_Arguments(argv)
    command = [sys.executable, str(runtime_script), *arguments]
    os.execv(sys.executable, command)
