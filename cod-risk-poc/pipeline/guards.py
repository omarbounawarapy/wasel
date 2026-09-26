"""Deterministic checks on any outbound draft, run before the LLM judge. Cheap and never flaky."""
import re

from .schemas import Verdict

MAX_LEN = 450

_DISCOUNT = re.compile(r"remise|réduction|reduction|promo|solde|gratuit|cadeau|discount|\bfree\b|offert|"
                       r"تخفيض|تخفيضات|هدية|مجانا|مجاني|ta5fidh|takhfidh", re.IGNORECASE)
_PAYMENT_DETAILS = re.compile(r"carte bancaire|num[ée]ro de (la )?carte|card number|\bcvv\b|\bcvc\b|\brib\b|"
                              r"mot de passe|password|code (secret|sms|de confirmation)|\bpin\b|"
                              r"كلمة السر|رقم البطاقة|الكود السري", re.IGNORECASE)
_PAYMENT_ANY = re.compile(r"paiement|payer|prépaiement|prepaiement|khlas|t5alles|tkhalles|خلاص|الدفع|تخلص|"
                          r"virement|d17|flouci", re.IGNORECASE)
_LINK = re.compile(r"https?://|www\.|\.com\b|\.tn\b|bit\.ly", re.IGNORECASE)
_PERCENT = re.compile(r"\d\s*%|%\s*\d|بالمية|pourcent", re.IGNORECASE)
# Standalone numbers only: Arabizi digits (t2aked, 3onwen) sit inside words and are letters there.
_NUMBER = re.compile(r"(?<![A-Za-z\d])\d+(?:[.,]\d+)?(?![A-Za-z\d])")


def _fmt_numbers(value_tnd: float, item_count: int) -> set[str]:
    allowed = {str(item_count), f"{value_tnd:.0f}", f"{value_tnd:.1f}", f"{value_tnd:.2f}",
               f"{value_tnd:.1f}".replace(".", ","), f"{value_tnd:.2f}".replace(".", ",")}
    if value_tnd == int(value_tnd):
        allowed.add(str(int(value_tnd)))
    return allowed


def check(body: str, order: dict, action: str) -> Verdict:
    checks = {
        "length_ok": 0 < len(body) <= MAX_LEN,
        "no_discount_or_gift": not _DISCOUNT.search(body),
        "no_percentages": not _PERCENT.search(body),
        "numbers_grounded": all(n in _fmt_numbers(float(order["value_tnd"]), int(order["item_count"]))
                                for n in _NUMBER.findall(body)),
        "no_payment_details_request": not _PAYMENT_DETAILS.search(body),
        "payment_only_if_authorized": action == "require_prepayment" or not _PAYMENT_ANY.search(body),
        "no_links": not _LINK.search(body),
    }
    failed = [k for k, ok in checks.items() if not ok]
    return Verdict(approved=not failed, checks=checks, source="guards",
                   reason="guards passed" if not failed else "guards failed: " + ", ".join(failed))
