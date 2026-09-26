"""Synthetic COD order generator. No real customer data anywhere in this project.

Text is generated from latent variables only (address_quality, intent, register), never from the label,
and uses no giveaway words ("risky", "fake"). The refusal label is a logistic function of the latents
plus structured fields, with 10% of labels flipped so metrics don't look suspiciously clean.

Latent columns are kept in the CSV (prefixed latent_) for the extraction eval. They are never model features.

    python data/generate.py --n 300 --seed 42
"""
import argparse
import csv
import datetime as dt
import math
import random
from pathlib import Path

GOVERNORATES = [  # (name, weight, zone tier bias, cities latin, city arabic)
    ("Tunis", 18, "urban", ["Tunis", "La Marsa", "El Menzah"], "تونس"),
    ("Ariana", 10, "urban", ["Ariana", "Ennasr"], "أريانة"),
    ("Ben Arous", 8, "urban", ["Ben Arous", "El Mourouj"], "بن عروس"),
    ("Sfax", 10, "urban", ["Sfax"], "صفاقس"),
    ("Sousse", 9, "urban", ["Sousse"], "سوسة"),
    ("Nabeul", 7, "peri-urban", ["Nabeul", "Hammamet"], "نابل"),
    ("Monastir", 5, "peri-urban", ["Monastir"], "المنستير"),
    ("Bizerte", 5, "peri-urban", ["Bizerte"], "بنزرت"),
    ("Kairouan", 5, "peri-urban", ["Kairouan"], "القيروان"),
    ("Gabès", 4, "peri-urban", ["Gabès"], "قابس"),
    ("Medenine", 4, "remote", ["Medenine", "Djerba"], "مدنين"),
    ("Gafsa", 3, "remote", ["Gafsa"], "قفصة"),
    ("Kasserine", 3, "remote", ["Kasserine"], "القصرين"),
    ("Sidi Bouzid", 3, "remote", ["Sidi Bouzid"], "سيدي بوزيد"),
    ("Jendouba", 3, "remote", ["Jendouba"], "جندوبة"),
    ("Tataouine", 2, "remote", ["Tataouine"], "تطاوين"),
    ("Tozeur", 1, "remote", ["Tozeur"], "توزر"),
]
ZONE_ORDER = ["urban", "peri-urban", "remote"]

CATEGORIES = {  # (weight, median TND, sigma)
    "fashion": (30, 65, 0.45), "cosmetics": (20, 45, 0.4), "electronics": (15, 230, 0.55),
    "home": (15, 95, 0.5), "sports": (10, 85, 0.45), "kids": (10, 55, 0.4),
}
CHANNELS = [("facebook", 50), ("instagram", 30), ("website", 20)]
REGISTERS = [("derja_latin", 40), ("fr", 30), ("ar", 30)]

STREETS_L = ["Rue Ibn Khaldoun", "Avenue Habib Bourguiba", "Rue de Marseille", "Rue Farhat Hached",
             "Avenue de la Liberté", "Rue Tahar Haddad", "Nahj Mongi Slim", "Rue des Oliviers"]
STREETS_A = ["نهج ابن خلدون", "شارع الحبيب بورقيبة", "نهج فرحات حشاد", "نهج الطاهر الحداد", "نهج المنجي سليم"]
HOODS_L = ["Cité Ettadhamen", "Cité El Khadra", "Hay Ennour", "Cité Ennasr 2", "Cité Erriadh", "Cité El Amel"]
HOODS_A = ["حي الزهور", "حي النصر", "حي الرياض", "حي الأمل", "حي التضامن"]
LANDMARKS = {
    "derja_latin": ["9odem jem3a el kbira", "jenb el farmasia de nuit", "9odem el mdrsa el ibtida2iya", "7dhe el bousta"],
    "fr": ["en face de la mosquée", "à côté de la pharmacie de nuit", "en face de l'école primaire",
           "derrière la poste"],
    "ar": ["قدام الجامع الكبير", "بحذا الصيدلية", "قدام المدرسة الابتدائية", "وراء البريد"],
}
VAGUE = {  # attached to low-quality addresses
    "derja_latin": ["9rib mel centre", "fi jihet el gare", "ki twsel kalamni"],
    "fr": ["du côté de la gare", "près du centre", "quand vous arrivez, appelez"],
    "ar": ["قريب من المركز", "فما جهة المحطة", "كي توصل كلمني"],
}
NO_ADDRESS = {"derja_latin": ["ki twsel kalamni", "nafs el 3onwen", ""],
              "fr": ["même adresse que la dernière fois", ""], "ar": ["كي توصل كلمني", ""]}

