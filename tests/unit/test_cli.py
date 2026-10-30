from pathlib import Path

import pytest

from neuropyhls.cli import build_parser, main
from neuropyhls.datasets import load_datasets
from neuropyhls.sources import load_sources

ROOT = Path(__file__).resolve().parents[2]


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert capsys.readouterr().out.startswith("neuropyhls ")


def test_pipeline_stubs_exit_2(tmp_path: Path) -> None:
    kernel = tmp_path / "k.py"
    kernel.write_text("def f(x):\n    return x\n")
    assert main(["analyse", str(kernel)]) == 2


def test_flow_option(tmp_path: Path) -> None:
    kernel = tmp_path / "k.py"
    kernel.write_text("def f(x):\n    return x\n")
    args = build_parser().parse_args(["port", str(kernel)])
    assert args.flow == "direct"
    args = build_parser().parse_args(["port", "--flow", "bambu", str(kernel)])
    assert args.flow == "bambu"
    assert main(["compare", str(kernel)]) == 2
    with pytest.raises(SystemExit):
        build_parser().parse_args(["port", "--flow", "catapult", str(kernel)])


def test_manifests_parse() -> None:
    sources = load_sources(ROOT / "examples" / "sources.toml")
    assert any(s.name == "spikeinterface" and len(s.commit) == 40 for s in sources)
    assert load_datasets(ROOT / "examples" / "datasets.toml") == []
