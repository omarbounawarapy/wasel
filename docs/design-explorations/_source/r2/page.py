SCHOOLS=[
 ("Swiss / International Style","Grid as the main instrument, one neutral grotesk, hierarchy by scale. Spread through corporate identity programmes into screens.","Visible structure and measured density.","The grid as decoration."),
 ("Braun / Rams, then Apple","“Less, but better.” Objects that tell you what they are. Apple's clarity, deference, depth descends from it.","Deference: the UI never competes with the order text.","Skeuomorphic gloss, glass everywhere."),
 ("Kenya Hara / Muji","Emptiness, not simplicity: remove what tells you what to think.","Quiet defaults, no brand noise next to customer words.","Blankness that hides state."),
 ("Paul Rand","A logo identifies; meaning comes from the thing it stands for. UPS: a shield with a parcel on top, and a joke.","One idea, a touch of wit, built from the product's own object.","Stock symbols (shield, check, globe)."),
 ("Linear / Bloomberg: taste as product judgement","Opinionated defaults, speed, craft over A/B tests; design is not decoration.","Decide for the seller: one recommended next step per order.","Ornament standing in for decisions."),
 ("Tunisian and Maghrebi graphic tradition","Mahdaoui's abstract calligraphy as signs; zellige geometry; Sidi Bou Said blue and white; bilingual Arabic-French print.","A local palette and geometry the seller already knows.","Tourist-poster arabesque."),
 ("Postal and courier print culture","Cancellation marks, waybills, carbon copies, rubber stamps: verdicts made visible.","One authored verdict mark per order.","Stamps and texture everywhere."),
 ("Wayfinding / transit diagrams","Lines at 45 and 90 degrees, stations, one colour per line: movement as a promise.","Order journey drawn as a line that changes colour.","Shrinking a network into an unreadable miniature."),
]
SEVEN=[
 ("Courier waybills and rubber stamps","bordereau de livraison, duplicate carbon sheets, the verdict stamp","Every seller has handled the paper this product replaces. A stamp states a decision.","PICK"),
 ("The studded blue door","Sidi Bou Said doors, nail-head patterns, whitewash and cobalt","The refusal happens at the door. Studs could count the reasons.",""),
 ("The Tunis light-rail diagram","Métro léger line colours, station order, terminus","Order status is already a journey with a terminus.",""),
 ("Hand-painted shop signs (enseignes)","signwriter enamel, bilingual lettering, price boards","Everyday street typography; strong colour, weak fit for dense data.",""),
 ("Zellige and Maghrebi tile geometry","glazed cobalt, turquoise, saffron, clay; the eight-point khatem star made of two squares","A tile is a unit. Two squares (two parcels) rotate into the star: a mark and a reasoning grid.","ASSIGNED"),
 ("Banknote and ID security print","guilloche lines, microprint, bilingual forms","Authenticity of a quote could be shown with fine-line pattern; hard to read at density.",""),
 ("The souk scale and weights","brass weights, balance beam","Weighing reasons is apt, but it is an instrument costume.",""),
]
DIRS=[
 dict(k="A",tag="ASSIGNED BY THE ROLL",name="Mosaïque",world="Zellige and Maghrebi tile geometry",screen=A,logo=logo_khatem(120),
  fonts="Hanken Grotesk (Latin) + Noto Kufi Arabic",pal=[("#123f93","cobalt, rail and primary"),("#12958f","turquoise, lowers risk"),("#dca017","saffron, medium"),("#b8442c","clay, raises risk"),("#f3f6fa","whitewash ground")],
  idea="A zellige panel is made of identical glazed units set to a rule. Wasel's score is made of reasons that each move it by a few points. So the reasons become tiles: one small glazed square is about 3 points, clay raises the risk, turquoise lowers it. In the list the tiles form a short strip you read like a bar; in the detail the same tiles stack into a panel, and the 'if they give a full address' panel sits under it at the same scale, so v1 to v2 is seen as clay turning to turquoise. The logo comes from the same geometry: two squares (two parcels, seller and customer) turn 45 degrees into the khatem star. It is the one decorative form; everything else is a standard, quiet product screen.",
  lends="type: geometric grotesk + Kufi · palette: cobalt rail, glaze colours as state · density: compact table · move: reasons as glazed tiles",
  risk="Maghrebi geometry is the tourist-poster rut. The defence is restraint: one tile unit, no tessellated backgrounds, no arabesque borders. The star must read as two squares first, not as a generic Islamic star."),
 dict(k="B",tag="IMPECCABLE'S PICK",name="Bordereau",world="Courier waybills and rubber stamps",screen=B,logo=logo_roundel(120),
  fonts="Archivo (narrow widths for labels) + Courier Prime for order numbers and amounts only + Readex Pro for Arabic",pal=[("#1d36a3","carbon-copy blue, rail and primary"),("#c8102e","stamp red, high risk"),("#f6d6dd","pink copy"),("#fbf3c4","yellow copy"),("#ffffff","original sheet")],
  idea="Sellers know the paper this product replaces: the courier's duplicate waybill, filled in by hand, stamped when something is decided. Wasel already makes one decision per order, so that decision gets one authored verdict stamp on the order (CONFIRMER L'ADRESSE), set slightly off-square like a real stamp. The score history uses the copies: the white original is v1, the pink copy is v2. Order numbers and amounts are set in a typewriter face because they are typed data; everything else is a clean sans. The logo is a postmark roundel with the door in it, and the wavy cancellation lines trail off it.",
  lends="type: narrow grotesk + typewriter for data · palette: carbon blue, stamp red, copy tints · density: form-dense but standard table · move: one verdict stamp, versions as carbon copies",
  risk="Stamps and form textures are an easy costume. The rule is one stamp per order and no ruled-paper table. The roundel logo must not look like a post office."),
 dict(k="C",tag="CHALLENGER · COMPETITIVE",name="Ligne",world="Metropolitan rail diagram (Tunis light rail)",screen=C,logo=logo_line(120),
  fonts="Overpass (signage humanist) + Tajawal for Arabic",pal=[("#0d1b3d","midnight enamel, rail"),("#d63a2f","line red, high risk"),("#e39b12","line amber, medium"),("#1f8a5b","line green, low risk"),("#f5f6f4","porcelain ground")],
  idea="An order is already a journey: message, scored, question asked, reply, rescored, shipped, the door. Draw it as a transit line with stations. The line is red while the risk is high; when the customer replies with a full address it turns green from the station 'Rescored', and a dashed branch shows 'Refused' as the diversion that costs money. In the list each order carries a seven-dot mini journey. The logo is the same grammar: a line leaving a station and ending at a door.",
  lends="type: wayfinding humanist · palette: midnight shell, line colours as risk · density: signage-clear · move: order journey as a line that changes colour",
  risk="The line must carry real states only. Verdict: competitive. It beats the assignment on product clarity (the journey is a real need) but identification is narrower than the tile or stamp for sellers outside Tunis."),
 dict(k="D",tag="CHALLENGER · COMPETITIVE",name="Module",world="Wim Crouwel gridded letterforms",screen=D,logo=logo_cells(120),
  fonts="Schibsted Grotesk + Almarai for Arabic; score numerals drawn on a 3×5 cell grid",pal=[("#101010","ink"),("#ffffff","white ground"),("#ff4a1c","signal plane, high risk only"),("#2f9e6e","green, low risk"),("#c9d3e6","construction grid blue")],
  idea="Every number in Wasel is a measurement. Crouwel built letterforms from visible cells, so the score is drawn as grid digits (87 above), the page keeps a faint construction grid you can switch on, and the logo is the door built from the same 6 by 6 cells. Colour is nearly absent: ink and white, with one signal plane that appears only when risk is high.",
  lends="type: neutral grotesk + grid-built numerals · palette: ink, white, one signal plane · density: measured · move: score numerals built from cells",
  risk="Crouwel is Dutch and reads cold; identification with Tunisian sellers is weak. Verdict: competitive on clarity only. The discipline kept is the visible baseline grid and the measured density."),
]
DECLINED=[("Dark-first developer console","Declined: the user is a seller, not a developer.","Kept: the destructive action is isolated. Cancel order now sits apart from the other buttons in every direction."),
 ("Botanical folio plates","Declined: warm cream is already spent and the subject is wrong.","Kept: same-scale plates. The 'now' and 'if they reply' panels are drawn at identical scale so the change reads at a glance."),
 ("Variable-font specimen","Declined: audience gets nothing from a type playground.","Kept: weight as meaning. The top reason is set heavier than the rest instead of using a coloured pill."),
 ("Convention circle catalogue","Declined: wrong audience and density.","Kept: hand marks for state. Orders the seller has already handled can be marked seen, not just coloured.")]
