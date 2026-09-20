import logging
from dataclasses import dataclass
from typing import Annotated


@dataclass
class Tool:
    _logger: logging.Logger

    async def run(self, procedure: Annotated[str, "medical procedude"]):
        self._logger.info("Received center query: %s", procedure)
        result = "No office found"

        if procedure == "liver transplant":
            result = "Arizona Medical Center"
        if procedure == "kidney transplant":
            result = "Rocky Mountain Medical Center"

        self._logger.info("Center query result: %s", result)
        return result
