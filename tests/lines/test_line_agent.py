from portsim_line import sentence, step_url

from agentenv_portsim.lines import LinesWeek, pack

E15 = pack().get("dock-24B-w06x1-busy-0-e15")


def test_each_reply_reads_as_a_sentence_an_eta_on_an_agreed_ship_too():
    week = LinesWeek(E15)
    assert sentence(week.status("globalliner", 3)) == "STEEN (ship 3): ETA hour 31."
    assert sentence(week.request("globalliner", 3, 35) | {"asked": 35}) == (
        "STEEN (ship 3) can't make hour 35: can't arrive that early; ETA hour 31.")
    assert sentence(week.request("globalliner", 3, 42) | {"asked": 42}) == (
        "STEEN (ship 3) will arrive at hour 42, reducing speed; it keeps its turn, hour 36.")
    assert sentence(week.status("globalliner", 3) | {"agreed_before": True}) == (
        "STEEN (ship 3): ETA hour 42, as agreed; its turn is hour 36.")


def test_the_step_route_sits_beside_the_mcp_route():
    assert step_url("http://gw:8080/envs/portsim/mcp/") == "http://gw:8080/envs/portsim/step"
