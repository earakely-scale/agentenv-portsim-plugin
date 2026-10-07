"""web/upstream/ is PortSimEnv's viewer (envs/berth_planning/openenv/berth_openenv/web/ at b0f4c2f), unchanged."""

import hashlib
from pathlib import Path

import agentenv_portsim

UPSTREAM = Path(agentenv_portsim.__file__).parent / "web" / "upstream"

B0F4C2F = {
    "api.js": "d63e37fbfd3a33a662b12f5d71ddc98f72a007521985dc2c8e0400f9205d8db8",
    "app.js": "cba7f68d02bcf06825b7e4cdd20df327e5cdc46964884911ae64055cc983ecc0",
    "cargo-handling.js": "2e67c15c58eb765fc92c8b9dc2b719cf5f4aefce7e7e2a6594ab970d51ef6de4",
    "chart.js": "9c3e5f9c90ff0d10ffbdcc44049d050a6b1ac6a24867305954705fe36754fb0d",
    "crane-allocation.js": "ee1ac440252548063c3683d4c5c0d3e4d42fe0e5f1bcccb259c46acc122c6f7f",
    "index.html": "7d058e9329219358a1054e228df9ff5faba31115f0b803f2711b7d92ce98b6cf",
    "model.js": "5908d93c4e179e7586cf02d2e41514f179a71c3407057dd886f7ed06e909631f",
    "navigation.js": "b081f45bfcf586e47a45dbc5ac430ed451523774916eccf0371d1e7942dc6e7a",
    "overview.js": "feeee6a4da688ffd5eb93ecbe3b51ad5464c01322e1135e86266d0e09bccb3be",
    "play.js": "c0e7b328d6ec6481f20b58379c8feb1891654927df3a534c53f242c36843ad11",
    "pp-shim.js": "47a40bceff2b86db6be22d4ace4ca0522a864a41ea64a8cf50875d245f8d295e",
    "scene-cargo.js": "608467a89b977a0a605511cafad47c1ffe3693e711aec0fbcd92d127f90c84f2",
    "scene-context.js": "c3a721f8eca9c8d60f80fa1ab436aaba6e7ae9defa215da63c8d759342d4f7a7",
    "scene-cranes.js": "b76af98ade0a176f886e000fa54fadae2bebd7b95576726fea62c6d4e2825b12",
    "scene-env.js": "016f7d2f69a3535393e3c58cf795d2331349935c9d38bf0716438fa3086e24ac",
    "scene-kit.js": "fa80390891beadbad9e927b517c36157a228ed8900a99c4c1df0c319c56c91c1",
    "scene-ships.js": "bffefce7f07787abf33813d662b27432d48639208b27ce93d8cc9b82ad8e6724",
    "scene-world.js": "37fcdbec67ca64a1ec93d2c2c1e03d3b0a3c1356bb63e95342424b0d4fddcf26",
    "scene.js": "db15a71a2f8c75714cd56e5157147c6d2b938f7ef826a75ed8cc54c5308a8a9f",
    "stage.js": "97ce44167ecc12562f792c0853f55e064f62145d131d9d0bb74cff378f721fcb",
    "style.css": "39211aee8cf4b2d2a42d86c3a830c07ba47ff554f53eb714af93f7e475a8202c",
    "transcript.js": "6facff74128bb2f229904b87b7fcbd1851a7ac147a023261cedf943664022971",
    "twin.js": "7112cfc7b89f436685aa3bc34acbf9356edbf8a41fd2a86386c30ce819632895",
    "twin/SOURCES.md": "0bee73691b93043c43efb1bd72e253ba88fc0f11cff143541d390f607b587ce9",
}


def test_the_vendored_viewer_is_upstreams_files_unchanged():
    files = {p.relative_to(UPSTREAM).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in UPSTREAM.rglob("*") if p.is_file()}
    assert files == B0F4C2F
