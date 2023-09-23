from argus.data_interfaces.kedro_viz_config_data_interface import (
    KedroVizConfigConfigDataInterface,
)
from tests.conftest import TestDataPaths


def test_kedro_viz_config_data_interface(test_data_paths: TestDataPaths) -> None:
    kedro_viz_config_data_interface = KedroVizConfigConfigDataInterface(
        filepath=test_data_paths.path_output_kedro_viz_config
    )

    print(f"{kedro_viz_config_data_interface} needs to be patched with an actual test")
