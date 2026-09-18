"""check_json.py: strict JSON (UTF-8, no NaN / Infinity, no duplicate key), never rewritten."""

import subprocess
import sys
from pathlib import Path

import check_json

SCRIPT = Path(check_json.__file__)


def write(tmp_path, name, data):
    path = tmp_path / name
    path.write_bytes(data)
    return path


def test_valid_files_pass(tmp_path, capsys):
    paths = [
        write(tmp_path, "object.json", b'{"name": "labels", "nested": {"list": [1, 2.5, null, true]}}\n'),
        write(tmp_path, "bom.json", b'\xef\xbb\xbf{"a": "\xc3\xa9tiquette"}'),
        write(tmp_path, "same-key-in-two-objects.json", b'[{"a": 1}, {"a": 2}]'),
    ]
    assert check_json.main([str(p) for p in paths]) == 0
    assert capsys.readouterr().out == ""


def test_duplicate_key_fails(tmp_path, capsys):
    path = write(tmp_path, "dup.json", b'{"outer": {"a": 1, "a": 2}}')
    assert check_json.main([str(path)]) == 1
    assert capsys.readouterr().out == f"{path}: invalid JSON: duplicate key 'a'\n"


def test_nan_and_infinity_fail(tmp_path, capsys):
    paths = [write(tmp_path, f"{name}.json", f'{{"x": {name}}}'.encode()) for name in ("NaN", "Infinity", "-Infinity")]
    assert check_json.main([str(p) for p in paths]) == 1
    assert capsys.readouterr().out.splitlines() == [
        f"{paths[0]}: invalid JSON: invalid constant NaN",
        f"{paths[1]}: invalid JSON: invalid constant Infinity",
        f"{paths[2]}: invalid JSON: invalid constant -Infinity",
    ]


def test_invalid_utf8_fails(tmp_path, capsys):
    path = write(tmp_path, "latin1.json", '{"a": "étiquette"}'.encode("latin-1"))
    assert check_json.main([str(path)]) == 1
    assert capsys.readouterr().out.startswith(f"{path}: invalid JSON: 'utf-8' codec can't decode byte 0xe9")


def test_syntax_error_and_missing_file_fail(tmp_path, capsys):
    broken = write(tmp_path, "trailing-comma.json", b'{"a": 1,}')
    missing = tmp_path / "missing.json"
    assert check_json.main([str(broken), str(missing)]) == 1
    out = capsys.readouterr().out.splitlines()
    assert out[0].startswith(f"{broken}: invalid JSON: Expecting property name enclosed in double quotes")
    assert out[1].startswith(f"{missing}: invalid JSON: [Errno 2] No such file or directory")


def test_files_are_never_rewritten(tmp_path):
    data = b'{ "b":1,\n\n  "a" : [ 1 ,2 ] }'
    path = write(tmp_path, "ugly.json", data)
    assert check_json.main([str(path)]) == 0
    assert path.read_bytes() == data


def test_command_line_exit_code(tmp_path):
    good = write(tmp_path, "good.json", b"{}")
    bad = write(tmp_path, "bad.json", b'{"a": NaN}')
    assert subprocess.run([sys.executable, str(SCRIPT), str(good)], capture_output=True).returncode == 0
    run = subprocess.run([sys.executable, str(SCRIPT), str(good), str(bad)], capture_output=True, text=True)
    assert run.returncode == 1
    assert run.stdout == f"{bad}: invalid JSON: invalid constant NaN\n"
