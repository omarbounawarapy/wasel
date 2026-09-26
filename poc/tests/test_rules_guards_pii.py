import pytest

from pipeline import config
from pipeline.guards import check
from pipeline.pii import strip_pii
from pipeline.rules import action_for


@pytest.mark.parametrize("tier,value,expected", [
    ("Low", 50, "ship"), ("Low", 400, "ship"),
    ("Med", 50, "confirm_sms"), ("Med", 150, "confirm_sms_landmark"), ("Med", 400, "confirm_sms_landmark"),
    ("High", 149.9, "confirm_sms_landmark"), ("High", 150, "require_prepayment"), ("High", 900, "require_prepayment"),
])
def test_rules_table(tier, value, expected):
    assert action_for(tier, value) == expected


def test_every_action_has_a_label():
    assert set(config.RULES.values()) <= set(config.ACTION_LABELS)


# --- guards ---

def _o(value=210.0, items=1):
    return {"value_tnd": value, "item_count": items}


def test_guards_pass_grounded_derja_message():
    body = "Aslema, commande mte3ek (electronics, 210 DT) hadhra. Tnajem t2akedlna b 'EYH'?"
    assert check(body, _o(), "confirm_sms").approved


def test_guards_reject_invented_discount():
    v = check("Commande 210 DT, remise speciale pour vous! Confirmez?", _o(), "confirm_sms")
    assert not v.approved and not v.checks["no_discount_or_gift"]


def test_guards_reject_percentage_not_in_order():
    v = check("Confirmez et profitez de 20% de moins", _o(), "confirm_sms")
    assert not v.approved and not v.checks["no_percentages"]


def test_guards_reject_amount_not_in_order():
    v = check("Votre commande de 180 DT est prête. Confirmez?", _o(210.0), "confirm_sms")
    assert not v.checks["numbers_grounded"]


def test_guards_reject_card_details_request():
    v = check("Envoyez-nous le numéro de carte et le CVV pour confirmer", _o(), "require_prepayment")
    assert not v.checks["no_payment_details_request"]


def test_guards_reject_payment_when_not_authorized():
    v = check("Merci de faire un virement avant livraison", _o(), "confirm_sms")
    assert not v.checks["payment_only_if_authorized"]
    assert check("Un paiement avant livraison est nécessaire. OUI?", _o(), "require_prepayment").approved


def test_guards_reject_links_and_overlong():
    assert not check("Confirmez ici: https://bit.ly/x", _o(), "confirm_sms").checks["no_links"]
    assert not check("a" * 1000, _o(), "confirm_sms").checks["length_ok"]


def test_arabizi_digits_are_not_treated_as_amounts():
    assert check("t2akedlna b 'EYH', ab3athelna 3onwen", _o(), "confirm_sms").checks["numbers_grounded"]


# --- PII ---

@pytest.mark.parametrize("text", [
    "kalamni 3al 98 123 456", "appelez-moi au 22345678", "tel +216 55 123 456", "0021697123456",
    "كلمني على 98.123.456",
])
def test_pii_strips_tunisian_phones(text):
    out = strip_pii(text)
    assert "[PHONE]" in out
    assert not any(ch.isdigit() for ch in out.replace("3al", "").replace("216", ""))


def test_pii_keeps_address_numbers_intact():
    addr = "Rue Ibn Khaldoun n°12, Cité Ennasr 2, Ariana"
    assert strip_pii(addr) == addr


def test_pii_strips_self_declared_names():
    assert "Ahmed" not in strip_pii("esmi Ahmed, nestanna fih")
    assert "Salma" not in strip_pii("Je m'appelle Salma")
    assert "أحمد" not in strip_pii("اسمي أحمد")
