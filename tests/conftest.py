"""Mark tests by folder (tests/unit -> unit, ...) and skip tool tests when the tool is missing."""

import shutil
from pathlib import Path

import pytest

FOLDER_MARKERS = {"unit", "bambu", "vitis"}
REQUIRED_TOOLS = {"bambu": ["bambu", "verilator"], "vitis": ["vitis-run"]}


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    for item in items:
        folder = Path(item.fspath).parent.name
        if folder in FOLDER_MARKERS:
            item.add_marker(getattr(pytest.mark, folder))
            missing = [t for t in REQUIRED_TOOLS.get(folder, []) if shutil.which(t) is None]
            if missing:
                item.add_marker(pytest.mark.skip(reason=f"not installed: {', '.join(missing)}"))
