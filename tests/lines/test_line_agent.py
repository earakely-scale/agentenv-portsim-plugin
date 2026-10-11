import asyncio

import portsim_line
from portsim_line import sentence, step_url
from portsim_llm import message_schema

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


def test_a_request_and_an_eta_query_each_reach_their_tool_and_both_at_once_is_refused():
    calls = []

    class Desk(portsim_line.Desk):
        async def call(self, name, arguments):
            calls.append((name, arguments))
            return {"ship": arguments["ship"], "eta": 31}

    desk = Desk(None, "", "globalliner")
    replies = [asyncio.run(desk.answer(e)) for e in (
        {"ship": 3, "ask": "eta"}, {"ship": 3, "ask": "eta", "request_arrival": None},
        {"ship": 3, "request_arrival": 42}, {"ship": 3, "ask": None, "request_arrival": 42},
        {"ship": 3, "ask": "eta", "request_arrival": 42}, {"ship": 3, "ask": None, "request_arrival": None})]
    assert calls == [("ship_status", {"ship": 3})] * 2 + [("agree_arrival", {"ship": 3, "arrival": 42})] * 2
    assert [r["asked"] for r in replies[2:4]] == [42, 42]
    assert all("one per request" in r["error"] for r in replies[4:])


def test_the_message_schema_lets_a_strict_provider_leave_either_half_out():
    request = message_schema(["globalliner"])["properties"]["requests"]["items"]
    assert set(request["required"]) == set(request["properties"]) and request["additionalProperties"] is False
    assert request["properties"]["ask"]["enum"] == ["eta", None]
    assert request["properties"]["request_arrival"]["type"] == ["integer", "null"]
