"""Builds the survey package in docs/design-explorations/package/:
  survey.html     one self-contained file (images embedded) a respondent opens on a phone or laptop
  collector.html  one file for the owner: paste codes or drop files, see the tallies, export CSV
  books/          the three interactive books (opened from the survey if the folder is kept together)
Run from the repo root: python3 docs/design-explorations/_source/package_build.py [whatsapp_number_digits] [email]
"""
import base64, io, json, os, shutil, sys
from PIL import Image

ROOT = "docs/design-explorations/"
OUT = ROOT + "package/"
WA_TO = sys.argv[1] if len(sys.argv) > 1 else ""
MAIL_TO = sys.argv[2] if len(sys.argv) > 2 else ""
DIRS = [("01-terminal", "01"), ("04-review-queue", "04"), ("17-clear-desk", "17")]
SHOTS = [("d1", "s1"), ("d2", "s2"), ("d5", "s3"), ("p1", "s4"), ("p2", "s5")]

# ----------------------------------------------------------------------------- texts: one source for survey and collector
T = {
 "en": dict(
  brand="Wasel · Design survey", intro_h="Help us choose a design",
  intro_p="Wasel tells an online seller which cash-on-delivery orders may be refused at the door, and writes the question to send the customer. You will see three designs of the same tool. All names, orders and amounts are test data. It takes about 5 minutes. You only tap; typing is always optional.",
  about="About you", start="Start", next="Next", back="Back", finish="Finish", design="Design", look="Look at the screens. Tap one to enlarge it.",
  open_full="Open the full version", need="Answer the three questions marked * to continue.", step="Step",
  s1="Orders list · laptop", s2="One order · laptop", s3="Money saved · laptop", s4="Orders list · phone", s5="One order · phone",
  q_role="What describes you best?", q_dev="What do you use every day?", q_lang="Which language would you want the tool in?",
  r1="I sell online and mostly use my phone", r2="I sell online and mostly use a laptop", r3="I manage orders for several shops", r4="I work in a team that handles orders", r5="Something else",
  phone="Phone", laptop="Laptop", both="Both", ar="Arabic", fr="French", en="English", mix="A mix",
  q_imp="Which words fit this design? (up to 3)", q_trust="Would you trust it with your orders?", t_lo="Not at all", t_hi="Completely",
  q_easy="Could you use it without help?", e_yes="Yes", e_little="With a little help", e_no="No",
  q_use="Where would you use it?", q_conf="What was confusing? (any)", q_like="What do you like? (any)", q_pay="How much would you pay per month?", q_note="Anything else about this design? (optional)",
  i_serious="Serious", i_friendly="Friendly", i_modern="Modern", i_old="Old-fashioned", i_cold="Cold", i_complicated="Complicated", i_clear="Clear", i_crowded="Crowded", i_trust="Trustworthy", i_hard="Hard to read",
  c_nothing="Nothing", c_risk="The risk names", c_next="The next steps", c_num="The numbers", c_col="The colours", c_hl="The highlighted words", c_btn="The buttons", c_much="Too much on the screen", c_small="Text too small",
  k_look="The look", k_col="The colours", k_risk="The risk labels", k_list="The list of orders", k_msg="The message to send", k_btn="The big button", k_money="The money saved page",
  p0="Nothing", p1="Under 20 TND", p2="20 to 50 TND", p3="50 to 100 TND", p4="100 to 200 TND", p5="200 TND or more",
  final_h="Now compare", q_fav="Which design would you choose?", q_worst="Which would you not choose?", none="None", q_theme="Light or dark screen?", th_light="Light", th_dark="Dark", th_both="Light, with a dark option",
  q_change="The one thing you would change (optional)", q_contact="Name or phone number, only if we may ask you more (optional)",
  send_h="Thank you", send_p="Please send us your answers. Choose one way.", wa="Send by WhatsApp", mail="Send by email", dl="Download the file", copy="Copy the code", copied="Copied", sent_note="Your answers are saved on this device until you send them.",
  design_letter="Design", write="Write something"),
 "fr": dict(
  brand="Wasel · Sondage design", intro_h="Aidez-nous à choisir un design",
  intro_p="Wasel indique à un vendeur en ligne quelles commandes payées à la livraison risquent d'être refusées à la porte, et rédige la question à envoyer au client. Vous allez voir trois designs du même outil. Tous les noms, commandes et montants sont des données de test. Cela prend environ 5 minutes. Vous touchez seulement; écrire est toujours facultatif.",
  about="À propos de vous", start="Commencer", next="Suivant", back="Retour", finish="Terminer", design="Design", look="Regardez les écrans. Touchez-en un pour l'agrandir.",
  open_full="Ouvrir la version complète", need="Répondez aux trois questions marquées * pour continuer.", step="Étape",
  s1="Liste des commandes · ordinateur", s2="Une commande · ordinateur", s3="Argent économisé · ordinateur", s4="Liste des commandes · téléphone", s5="Une commande · téléphone",
  q_role="Qu'est-ce qui vous décrit le mieux ?", q_dev="Que utilisez-vous chaque jour ?", q_lang="Dans quelle langue voulez-vous l'outil ?",
  r1="Je vends en ligne, surtout avec mon téléphone", r2="Je vends en ligne, surtout avec un ordinateur", r3="Je gère les commandes de plusieurs boutiques", r4="Je travaille dans une équipe qui traite les commandes", r5="Autre chose",
  phone="Téléphone", laptop="Ordinateur", both="Les deux", ar="Arabe", fr="Français", en="Anglais", mix="Un mélange",
  q_imp="Quels mots vont avec ce design ? (3 au maximum)", q_trust="Lui confieriez-vous vos commandes ?", t_lo="Pas du tout", t_hi="Complètement",
  q_easy="Pourriez-vous l'utiliser sans aide ?", e_yes="Oui", e_little="Avec un peu d'aide", e_no="Non",
  q_use="Où l'utiliseriez-vous ?", q_conf="Qu'est-ce qui était confus ? (plusieurs possibles)", q_like="Qu'est-ce que vous aimez ? (plusieurs possibles)", q_pay="Combien paieriez-vous par mois ?", q_note="Autre chose sur ce design ? (facultatif)",
  i_serious="Sérieux", i_friendly="Accueillant", i_modern="Moderne", i_old="Démodé", i_cold="Froid", i_complicated="Compliqué", i_clear="Clair", i_crowded="Chargé", i_trust="Digne de confiance", i_hard="Difficile à lire",
  c_nothing="Rien", c_risk="Les noms des risques", c_next="Les prochaines étapes", c_num="Les chiffres", c_col="Les couleurs", c_hl="Les mots surlignés", c_btn="Les boutons", c_much="Trop de choses à l'écran", c_small="Texte trop petit",
  k_look="L'apparence", k_col="Les couleurs", k_risk="Les étiquettes de risque", k_list="La liste des commandes", k_msg="Le message à envoyer", k_btn="Le grand bouton", k_money="La page argent économisé",
  p0="Rien", p1="Moins de 20 TND", p2="20 à 50 TND", p3="50 à 100 TND", p4="100 à 200 TND", p5="200 TND ou plus",
  final_h="Comparons", q_fav="Quel design choisiriez-vous ?", q_worst="Lequel ne choisiriez-vous pas ?", none="Aucun", q_theme="Écran clair ou sombre ?", th_light="Clair", th_dark="Sombre", th_both="Clair, avec option sombre",
  q_change="La seule chose que vous changeriez (facultatif)", q_contact="Nom ou numéro, seulement si nous pouvons vous poser d'autres questions (facultatif)",
  send_h="Merci", send_p="Envoyez-nous vos réponses. Choisissez une façon.", wa="Envoyer par WhatsApp", mail="Envoyer par e-mail", dl="Télécharger le fichier", copy="Copier le code", copied="Copié", sent_note="Vos réponses restent sur cet appareil jusqu'à l'envoi.",
  design_letter="Design", write="Écrire quelque chose"),
 "ar": dict(
  brand="واصل · استبيان التصميم", intro_h="ساعدنا في اختيار تصميم",
  intro_p="واصل يخبر البائع عبر الإنترنت أي الطلبات بالدفع عند الاستلام قد يُرفض عند الباب، ويكتب السؤال الذي يُرسل للزبون. سترى ثلاثة تصاميم لنفس الأداة. كل الأسماء والطلبات والمبالغ بيانات تجريبية. يستغرق نحو 5 دقائق. تضغط فقط، والكتابة اختيارية دائماً.",
  about="عنك", start="ابدأ", next="التالي", back="رجوع", finish="إنهاء", design="التصميم", look="شاهد الشاشات. المس واحدة لتكبيرها.",
  open_full="افتح النسخة الكاملة", need="أجب عن الأسئلة الثلاثة المعلّمة بـ * للمتابعة.", step="الخطوة",
  s1="قائمة الطلبات · حاسوب", s2="طلب واحد · حاسوب", s3="المال الموفَّر · حاسوب", s4="قائمة الطلبات · هاتف", s5="طلب واحد · هاتف",
  q_role="ما الذي يصفك أكثر؟", q_dev="ماذا تستعمل كل يوم؟", q_lang="بأي لغة تريد الأداة؟",
  r1="أبيع عبر الإنترنت وأستعمل هاتفي غالباً", r2="أبيع عبر الإنترنت وأستعمل حاسوباً غالباً", r3="أدير طلبات عدة محلات", r4="أعمل في فريق يعالج الطلبات", r5="شيء آخر",
  phone="هاتف", laptop="حاسوب", both="الاثنان", ar="العربية", fr="الفرنسية", en="الإنجليزية", mix="خليط",
  q_imp="ما الكلمات التي تناسب هذا التصميم؟ (حتى 3)", q_trust="هل تثق به لطلباتك؟", t_lo="أبداً", t_hi="تماماً",
  q_easy="هل تستطيع استعماله دون مساعدة؟", e_yes="نعم", e_little="بقليل من المساعدة", e_no="لا",
  q_use="أين ستستعمله؟", q_conf="ما الذي كان مربكاً؟ (أي عدد)", q_like="ما الذي يعجبك؟ (أي عدد)", q_pay="كم تدفع شهرياً؟", q_note="أي شيء آخر عن هذا التصميم؟ (اختياري)",
  i_serious="جاد", i_friendly="ودود", i_modern="عصري", i_old="قديم", i_cold="بارد", i_complicated="معقد", i_clear="واضح", i_crowded="مزدحم", i_trust="جدير بالثقة", i_hard="صعب القراءة",
  c_nothing="لا شيء", c_risk="أسماء المخاطر", c_next="الخطوات التالية", c_num="الأرقام", c_col="الألوان", c_hl="الكلمات المظلَّلة", c_btn="الأزرار", c_much="الكثير على الشاشة", c_small="الخط صغير",
  k_look="الشكل", k_col="الألوان", k_risk="تسميات الخطر", k_list="قائمة الطلبات", k_msg="الرسالة المراد إرسالها", k_btn="الزر الكبير", k_money="صفحة المال الموفَّر",
  p0="لا شيء", p1="أقل من 20 د.ت", p2="من 20 إلى 50 د.ت", p3="من 50 إلى 100 د.ت", p4="من 100 إلى 200 د.ت", p5="200 د.ت أو أكثر",
  final_h="الآن قارن", q_fav="أي تصميم تختار؟", q_worst="أي تصميم لن تختاره؟", none="لا شيء", q_theme="شاشة فاتحة أم داكنة؟", th_light="فاتحة", th_dark="داكنة", th_both="فاتحة مع خيار داكن",
  q_change="الشيء الوحيد الذي ستغيّره (اختياري)", q_contact="الاسم أو الرقم، فقط إن سمحت لنا بسؤالك أكثر (اختياري)",
  send_h="شكراً", send_p="أرسل لنا إجاباتك. اختر طريقة واحدة.", wa="أرسل عبر واتساب", mail="أرسل بالبريد", dl="نزّل الملف", copy="انسخ الرمز", copied="تم النسخ", sent_note="إجاباتك محفوظة على هذا الجهاز حتى ترسلها.",
  design_letter="التصميم", write="اكتب شيئاً"),
}

