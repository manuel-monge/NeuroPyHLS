import subprocess


def test_vitis_runs() -> None:
    result = subprocess.run(["vitis-run", "--version"], capture_output=True, text=True, check=False)
    assert result.returncode == 0
