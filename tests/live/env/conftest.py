import pytest

from agentenv_portsim.schedule import ONE_WEEK
from berth_core import load_pack

EXAMPLE = "dock-24B-w07x1-busy-0"


@pytest.fixture(scope="session")
def pack():
    return load_pack()


@pytest.fixture(scope="session")
def one_week(pack):
    return [t for t in pack.tasks if ONE_WEEK.match(t.task_id)]


@pytest.fixture(scope="session")
def example(pack):
    return pack.get(EXAMPLE)