def opts(prefix, keys): return [[f"{prefix}_{k}" if prefix else k, ] for k in keys]

# generic question definitions: key, kind (one/many/scale/text), text key, option keys (also text keys), required, max
PROFILE = [
 dict(k="role", kind="one", q="q_role", o=["r1", "r2", "r3", "r4", "r5"], req=True),
 dict(k="dev", kind="one", q="q_dev", o=["phone", "laptop", "both"], req=True),
 dict(k="lang", kind="one", q="q_lang", o=["ar", "fr", "en", "mix"], req=True),
]
PER = [
 dict(k="trust", kind="scale", q="q_trust", o=["1", "2", "3", "4", "5"], req=True),
 dict(k="easy", kind="one", q="q_easy", o=["e_yes", "e_little", "e_no"], req=True),
 dict(k="use", kind="one", q="q_use", o=["phone", "laptop", "both"], req=True),
 dict(k="imp", kind="many", q="q_imp", o=["i_serious", "i_friendly", "i_modern", "i_old", "i_cold", "i_complicated", "i_clear", "i_crowded", "i_trust", "i_hard"], max=3),
 dict(k="conf", kind="many", q="q_conf", o=["c_nothing", "c_risk", "c_next", "c_num", "c_col", "c_hl", "c_btn", "c_much", "c_small"]),
 dict(k="like", kind="many", q="q_like", o=["k_look", "k_col", "k_risk", "k_list", "k_msg", "k_btn", "k_money"]),
 dict(k="pay", kind="one", q="q_pay", o=["p0", "p1", "p2", "p3", "p4", "p5"]),
 dict(k="note", kind="text", q="q_note"),
]
FINAL = [
 dict(k="fav", kind="design", q="q_fav"),
 dict(k="worst", kind="design", q="q_worst"),
 dict(k="theme", kind="one", q="q_theme", o=["th_light", "th_dark", "th_both"]),
 dict(k="change", kind="text", q="q_change"),
 dict(k="contact", kind="textshort", q="q_contact"),
]

