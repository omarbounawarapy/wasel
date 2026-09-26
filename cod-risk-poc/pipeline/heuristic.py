"""Offline, rule-based extractor with the same output contract as the LLM.

Used when no LLM key is configured, so the app runs anywhere. It is a keyword lexicon, not NLP:
it misses paraphrases the LLM catches, and the UI labels every result it produces as "heuristic".
"""
import re

from .schemas import Flags, RedFlag

_I = re.IGNORECASE

RED_FLAG_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("vague_location", re.compile(
        r"(9rib|qrib|9reb)\s+(mel|men|mil|m[ae]l)\s+\w+|fi jih(e|a)t\s+\w+|du côté d[e']\s?\w*|"
        r"quelque part\s?\w*|près du centre|ki t?w?(ou|u|o)?s(e|a)l\s+\w+|"
        r"quand vous arrivez,? appelez|قريب من\s?\S*|فما جهة\s?\S*|كي توصل\s?\S*|"
        r"même adresse|nafs? el ?3onw(e|a)n", _I)),
    ("reschedule", re.compile(
        r"ba3d (jom3a|joum3a|ghodwa|el 3id|chhar)|pas avant\s+[\w\s]{0,20}?(semaine|lundi|mois)|"
        r"je suis en voyage[\w\s']{0,20}|ab3ath(ha|ou)? ba3d\s?\w*|report(er|ez) la livraison|"
        r"راني مسافر|ابعثها بعد\s?\S*|بعد الجمعة|wa9t nekhle?s\s?\w*|mech tawa|moch tawa", _I)),
    ("hesitation", re.compile(
        r"nchouf ken\s?\w*|peut[- ]être\s?\w*|mani(ch|sh) (mt2akd(a|ed)?|metakd(a|ed)?)|"
        r"مانيش متأكد[ةه]?|ken 3jebni\s?\w*|si (ça|ca) me pla[iî]t|nchawer\s+\w+|"
        r"belk?e?k nbadel ra2yi|je ne suis pas s[uû]re?|mazelt ma \w+|نشوف|بلكشي نبدل", _I)),
    ("third_party_receiver", re.compile(
        r"(khouya|o5ti|okhti|bouya|ommi|jari|el jar|l voisin|le voisin)\s+(bech|bch|ba4)\s+\w+|"
        r"c'est (ma|mon)\s+\w+\s+qui (va )?(recevoir|récupérer)|"
        r"(ma mère|mon frère|ma s(oe|œ)ur|mon mari|le gardien)\s+(va|pourra)\s+(recevoir|récupérer)|"
        r"(5al|khal)(liha|iha|lih) (3and|3end)\s+\w+(\s+\w+)?|خلّ?يها عند\s?\S*|خويا باش\s?\S*", _I)),
    # Text aimed at the AI rather than the shop. Flagged, never obeyed.
    ("other", re.compile(
        r"ignore (all |the )?(previous|prior|above) instructions[^.\n]*|system prompt|"
        r"this order is (low|no) risk|تجاهل (كل )?التعليمات[^.\n]*|ignorez les instructions[^.\n]*", _I)),
]

_STREET = re.compile(r"\b(rue|avenue|av\.|nahj|nehj|boulevard|bd|route|immeuble|imm\.?|appt|étage|n°)\b|"
                     r"نهج|شارع|طريق|عمارة", _I)
_LANDMARK = re.compile(r"\b(9odem|9oddem|qodem|en face d[eu']|face à|à côté d[eu']|jenb|b?7dhe|derrière|wra)\b"
                       r"[^,.;]{0,25}\b(mosqu[ée]e|jem3a|jame3|pharmacie|farmasia|école|ecole|mdrsa|"
                       r"lyc[ée]e|poste|bousta|station|hammam|caf[ée]|kiosque|banque|clinique)\b|"
                       r"(قدام|بحذا|حذا|بجانب|وراء)\s+(ال)?(جامع|صيدلية|مدرسة|ليسي|البريد|الحمام|البنك|المصحة)", _I)