FONTS="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600;700&family=Noto+Kufi+Arabic:wght@500;700&family=Archivo:wdth,wght@62..125,400..800&family=Courier+Prime:wght@400;700&family=Readex+Pro:wght@400;600&family=Overpass:wght@400;600;700&family=Tajawal:wght@500;700&family=Schibsted+Grotesk:wght@400;500;700&family=Almarai:wght@400;700&display=swap"
def card(d):
    pal=''.join(f'<span class="sw2"><i style="background:{c}"></i><b>{c}</b><em>{esc(n)}</em></span>' for c,n in d["pal"])
    return f'''<article class="dir" id="d{d["k"]}"><header><span class="badge">{d["tag"]}</span><h2>{d["name"]}</h2><p>World: {esc(d["world"])}</p></header>
<div class="two"><div><h4>Design idea, written before drawing</h4><p>{esc(d["idea"])}</p><h4>What the world lends (Operate rules)</h4><p class="lend">{esc(d["lends"])}</p><h4>Honest risk</h4><p>{esc(d["risk"])}</p></div>
<div class="kit"><div class="lg">{d["logo"]}<span>Logo derived from the world</span></div><p class="fonts">{esc(d["fonts"])}</p><div class="pal">{pal}</div></div></div>
<div class="frame">{d["screen"]}</div></article>'''
def schools():
    return ''.join(f'<tr><th scope="row">{esc(a)}</th><td>{esc(b)}</td><td>{esc(c)}</td><td>{esc(e)}</td></tr>' for a,b,c,e in SCHOOLS)