def jpeg_b64(path, q=80):
    im = Image.open(path).convert("RGB")
    b = io.BytesIO(); im.save(b, "JPEG", quality=q, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()

def build():
    os.makedirs(OUT + "books", exist_ok=True)
    imgs = {}
    for did, n in DIRS:
        for x, cap in SHOTS:
            imgs[f"{n}-{x}"] = jpeg_b64(f"{ROOT}_package_src/shots/{did}-{x}.png")
        shutil.copy(f"{ROOT}book/{did}.html", f"{OUT}books/{did}.html")
    data = dict(T=T, PROFILE=PROFILE, PER=PER, FINAL=FINAL, IMGS=imgs, DIRS=[dict(id=n, file=f"books/{did}.html") for did, n in DIRS],
                SHOTS=[dict(img=x, cap=c) for x, c in SHOTS], WA=WA_TO, MAIL=MAIL_TO,
                NAMES={n: nm for (did, n), nm in zip(DIRS, ["Terminal Desk v2", "Review Desk", "Clear Desk"])})
    survey = open(ROOT + "_source/survey_template.html").read().replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False))
    open(OUT + "survey.html", "w").write(survey)
    cdata = dict(T=T["en"], PROFILE=PROFILE, PER=PER, FINAL=FINAL, NAMES=data["NAMES"])
    coll = open(ROOT + "_source/collector_template.html").read().replace("/*__DATA__*/null", json.dumps(cdata, ensure_ascii=False))
    open(OUT + "collector.html", "w").write(coll)
    for f in ("survey.html", "collector.html"):
        print(f, os.path.getsize(OUT + f) // 1024, "KB")

if __name__ == "__main__":
    build()
