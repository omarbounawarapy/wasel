"""Per-address limits: the address a request counts under, the windows and the LLM share."""
from datetime import timedelta

import pytest

from tests.conftest import T0
from wasel.db.conn import fresh_db
from wasel.db.usage import SqliteUsageMeter
from wasel.ratelimit import AddressLimiter, client_address


@pytest.mark.parametrize("peer,headers,header,expected", [
    ("9.9.9.9", {}, "", "9.9.9.9"),                                    # direct connection
    ("10.0.0.5", {}, "", None),                                        # behind a proxy we were not told about
    ("127.0.0.1", {"cf-connecting-ip": "8.8.8.8"}, "cf-connecting-ip", "8.8.8.8"),
    ("127.0.0.1", {"x-forwarded-for": "8.8.8.8"}, "", None),           # untrusted header is ignored
    ("9.9.9.9", {"cf-connecting-ip": "not an ip"}, "cf-connecting-ip", None),
    ("127.0.0.1", {"cf-connecting-ip": "10.1.1.1"}, "cf-connecting-ip", None),
    ("127.0.0.1", {"cf-connecting-ip": "2001:db8::1"}, "cf-connecting-ip", None),   # documentation range is not public
    ("127.0.0.1", {"cf-connecting-ip": "2606:4700::1111"}, "cf-connecting-ip", "2606:4700::/64"),
])
def test_client_address(peer, headers, header, expected):
    assert client_address(peer, headers, header) == expected


def test_write_window_slides():
    lim = AddressLimiter()
    assert [lim.hit_write("a", t, 3, 600) for t in (0, 1, 2)] == [None] * 3
    assert lim.hit_write("a", 3, 3, 600) == 597                      # until the first write leaves the window
    assert lim.hit_write("b", 3, 3, 600) is None                     # another address
    assert lim.hit_write("a", 601, 3, 600) is None


def test_the_ids_of_one_address_share_the_llm_budget(tmp_path):
    lim = AddressLimiter()
    for v in "abcd":
        lim.note_visitor("1.2.3.4", v, 0)
    lim.note_visitor("5.6.7.8", "z", 0)
    meter = SqliteUsageMeter(fresh_db(tmp_path / "u.db"), daily_cap=100, public=True, visitor_10min=6, visitor_day=20,
                             siblings=lim.siblings, address_cap=3)
    assert [meter.allow("extract", v, T0) for v in "abc"] == ["ok"] * 3
    assert meter.allow("extract", "d", T0) == "visitor_cap"           # a fourth id, same address
    assert meter.allow("extract", "z", T0 + timedelta(seconds=1)) == "ok"
