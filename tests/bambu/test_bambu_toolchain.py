import subprocess


def test_bambu_runs() -> None:
    result = subprocess.run(["bambu", "--version"], capture_output=True, text=True, check=False)
    assert result.returncode == 0
    # The version banner is ASCII art plus a copyright line; the tool name itself is not in it.
    assert "politecnico di milano" in (result.stdout + result.stderr).lower()
