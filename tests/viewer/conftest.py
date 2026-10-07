import pytest
from recorded import ROOT

from agentenv_portsim.episodes import Runs


@pytest.fixture(scope="session")
def runs() -> Runs:
    return Runs(ROOT)
