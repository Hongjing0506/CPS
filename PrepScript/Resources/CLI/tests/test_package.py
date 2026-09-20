from pathlib import Path

import cps
from cps.bootstrap import Find_Runtime_Script, Read_CRESM_Environment


def test_wrapper_version_is_available():
    assert cps.__version__ == '0.1.0'


def test_runtime_script_is_found_from_prep_script(tmp_path, monkeypatch):
    (tmp_path / 'CRESM_Preprocessing_System.py').write_text('', encoding='utf-8')
    (tmp_path / 'Modules').mkdir()
    monkeypatch.chdir(tmp_path)
    assert Find_Runtime_Script() == Path.cwd() / 'CRESM_Preprocessing_System.py'


def test_conda_environment_is_read_from_runtime_env_ini(tmp_path, monkeypatch):
    (tmp_path / 'env.ini').write_text('[Environment]\nCONDA_CRESM = cresm\n', encoding='utf-8')
    monkeypatch.chdir(tmp_path)
    assert Read_CRESM_Environment() == 'cresm'
