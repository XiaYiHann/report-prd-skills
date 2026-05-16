from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="run tests marked with integration",
    )
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="run tests marked with slow",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    run_integration = config.getoption("--run-integration")
    run_slow = config.getoption("--run-slow")
    skip_integration = pytest.mark.skip(reason="integration tests are skipped by default; pass --run-integration")
    skip_slow = pytest.mark.skip(reason="slow tests are skipped by default; pass --run-slow")

    for item in items:
        if "integration" in item.keywords and not run_integration:
            item.add_marker(skip_integration)
        if "slow" in item.keywords and not run_slow:
            item.add_marker(skip_slow)
