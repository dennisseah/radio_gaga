from unittest.mock import Mock, call

import pytest

from radio_gaga.tools.medical_centers import Tool


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("procedure", "expected_center"),
    [
        ("liver transplant", "Arizona Medical Center"),
        ("kidney transplant", "Rocky Mountain Medical Center"),
        ("heart transplant", "No office found"),
    ],
)
async def test_run_returns_center_for_procedure(
    procedure: str, expected_center: str
) -> None:
    logger = Mock()

    result = await Tool(logger).run(procedure)

    assert result == expected_center
    assert logger.info.call_args_list == [
        call("Received center query: %s", procedure),
        call("Center query result: %s", expected_center),
    ]
