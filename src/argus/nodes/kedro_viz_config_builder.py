import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import orjson

from argus.data_interfaces.kedro_viz_config_data_interface import KedroVizConfig

logger = logging.getLogger(__name__)


class NodeType(str, Enum):
    data = "data"
    task = "task"


@dataclass
class DataNodeDict:
    node_name: str
    tags: List[str] = field(default_factory=list)
    pipelines: List[str] = field(default_factory=list)
    modular_pipelines: List[str] = field(default_factory=list)
    layer: Optional[str] = None
    dataset_type: Optional[str] = None
    additional_attrs: Optional[Dict] = None


@dataclass
class TaskNodeDict:
    node_name: str
    tags: List[str] = field(default_factory=list)
    pipelines: List[str] = field(default_factory=list)
    modular_pipelines: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    additional_attrs: Optional[Dict] = None


@dataclass
class TripleDict:
    input_data_node_dict: DataNodeDict
    task_node_dict: TaskNodeDict
    output_data_node_dict: DataNodeDict

    # TODO: Implement validation methods


class KedroVizConfigBuilder:
    def __init__(self, kedro_viz_config: KedroVizConfig):
        self.kedro_viz_config = kedro_viz_config
        self.node_counter = 0  # To assign continuous integer IDs to nodes
        self.node_name_to_node_id: Dict[
            str, str
        ] = {}  # Node names are more user friendly

        self._add_pipeline(pipeline_id="__default__", pipeline_name="__default__")
        self._add_modular_pipeline(modular_pipeline_name="__root__")

    def _node_exists(self, node_id: str) -> bool:
        """
        Check if a node with the given ID exists.
        """
        return any(node["id"] == node_id for node in self.kedro_viz_config.nodes)

    def _modular_pipeline_exists(self, modular_pipeline_name: str) -> bool:
        """
        Check if a modular pipeline with the given name exists.
        """
        return any(
            mp_attrs["id"] == modular_pipeline_name
            for mp_attrs in self.kedro_viz_config.modular_pipelines.values()
        )

    def integrity_checks(self) -> bool:
        """
        Perform integrity checks on the built pipeline.
        Return True if all checks pass, else raise an exception.
        """
        # Check if nodes referenced in edges exist
        for edge in self.kedro_viz_config.edges:
            if not self._node_exists(edge["source"]) or not self._node_exists(
                edge["target"]
            ):
                raise ValueError(
                    f"Integrity check failed: Edge references non-existent node(s) - {edge}"
                )

        # Check if modular pipelines referenced in nodes exist
        for node in self.kedro_viz_config.nodes:
            for mp in node.get("modular_pipelines", []):
                if not self._modular_pipeline_exists(mp):
                    raise ValueError(
                        f"Integrity check failed: Node references non-existent modular pipeline - {node}"
                    )

        return True

    def add_triple(self, triple_dict: TripleDict) -> Tuple[str, str, str]:
        # Add nodes
        self._add_data_node(data_node_dict=triple_dict.input_data_node_dict)
        self._add_task_node(task_node_dict=triple_dict.task_node_dict)
        self._add_data_node(data_node_dict=triple_dict.output_data_node_dict)

        # Identify element IDs
        input_data_node_id = self.node_name_to_node_id[
            triple_dict.input_data_node_dict.node_name
        ]
        task_node_id = self.node_name_to_node_id[triple_dict.task_node_dict.node_name]
        output_data_node_id = self.node_name_to_node_id[
            triple_dict.output_data_node_dict.node_name
        ]

        # Add edges
        self._add_edge(source=input_data_node_id, target=task_node_id)
        self._add_edge(source=task_node_id, target=output_data_node_id)

        # Add tags
        tags: Set[str] = set(
            [
                tag
                for tag in triple_dict.input_data_node_dict.tags
                + triple_dict.task_node_dict.tags
                + triple_dict.output_data_node_dict.tags
            ]
        )
        for tag in tags:
            self._add_tag(tag=tag)

        # Add layers
        if triple_dict.input_data_node_dict.layer is not None:
            self._add_layer(triple_dict.input_data_node_dict.layer)
        if triple_dict.output_data_node_dict.layer is not None:
            self._add_layer(triple_dict.output_data_node_dict.layer)

        # Add pipelines
        pipelines: Set[str] = set(
            [
                pipeline
                for pipeline in triple_dict.input_data_node_dict.pipelines
                + triple_dict.task_node_dict.pipelines
                + triple_dict.output_data_node_dict.pipelines
            ]
        )
        for pipeline in pipelines:
            self._add_pipeline(pipeline_id=pipeline, pipeline_name=pipeline)

        # Append to modular pipelines
        if not any(
            [
                input_data_node_id == id_type_dict["id"]
                for id_type_dict in self.kedro_viz_config.modular_pipelines["__root__"][
                    "children"
                ]
            ]
        ):
            self.kedro_viz_config.modular_pipelines["__root__"]["children"].append(
                {"id": input_data_node_id, "type": "data"}
            )
        if not any(
            [
                task_node_id == id_type_dict["id"]
                for id_type_dict in self.kedro_viz_config.modular_pipelines["__root__"][
                    "children"
                ]
            ]
        ):
            self.kedro_viz_config.modular_pipelines["__root__"]["children"].append(
                {"id": task_node_id, "type": "task"}
            )
        if not any(
            [
                output_data_node_id == id_type_dict["id"]
                for id_type_dict in self.kedro_viz_config.modular_pipelines["__root__"][
                    "children"
                ]
            ]
        ):
            self.kedro_viz_config.modular_pipelines["__root__"]["children"].append(
                {"id": output_data_node_id, "type": "data"}
            )

        logger.info(
            f"Added a triple: {(triple_dict.input_data_node_dict.node_name, triple_dict.task_node_dict.node_name, triple_dict.output_data_node_dict.node_name)}"
        )

        return (input_data_node_id, task_node_id, output_data_node_id)

    def _add_data_node(self, data_node_dict: DataNodeDict) -> str:
        """
        Add a data node to the pipeline and return its ID.
        """
        if data_node_dict.node_name in self.node_name_to_node_id.keys():
            return self.node_name_to_node_id[data_node_dict.node_name]

        node_id = str(self.node_counter)
        node = {
            "id": node_id,
            "name": data_node_dict.node_name,
            "tags": data_node_dict.tags,
            "pipelines": data_node_dict.pipelines or ["__default__"],
            "type": NodeType.data.value,
            "modular_pipelines": data_node_dict.modular_pipelines,
            "layer": data_node_dict.layer,
            "dataset_type": data_node_dict.dataset_type,
        }

        if data_node_dict.additional_attrs is not None:
            node.update(data_node_dict.additional_attrs)
        self.kedro_viz_config.nodes.append(node)
        self.node_counter += 1
        self.node_name_to_node_id[data_node_dict.node_name] = node_id

        logger.debug(
            f"Added a data node: {data_node_dict.node_name} "
            f"whose node id is {node_id}"
        )

        return node_id

    def _add_task_node(self, task_node_dict: TaskNodeDict) -> str:
        """
        Add a task node to the pipeline and return its ID.
        """
        if task_node_dict.node_name in self.node_name_to_node_id.keys():
            return self.node_name_to_node_id[task_node_dict.node_name]

        node_id = str(self.node_counter)
        node = {
            "id": node_id,
            "name": task_node_dict.node_name,
            "tags": task_node_dict.tags,
            "pipelines": task_node_dict.pipelines or ["__default__"],
            "type": NodeType.task.value,
            "modular_pipelines": task_node_dict.modular_pipelines,
            "parameters": task_node_dict.parameters,
        }

        if task_node_dict.additional_attrs is not None:
            node.update(task_node_dict.additional_attrs)
        self.kedro_viz_config.nodes.append(node)
        self.node_counter += 1
        self.node_name_to_node_id[task_node_dict.node_name] = node_id

        logger.debug(
            f"Added a task node: {task_node_dict.node_name} "
            f"whose node id is {node_id}"
        )

        return node_id

    def _add_edge(self, source: str, target: str) -> None:
        """
        Add an edge to the pipeline.
        """
        if {source: target} in self.kedro_viz_config.edges:
            return None

        edge = {"source": source, "target": target}
        self.kedro_viz_config.edges.append(edge)

        logger.debug(
            f"Added an edge between node with id {source} " f"and node with id {target}"
        )

    def _add_tag(self, tag: str) -> None:
        """
        Add a tag to the pipeline.
        """
        if tag not in self.kedro_viz_config.tags:
            self.kedro_viz_config.tags.append(tag)

            logger.debug(f"Added a tag {tag} to the set")

    def _add_layer(self, layer: str) -> None:
        """
        Add a layer to the pipeline.
        """
        if layer not in self.kedro_viz_config.layers:
            self.kedro_viz_config.layers.append(layer)

            logger.debug(f"Added a layer {layer} to the set")

    def _add_pipeline(self, pipeline_id: str, pipeline_name: str) -> None:
        """
        Add a pipeline to the list of pipelines.
        """
        if not any(
            [
                pipeline_id == pipeline["id"]
                for pipeline in self.kedro_viz_config.pipelines
            ]
        ):
            new_pipeline = {"id": pipeline_id, "name": pipeline_name}
            self.kedro_viz_config.pipelines.append(new_pipeline)

            logger.debug(f"Added a pipeline {pipeline_id} to the set")

    def _add_modular_pipeline(
        self, modular_pipeline_name: str, attributes: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Add a modular pipeline to the list of modular pipelines with attributes.
        """
        if not self._modular_pipeline_exists(modular_pipeline_name):
            modular_pipeline = {
                modular_pipeline_name: {
                    "id": modular_pipeline_name,
                    "name": modular_pipeline_name,
                    "inputs": [],
                    "outputs": [],
                    "children": [
                        {"id": node["id"], "type": node["type"]}
                        for node in self.kedro_viz_config.nodes
                    ],
                }
            }
            if attributes:
                modular_pipeline[modular_pipeline_name].update(attributes)
            self.kedro_viz_config.modular_pipelines.update(modular_pipeline)

    def set_selected_pipeline(self, selected_pipeline: str) -> None:
        """
        Set the selected pipeline.
        """
        self.kedro_viz_config.selected_pipeline = selected_pipeline

    def pretty_print(self) -> str:
        """
        Return a pretty-printed string representation of the pipeline structure.
        """
        return orjson.dumps(
            self.kedro_viz_config.__dict__, option=orjson.OPT_INDENT_2
        ).decode("utf-8")