# Notes per intent. Some phrasings are intentionally outside the heuristic lexicon (paraphrases),
# so the offline extractor is measurably imperfect, as a keyword matcher would be on real text.
NOTES = {
    "confident": {
        "derja_latin": ["ya3tik essa7a, nestanna fih", "Merci barcha, dispo toute la journée", "3aslema, ena fi dar"],
        "fr": ["Merci, je suis disponible toute la journée.", "Livraison rapide svp, merci",
               "Je serai à la maison après 17h, merci"],
        "ar": ["يعطيك الصحة، نستنى فيه", "بارك الله فيك", "نكون في الدار الكل نهار"],
    },
    "neutral": {
        "derja_latin": ["", "", "taille M", "couleur ka7la"],
        "fr": ["", "", "Taille L svp", "Couleur noire"],
        "ar": ["", "", "المقاس M", "اللون الأسود"],
    },
    "hesitant": {
        "derja_latin": ["nchouf ken ynasebni", "manich mt2akda mel couleur", "ken 3jebni nekhou",
                        "nchawer rajli 9bal", "mazal ma 5tartech el taille"],
        "fr": ["peut-être je le prends, je ne suis pas sûre de la taille", "si ça me plaît je garde",
               "j'hésite encore entre deux tailles"],
        "ar": ["مانيش متأكدة من المقاس", "نشوف كان يعجبني", "مازلت نخمم فيه"],
    },
    "reschedule": {
        "derja_latin": ["ab3athha ba3d jom3a", "mech tawa, ba3d el 3id", "ken tnajmou t2akhrouha chwaya"],
        "fr": ["je suis en voyage jusqu'à la semaine prochaine", "pas avant la semaine prochaine svp",
               "merci de livrer plus tard dans le mois"],
        "ar": ["راني مسافر، ابعثها بعد الجمعة", "موش توا، الجمعة الجاية"],
    },
    "third_party": {
        "derja_latin": ["khouya bech yestalem", "5aliha 3and el 3attar", "el 7ares ya5ou el colis"],
        "fr": ["c'est ma soeur qui va recevoir", "ma mère va récupérer le colis", "laissez-le chez le gardien"],
        "ar": ["خلّيها عند الجار", "خويا باش يستلم"],
    },
}
INTENT_W = [("confident", 25), ("neutral", 35), ("hesitant", 15), ("reschedule", 12), ("third_party", 13)]
PHONE_NOTES = {"derja_latin": "kalamni 3al {p}", "fr": "appelez-moi au {p}", "ar": "كلمني على {p}"}


def pick(rng, weighted):
    items, weights = zip(*weighted)
    return rng.choices(items, weights=weights, k=1)[0]


def fake_phone(rng) -> str:
    d = rng.choice("2459") + "".join(rng.choice("0123456789") for _ in range(7))
    return f"{d[:2]} {d[2:5]} {d[5:]}"


