import logging
import shutil
from pathlib import Path

from pytest import ExitCode, Session, fixture

logger = logging.getLogger(__name__)


class TestDataPaths:
    @property
    def own_path(self) -> Path:
        return Path(__file__).parent

    @property
    def path_dir_data(self) -> Path:
        return self.own_path / "data"

    # Test input data paths

    # Test output data paths

    @property
    def path_dir_output(self) -> Path:
        return self.path_dir_data / "output"


@fixture
def test_data_paths() -> TestDataPaths:
    return TestDataPaths()


def pytest_sessionstart(session: Session) -> None:
    path_dir_output = TestDataPaths().path_dir_output

    logger.info(
        f"A test data output directory at {path_dir_output} "
        "will be created if not exist already"
    )

    path_dir_output.mkdir(parents=True, exist_ok=True)


def pytest_sessionfinish(session: Session, exitstatus: ExitCode) -> None:
    path_dir_output = TestDataPaths().path_dir_output

    logger.info(f"Deleting Test output data directory at {path_dir_output}")

    shutil.rmtree(path=path_dir_output)