_NEIGHBORHOOD = re.compile(r"\b(cit[ée]|cite|hay|quartier|résidence|residence)\b|حي\s", _I)
_CITIES = re.compile(
    r"\b(tunis|ariana|ben arous|manouba|nabeul|zaghouan|bizerte|béja|beja|jendouba|kef|siliana|sousse|"
    r"monastir|mahdia|sfax|kairouan|kasserine|sidi bouzid|gab[eè]s|medenine|m[ée]denine|tataouine|"
    r"gafsa|tozeur|k[ée]bili|la marsa|hammamet|djerba|ennasr|menzah|mourouj)\b|"
    r"تونس|أريانة|بن عروس|منوبة|نابل|زغوان|بنزرت|باجة|جندوبة|الكاف|سليانة|سوسة|المنستير|المهدية|صفاقس|"
    r"القيروان|القصرين|سيدي بوزيد|قابس|مدنين|تطاوين|قفصة|توزر|قبلي", _I)

_CONFIDENT = re.compile(r"merci|ya3tik essa7a|بارك الله|disponible|nestanna|n(e|a)stanna|urgent|rapidement|"
                        r"متوفر|نستنى|يعطيك الصحة", _I)
_HOSTILE = re.compile(r"arnaque|escroc|voleur|n7el|manich khalss|ما نخلصش", _I)
_DERJA_LATIN = re.compile(r"\b\w*[a-z][379]\w*\b|\b(bech|ken|mel|fi|w|chouf|tawa|barcha)\b", _I)
_DERJA_AR = re.compile(r"راني|مانيش|باش|برشا|توا|خلّ?يها|خويا|نشوف|كي")
_FRENCH = re.compile(r"\b(le|la|les|de|du|des|je|vous|est|suis|avec|pour|pas|merci|rue|près)\b", _I)
_ARABIC_CHAR = re.compile(r"[؀-ۿ]")


def _language(text: str) -> str:
    if not text.strip():
        return "mixed"
    ar = len(_ARABIC_CHAR.findall(text))
    latin = len(re.findall(r"[A-Za-zÀ-ÿ]", text))
    if ar and latin and min(ar, latin) / max(ar, latin) > 0.25:
        return "mixed"
    if ar > latin:
        return "derja_arabic_script" if _DERJA_AR.search(text) else "ar"
    derja, fr = len(_DERJA_LATIN.findall(text)), len(_FRENCH.findall(text))
    if derja and fr:
        return "derja_latin" if derja > fr else ("fr" if fr > 2 * derja else "mixed")
    return "derja_latin" if derja else "fr"


def heuristic_extract(address: str, note: str) -> Flags:
    text = f"{address}\n{note}"
    red_flags: list[RedFlag] = []
    for ftype, pat in RED_FLAG_PATTERNS:
        for m in pat.finditer(text):
            phrase = m.group(0).strip()
            if phrase and not any(phrase == f.text for f in red_flags):
                red_flags.append(RedFlag(text=phrase, type=ftype))

    has_landmark = bool(_LANDMARK.search(address))
    if _STREET.search(address) or has_landmark:
        spec = 3
    elif _NEIGHBORHOOD.search(address):
        spec = 2
    elif _CITIES.search(address):
        spec = 1
    else:
        spec = 0

    types = {f.type for f in red_flags}
    if _HOSTILE.search(text):
        tone = "hostile"
    elif "hesitation" in types:
        tone = "hesitant"
    elif _CONFIDENT.search(note):
        tone = "confident"
    else:
        tone = "neutral"

    return Flags(
        language=_language(note if note.strip() else address),
        address_specificity=spec,
        has_landmark=has_landmark,
        red_flags=red_flags,
        tone=tone,
        reschedule_requested="reschedule" in types,
    )