def make_address(rng, q, reg, city_l, city_a) -> str:
    city = city_a if reg == "ar" else city_l
    hood = rng.choice(HOODS_A if reg == "ar" else HOODS_L)
    if q == 3:
        if rng.random() < 0.6:
            street = rng.choice(STREETS_A) + f" عدد {rng.randint(1, 120)}" if reg == "ar" else \
                f"{rng.choice(STREETS_L)} n°{rng.randint(1, 120)}"
            return f"{street}، {hood}، {city}" if reg == "ar" else f"{street}, {hood}, {city}"
        lm = rng.choice(LANDMARKS[reg])
        return f"{hood}، {lm}، {city}" if reg == "ar" else f"{hood}, {lm}, {city}"
    if q == 2:
        return f"{hood}، {city}" if reg == "ar" else f"{hood}, {city}"
    if q == 1:
        if rng.random() < 0.5:
            v = rng.choice(VAGUE[reg])
            return f"{city}، {v}" if reg == "ar" else f"{city}, {v}"
        return city
    return rng.choice(NO_ADDRESS[reg])


def generate(n: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    start = dt.datetime(2026, 7, 25, tzinfo=None)
    rows = []
    for i in range(n):
        gov, _, zone_bias, cities, city_a = pick(rng, [(g, g[1]) for g in GOVERNORATES])
        zone = zone_bias if rng.random() < 0.8 else rng.choice(ZONE_ORDER)
        reg = pick(rng, REGISTERS)
        reliability = rng.gauss(0, 1)
        q = pick(rng, [(3, 40), (2, 25), (1, 22), (0, 13)])
        intent = pick(rng, INTENT_W)
        cat = pick(rng, [(c, v[0]) for c, v in CATEGORIES.items()])
        _, median, sigma = CATEGORIES[cat]
        value = round(math.exp(rng.gauss(math.log(median), sigma)), 1)
        items = min(5, 1 + int(rng.expovariate(1.2)))
        channel = pick(rng, CHANNELS)
        prior = max(0, int(rng.gauss(1.5 + reliability, 1.8)))
        base_refuse = 1 / (1 + math.exp(1.2 + 1.2 * reliability))
        prior_ref = sum(rng.random() < base_refuse for _ in range(prior))
        hour = pick(rng, [(h, 1 + (3 if 18 <= h <= 23 else 0) + (1 if 12 <= h <= 14 else 0)) for h in range(24)])
        created = start + dt.timedelta(days=rng.randint(0, 59), hours=hour, minutes=rng.randint(0, 59))

        note = rng.choice(NOTES[intent][reg])
        if rng.random() < 0.1:
            p = PHONE_NOTES[reg].format(p=fake_phone(rng))
            note = f"{note}, {p}" if note else p

        logit = (-2.9 + {"urban": 0, "peri-urban": 0.7, "remote": 1.5}[zone] + 0.8 * (3 - q)
                 + {"confident": -1.2, "neutral": 0, "hesitant": 1.9, "reschedule": 1.6, "third_party": 1.0}[intent]
                 + 2.5 * (prior_ref / prior if prior else 0) + (0.6 if prior == 0 else -0.15 * min(prior, 5))
                 + 0.5 * math.log(value / 80) - 0.3 * reliability
                 + (0.25 if channel != "website" else -0.2) + (0.3 if hour >= 23 or hour <= 4 else 0))
        refused = rng.random() < 1 / (1 + math.exp(-logit))
        if rng.random() < 0.10:
            refused = not refused

        rows.append({
            "order_id": f"ORD-{1001 + i}", "created_at": created.isoformat(timespec="minutes"),
            "governorate": gov, "zone_tier": zone,
            "address_text": make_address(rng, q, reg, rng.choice(cities), city_a), "note_text": note,
            "product_category": cat, "value_tnd": value, "item_count": items, "channel": channel,
            "is_first_order": int(prior == 0), "prior_orders": prior, "prior_refusals": prior_ref,
            "refused": int(refused),
            "latent_address_quality": q, "latent_intent": intent, "latent_register": reg,
        })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=str(Path(__file__).parent / "orders.csv"))
    a = ap.parse_args()
    rows = generate(a.n, a.seed)
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows, refusal rate {sum(r['refused'] for r in rows) / len(rows):.1%} -> {a.out}")


if __name__ == "__main__":
    main()
