import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

import orjson

logger = logging.getLogger(__name__)


@dataclass
class KedroVizConfig:
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    edges: List[Dict[str, str]] = field(default_factory=list)
    layers: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    pipelines: List[Dict[str, str]] = field(default_factory=list)
    modular_pipelines: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    selected_pipeline: str = "__default__"


class KedroVizConfigConfigDataInterface:
    def __init__(self, filepath: Path) -> None:
        self.filepath = filepath

    @staticmethod
    def _save(filepath: Path, kedro_viz_config: KedroVizConfig) -> None:
        with open(filepath, "w") as f:
            json_s = orjson.dumps(
                kedro_viz_config.__dict__, option=orjson.OPT_INDENT_2
            ).decode("utf-8")
            f.write(json_s)

            logger.info(f"The Kedro Viz Configuration file generated it:\n{json_s}")
            logger.info(f"Saved a {type(kedro_viz_config)} file to {filepath}")

    def save(self, kedro_viz_config: KedroVizConfig) -> None:
        self._save(filepath=self.filepath, kedro_viz_config=kedro_viz_config)
