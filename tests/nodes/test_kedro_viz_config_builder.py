"""
test_node_addition: Checks if a node can be added and if its attributes are set correctly.
test_edge_addition: Verifies that edges between nodes can be added.
test_adding_existing_tag: Ensures that adding an existing tag doesn't create duplicates.
test_adding_existing_layer: Makes sure that adding an existing layer doesn't create duplicates.
test_modular_pipeline_addition: Checks if a modular pipeline can be added and if its attributes are set correctly.
test_integrity_checks: Tests the integrity checks with a valid configuration.
test_integrity_checks_failure: Ensures the integrity checks fail when there's a mismatch in the configuration.
"""

import pytest

from argus.data_interfaces.kedro_viz_config_data_interface import KedroVizConfig
from argus.nodes.kedro_viz_config_builder import (
    DataNodeDict,
    KedroVizConfigBuilder,
    TaskNodeDict,
)


def test_node_addition() -> None:
    builder = KedroVizConfigBuilder(KedroVizConfig())
    task_node_dict = TaskNodeDict(node_name="Node A")
    node_id = builder._add_task_node(task_node_dict)

    assert isinstance(node_id, str)
    assert len(builder.kedro_viz_config.nodes) == 1
    assert builder.kedro_viz_config.nodes[0]["name"] == "Node A"


def test_edge_addition() -> None:
    builder = KedroVizConfigBuilder(KedroVizConfig())
    task_node_1_dict = TaskNodeDict(node_name="Node 1")
    task_node_2_dict = TaskNodeDict(node_name="Node 2")
    node1 = builder._add_task_node(task_node_1_dict)
    node2 = builder._add_task_node(task_node_2_dict)
    builder._add_edge(source=node1, target=node2)

    assert len(builder.kedro_viz_config.edges) == 1
    assert builder.kedro_viz_config.edges[0]["source"] == node1
    assert builder.kedro_viz_config.edges[0]["target"] == node2


def test_adding_existing_tag() -> None:
    builder = KedroVizConfigBuilder(KedroVizConfig())
    builder._add_tag("tag1")
    builder._add_tag("tag1")

    assert len(builder.kedro_viz_config.tags) == 1


def test_modular_pipeline_addition() -> None:
    builder = KedroVizConfigBuilder(KedroVizConfig())
    builder._add_modular_pipeline(
        "mod_pipeline1", attributes={"description": "This is a modular pipeline"}
    )

    assert len(builder.kedro_viz_config.modular_pipelines) == 2
    assert (
        list(builder.kedro_viz_config.modular_pipelines.values())[1]["id"]
        == "mod_pipeline1"
    )
    assert (
        list(builder.kedro_viz_config.modular_pipelines.values())[1]["description"]
        == "This is a modular pipeline"
    )


def test_integrity_checks() -> None:
    builder = KedroVizConfigBuilder(KedroVizConfig())
    data_node_dict = DataNodeDict(
        node_name="Node 1",
        modular_pipelines=["mod_pipeline1"],
        tags=["tag3"],
        pipelines=["pipeline1"],
        layer="layer1",
    )
    task_node_dict = TaskNodeDict(
        node_name="Node 2",
        modular_pipelines=["mod_pipeline1"],
        tags=["tag3"],
        pipelines=["pipeline1"],
    )
    node1 = builder._add_data_node(data_node_dict)
    node2 = builder._add_task_node(task_node_dict)
    builder._add_edge(source=node1, target=node2)
    builder._add_tag("tag3")
    builder._add_layer("layer1")
    builder._add_pipeline("pipeline1", "pipeline1")
    builder._add_modular_pipeline(
        "mod_pipeline1", attributes={"description": "This is a modular pipeline"}
    )

    # This should pass without any exceptions
    assert builder.integrity_checks() is True


def test_integrity_checks_failure() -> None:
    builder = KedroVizConfigBuilder(KedroVizConfig())
    data_node_dict = DataNodeDict(node_name="Node 1")
    node1 = builder._add_data_node(data_node_dict)
    builder._add_edge(source=node1, target="99999")  # Nonexistent node

    with pytest.raises(
        ValueError,
        match=r"Integrity check failed: Edge references non-existent node\(s\)",
    ):
        builder.integrity_checks()
