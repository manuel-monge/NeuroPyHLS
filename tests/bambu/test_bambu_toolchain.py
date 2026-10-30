import subprocess


def test_bambu_runs() -> None:
    result = subprocess.run(["bambu", "--version"], capture_output=True, text=True, check=False)
    assert result.returncode == 0
    assert "bambu" in (result.stdout + result.stderr).lower()