def seven():
    return ''.join(f'<li class="{"asg" if t=="ASSIGNED" else "pk" if t=="PICK" else ""}"><b>{i+1}. {esc(n)}</b>{"<em>"+t+"</em>" if t else ""}<span>{esc(a)}</span><p>{esc(why)}</p></li>' for i,(n,a,why,t) in enumerate(SEVEN))
css=open('page.css').read()
out=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Wasel Brand Directions, Round 2</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="{FONTS}" rel="stylesheet"><style>{css}</style></head><body>
<header class="top"><h1>Wasel: brand directions, round 2</h1>
<p class="lead">Redone from research. The first six directions broke rules I then read in the skill's own refuse list (eyebrow labels, hero-number templates, glass and gradient tiles, Inter, instrument and newspaper costumes). This round starts from what real brand schools teach, then from the seller's own Tunisian world, and lets the world lend only type, palette, density and one signature move.</p>
<nav class="jump"><a href="#studied">What I studied</a><a href="#seven">Seven worlds</a><a href="#dA">A Mosaïque</a><a href="#dB">B Bordereau</a><a href="#dC">C Ligne</a><a href="#dD">D Module</a><a href="#declined">Declined</a></nav></header>
<main>
<section id="studied"><h2>What I studied and what I took</h2>
<table class="sch"><thead><tr><th>School</th><th>What it teaches</th><th>Taken for Wasel</th><th>Refused</th></tr></thead><tbody>{schools()}</tbody></table>
<p class="src">Sources: <a href="https://blakecrosley.com/blog/design-philosophy-kenya-hara">Kenya Hara</a> · <a href="https://medium.com/design-bootcamp/the-bauhaus-ui-in-your-pocket-7c30a83b932f">Bauhaus to screen</a> · <a href="https://medium.com/@dineshgoundla/the-iconic-design-legacy-of-braun-and-dieter-rams-how-their-philosophy-revolutionized-product-d352df967903">Braun and Rams</a> · <a href="https://en.wikipedia.org/wiki/Paul_Rand">Paul Rand</a> · <a href="https://www.lennysnewsletter.com/p/inside-linear-building-with-taste">Linear</a> · <a href="https://en.wikipedia.org/wiki/Nja_Mahdaoui">Nja Mahdaoui</a> · <a href="https://en.wikipedia.org/wiki/Cancellation_(mail)">postal cancellation</a> · <a href="https://blakecrosley.com/guides/design/teenage-engineering">Teenage Engineering</a> · <a href="https://www.mintlify.com/pbakaus/impeccable/concepts/anti-patterns">AI anti-patterns</a> · <a href="https://blog.29lt.com/2017/06/07/29lt-bukra-type-family/">29LT bilingual type</a></p></section>
<section id="seven"><h2>Seven worlds from the seller's Tunisia, ordered by resonance</h2><ul class="seven">{seven()}</ul>
<p class="src">The roll (not my taste) assigned #5. #1 is my own top pick and is shown as the pick card. Two challengers from the catalogue were fused and judged competitive (C, D); four were declined, below.</p></section>
{"".join(card(d) for d in DIRS)}
<section id="declined"><h2>Declined challengers and what the build kept from each</h2><ul class="dec">{''.join(f"<li><b>{n}</b><span>{v}</span><p>{k}</p></li>" for n,v,k in DECLINED)}</ul>
<h3>The standing exit</h3><p>If you prefer the category standard played straight (a clean light dashboard in the manner of Stripe or Linear, no world at all), say so and that becomes the commitment at full fidelity. I have not recommended it.</p></section>
</main></body></html>'''
open('index.html','w').write(out); print('built',len(out))
