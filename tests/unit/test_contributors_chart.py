"""scripts/dev/contributors_chart.py: identities are merged by handle, bots and chart commits are not counted."""
import importlib.util
from collections import Counter

from wasel.paths import ROOT

spec = importlib.util.spec_from_file_location("contributors_chart", ROOT / "scripts" / "dev" / "contributors_chart.py")
chart = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chart)


def test_one_person_under_several_identities_is_one_slice():
    assert chart.handle("Omar Bounawara", "omar.bounawara.py@gmail.com") == "omarbounawarapy"
    assert chart.handle("omarbounawarapy", "omar.bounawara.py@gmail.com") == "omarbounawarapy"
    assert chart.handle("monta", "montaassarr@users.noreply.github.com") == "montaassarr"
    assert chart.handle("Montassar", "montaassarr@users.noreply.github.com") == "montaassarr"
    assert chart.handle("mohamed aziz riahi", "164111575+azaizoz@users.noreply.github.com") == "azaizoz"
    assert chart.handle("riahi aziz", "riahiaziz199@gmail.com") == "azaizoz"
    assert chart.handle("Someone", "someone@example.com") == "Someone"       # unknown: the commit name
    assert chart.handle("dependabot[bot]", "49699333+dependabot[bot]@users.noreply.github.com") is None


def test_svg_has_a_slice_and_a_percentage_per_person():
    svg = chart.render(Counter({"a": 3, "b": 1}))
    assert svg.count("<path") == 2 and "75.0% · 3 commits" in svg and "25.0% · 1 commit<" in svg
    assert "<circle" in chart.render(Counter({"solo": 5}))                      # one person: a full disc, not an arc
    assert chart.render(Counter()).startswith("<svg")                           # empty history does not crash
