"""The twin is downloaded once into the user cache and checked against its pins; bytes that don't match aren't
written."""

import hashlib
import io

import click
import pytest

from agentenv_portsim import twin

GOOD = b"twin data"


@pytest.fixture
def cache(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    monkeypatch.setattr(twin, "FILES", {"twin.json.gz": (len(GOOD), hashlib.sha256(GOOD).hexdigest())})
    return tmp_path / "agentenv-portsim/twin/b0f4c2f"


def serving(monkeypatch, body: bytes) -> list[str]:
    asked = []

    def urlopen(url, timeout):
        asked.append(url)
        return io.BytesIO(body)

    monkeypatch.setattr(twin.urllib.request, "urlopen", urlopen)
    return asked


def test_the_cache_follows_xdg_cache_home(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    assert twin.cache_dir() == tmp_path / "agentenv-portsim/twin/b0f4c2f"
    monkeypatch.delenv("XDG_CACHE_HOME")
    assert twin.cache_dir().parent.parent.parent.name == ".cache"


def test_a_missing_file_is_downloaded_from_the_bucket_with_the_attribution(cache, monkeypatch):
    asked, said = serving(monkeypatch, GOOD), []
    assert twin.ensure(echo=said.append) == cache
    assert asked == [twin.BUCKET + "twin.json.gz"]
    assert (cache / "twin.json.gz").read_bytes() == GOOD
    assert [f.name for f in cache.iterdir()] == ["twin.json.gz"]
    assert len(said) == 1 and "© OpenStreetMap contributors (ODbL)" in said[0]


def test_valid_cached_files_are_not_downloaded_again(cache, monkeypatch):
    cache.mkdir(parents=True)
    (cache / "twin.json.gz").write_bytes(GOOD)
    asked, said = serving(monkeypatch, b"never read"), []
    assert twin.ensure(echo=said.append) == cache
    assert asked == said == []


def test_bytes_that_do_not_match_the_pin_raise_and_leave_nothing(cache, monkeypatch):
    serving(monkeypatch, b"something else")
    with pytest.raises(click.ClickException, match="sha256"):
        twin.ensure(echo=lambda _: None)
    assert list(cache.iterdir()) == []


@pytest.mark.network
def test_the_bucket_serves_the_pinned_files(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    root = twin.ensure(echo=lambda _: None)
    assert sorted(f.name for f in root.iterdir()) == sorted(twin.FILES)
