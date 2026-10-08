import html
from screens import SCREENS
from data import esc
def L(inner,px=72,vb="0 0 120 120"): return f'<svg viewBox="{vb}" width="{px}" height="{px}" aria-hidden="true">{inner}</svg>'
LOGOS=dict(
 swiss='<div style="font:800 40px Archivo;letter-spacing:-.05em;color:#111;line-height:1">Wasel<span style="color:#e30613">.</span></div><div style="font:600 18px \'Noto Sans Arabic\';color:#111">واصل</div>',
 destijl=L('<rect x="6" y="6" width="108" height="108" fill="#111"/><rect x="12" y="12" width="56" height="58" fill="#d4281f"/><rect x="74" y="12" width="34" height="58" fill="#fff"/><rect x="12" y="76" width="30" height="32" fill="#f2c230"/><rect x="48" y="76" width="60" height="32" fill="#1f48a8"/>'),
 isotype=L('<g transform="translate(6 18) scale(1.3)"><rect x="3" y="12" width="52" height="42" fill="#161616"/><path d="M3 12 L14 3 H44 L55 12 Z" fill="#161616"/><rect x="26" y="3" width="6" height="51" fill="#fff"/></g><path d="M82 100 V58 A15 15 0 0 1 112 58 V100" fill="none" stroke="#161616" stroke-width="6"/><circle cx="97" cy="82" r="6" fill="#e0401a"/>'),
 ma=L('<path d="M30 104 V56 A30 30 0 0 1 90 56 V104" fill="none" stroke="#1a1a1a" stroke-width="3"/>'),
 tufte=L('<g fill="#1a1a1a"><rect x="14" y="70" width="14" height="34"/><rect x="34" y="50" width="14" height="54"/><rect x="54" y="34" width="14" height="70" fill="#8f1d1d"/><rect x="74" y="50" width="14" height="54"/><rect x="94" y="70" width="14" height="34"/></g>'),
 beck=L('<path d="M8 96 H60 L84 72" fill="none" stroke="#d63a2f" stroke-width="10"/><path d="M8 66 H70 L84 72" fill="none" stroke="#e39b12" stroke-width="10" opacity="0"/><path d="M8 40 H52 L84 72" fill="none" stroke="#1f8a5b" stroke-width="10"/><path d="M80 104 V64 A18 18 0 0 1 116 64 V104 Z" fill="#10182e"/><rect x="90" y="72" width="16" height="32" fill="#f7f8f6"/>'))
D=[
 dict(k="swiss",name="Swiss Objectivity",who="Josef Müller-Brockmann, the Swiss Style",
  belief="The grid is a law of universal validity: objectivity instead of subjectivity, the will to clarify and concentrate. Typography is the image; asymmetry and a single sans carry the message. Nothing decorative survives.",
  becomes="a typeset document, not an app. There are no pills, cards or boxes. Importance is expressed by type size and weight alone: a score of 89 is set larger and bolder than a score of 9, so the page is ranked before you read a word. One red is allowed, only for risk. The selected order opens as a typographic spread beside the list.",
  inter="Read down a ranked sheet and pick a line; the spread sets one big number, the customer's words with the risky phrases underlined in red, and plain text commands (Send the question →).",
  logo="A wordmark set tight in a grotesque with one red full stop. The Arabic name sits under it at equal weight. No symbol: the type is the mark.",
  cost="Dense lists without pills lose scannability for new users, and type-size ranking breaks down for 200 orders. It also asks for strict discipline from every future screen. Codebase change: medium (replace table and cards, new type scale).",
  frame=SCREENS["swiss"]),
 dict(k="destijl",name="De Stijl: composition by proportion",who="Mondrian, van Doesburg, Rietveld (neoplasticism)",
  belief="Reduce to the elements (the straight line, the right angle, three primary colours plus black and white) and build universal harmony through asymmetric balance. The proportions of the rectangles are the content.",
  becomes="a map of money, not a list. The whole screen is a composition of rectangles; the area of each rectangle is the order's value in TND, the colour is the risk tier (red high, yellow medium, blue low, with the shape and number printed so colour is never alone). You see where the money is exposed before you read a name. The black lines are the grid.",
  inter="Look, then click a rectangle. The detail is one more white rectangle in the same composition. There is no sorting or paging; you navigate by proportion.",
  logo="A tiny Mondrian composition in which the tall white rectangle is the door.",
  cost="Small orders become unreadable slivers (a 35 TND order beside a 450 TND one), and a map cannot express order by time. It answers 'where is my money at risk' very well and 'what do I do next' poorly. Codebase change: medium (new overview, list stays as a secondary view).",
  frame=SCREENS["destijl"]),
 dict(k="isotype",name="Isotype: counted pictures",who="Otto Neurath and Gerd Arntz",
  belief="Words divide, pictures unite. A greater quantity is shown by more symbols, never by a bigger symbol, and a symbol denotes no more than is necessary to the statement. A fact should be countable at a glance, in any language.",
  becomes="a board of parcels you can count. Each order is one parcel pictogram of identical size, sorted into columns by what you should do with it. The number of parcels is the number; risk is the parcel's colour and its printed shape. Scores become counts (one parcel = 10 points: Sami's 87 is nine red parcels, and 16 after a reply is two). Results are drawn the same way: 13 parcels, each 10 refused deliveries avoided.",
  inter="Scan the columns, count, tap a parcel. Nothing on the page is a number you have to read.",
  logo="A black parcel pictogram beside a door arch with one vermilion dot.",
  cost="Approximation is the price: 87 becomes nine parcels. Precise values must still be one tap away. It needs a drawn pictogram set (parcel, door, chat) with one stroke and one weight. Codebase change: medium to large (new board and results).",
  frame=SCREENS["isotype"]),
 dict(k="ma",name="Ma and honesty: one decision",who="Kenya Hara and Muji (emptiness), with Dieter Rams (honest, unobtrusive, as little design as possible)",
  belief="Emptiness is not minimalism; it is readiness, an interval that lets something happen. Remove what tells the person what to think. Rams adds: good design is honest and as little design as possible, so say how sure you are and nothing more.",
  becomes="a stage with one order on it. The screen is a single sentence in plain words, a quiet statement of confidence ('87 out of 100 sure'), and two choices. The queue is only a row of thin ticks at the bottom. Finishing an order empties the screen, then the next appears; when nothing is waiting, the screen says so. This is a triage model, not a dashboard.",
  inter="Space to choose, arrow for next, Escape for the list. Decisions are made one at a time, which suits a phone held between other tasks.",
  logo="An open door: one thin outline arch with nothing inside it.",
  cost="A power user with 60 orders loses the overview; the list must exist behind Escape. A wrong sentence is worse than a wrong table row, so the copy must be generated and verified carefully. Codebase change: medium (new focus mode, sentence generation from existing reasons).",
  frame=SCREENS["ma"]),
 dict(k="tufte",name="Tufte: the evidence wall",who="Edward Tufte, information design",
  belief="Graphical excellence gives the viewer the greatest number of ideas in the shortest time with the least ink in the smallest space. Maximise data-ink, remove chartjunk, and use small multiples so the eye can compare. Clutter is a failure of design, not a property of information.",
  becomes="a wall of identical small multiples. Every order is the same word-sized graphic: its reasons as tiny bars on a shared axis (right raises risk, left lowers it, same scale everywhere), the score, and the one-line item. There are no pills, borders or cards; whitespace separates. A margin note explains how to read it. The unusual order is the one whose bars point away from its neighbours.",
  inter="Compare. Sort by risk, value or age with plain text controls. A hover or tap opens the order; the v1 to v2 change is a single line of text under the bars.",
  logo="Five bars whose heights form an arch: a skyline that is a door, with the tallest bar in red.",
  cost="It is the best direction for showing why a score is what it is, and the slowest for deciding what to do. It rewards expert users and can overwhelm a first-time seller. It needs the reason values to be on a comparable scale (they already are, in points). Codebase change: medium (new wall view).",
  frame=SCREENS["tufte"]),
 dict(k="beck",name="Beck: the network diagram",who="Harry Beck (London Underground), Massimo Vignelli (New York subway)",
  belief="Topology over topography: connectivity matters, geographic fidelity does not. Colour each line, use only 45 and 90 degree angles, mark interchanges. The cautionary tale: Vignelli's map was internally consistent, but riders navigate by geography and felt it lied.",
  becomes="the business drawn as one diagram. Three lines (confirm, prepay, ship) run through the same stations (scored, question asked, reply, rescored, shipped) and converge on the Door, with a dashed branch for Refused. Each order is a marker on its line at its stage; the dangerous ones are the ones still waiting before the reply. The page admits what it hides: 'Schematic: spacing is not time or distance.'",
  inter="The diagram is the navigation: click a station to see everything waiting there, click a marker for the order. There is no table.",
  logo="Two coloured lines running into a navy door arch.",
  cost="Vignelli's lesson applies: if the diagram ever hides something the seller needs (the amount, the deadline), it is a lie by omission. It works for flow, not for lookup. Codebase change: medium to large (diagram layout, station detail).",
  frame=SCREENS["beck"]),
]
CONS=[("Bauhaus (Gropius, Moholy-Nagy, Kandinsky)","Form follows function; circle, square and triangle in the three primaries. Wasel already marks tiers with a circle, a diamond and a triangle, so this is a real fit: the tiers would become the three Bauhaus forms in three colours, and the page would be built on a diagonal 'new typography' axis. Not built: it shares De Stijl's colour logic and I'd rather you choose between them."),
 ("Girih and tawhid (Islamic geometric thought)","Unity in multiplicity: simple shapes repeated by rule produce an infinite, ordered whole, and pattern is order, not decoration. As a structure this would mean one repeating module (the order) that stays the same shape from a day to a month. Not built: it needs a zoomable model I haven't designed yet, and it is the easiest direction to fake with a pretty star."),
 ("Neo-brutalism and raw HTML honesty","Truth to materials: show the system as it is. Here that would be a plain calculation sheet exposing the model's inputs and thresholds. Not built: it overlaps Tufte and the skill lists hard shadows as a costume."),
 ("Memphis and postmodernism","Play, irony, expressive colour. Wrong tone for a product that tells someone a parcel will probably be refused.")]
SCHOOLS=[
 ("Swiss Style","Objectivity; the grid is law; type is the image","Information is a ranked text, set so importance is physical size","A typeset document"),
 ("De Stijl","Universal harmony through proportion","Information is an area; value is how much room it takes","A composition / map"),
 ("Isotype","Pictures unite; more symbols, not bigger ones","Information is a count you can see without reading","A board of counted pictures"),
 ("Ma / Hara and Rams","Emptiness as readiness; honest; as little as possible","Information is one thing at a time, stated honestly","A stage with one decision"),
 ("Tufte","Most ideas, least ink; small multiples","Information is evidence to be compared","A wall of identical small graphics"),
 ("Beck and Vignelli","Topology over topography; but never lie by omission","Information is connectivity and stage","A network diagram"),
]
FONTS="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;600;700&family=Archivo:wght@400;500;600;700;800&family=Jost:wght@400;500;700&family=Lexend:wght@400;600;700&family=Zen+Kaku+Gothic+New:wght@300;400;500&family=Source+Serif+4:ital,wght@0,400;0,600;1,400&family=Public+Sans:wght@400;600;700;800&family=Noto+Sans+Arabic:wght@400;600;700&display=swap"
def card(d):
    return f'''<article class="dir" id="{d["k"]}"><header><h2>{d["name"]}</h2><p>{d["who"]}</p></header>
<div class="grid2"><div><h4>The belief</h4><p>{esc(d["belief"])}</p></div><div><h4>So the product becomes</h4><p>{esc(d["becomes"])}</p></div><div><h4>How you use it</h4><p>{esc(d["inter"])}</p></div></div>
<div class="lgrow"><div class="lg">{LOGOS[d["k"]]}</div><p><b>Logo logic.</b> {esc(d["logo"])}</p><p><b>Honest cost.</b> {esc(d["cost"])}</p></div>
<div class="frame">{d["frame"]}</div></article>'''
ph=''.join(f'<tr><th scope="row">{a}</th><td>{b}</td><td>{c}</td><td>{e}</td></tr>' for a,b,c,e in SCHOOLS)
cons=''.join(f'<div><b>{a}</b><span>{esc(b)}</span></div>' for a,b in CONS)
css=open('page.css').read()
out=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Wasel Design Philosophies</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="{FONTS}" rel="stylesheet"><style>{css}</style></head><body>
<header class="top"><h1>Wasel: six design philosophies, six different products</h1>
<p class="lead">You were right: round 2 was one dashboard repainted. A school is a belief about what information is and what a person should do with it, so each direction below changes the structure of the product itself: a document, a map, a board of counted pictures, a single decision, an evidence wall, a network diagram. Same nine orders everywhere.</p>
<nav class="jump"><a href="#studied">Philosophy to structure</a>{''.join(f'<a href="#{d["k"]}">{d["name"].split(":")[0]}</a>' for d in D)}<a href="#cons">Considered, not built</a></nav></header>
<main class="pg"><section class="blk" id="studied"><h2>What each school believes, and what that makes the product</h2>
<table class="ph"><thead><tr><th>School</th><th>Belief</th><th>Information is…</th><th>So the product is…</th></tr></thead><tbody>{ph}</tbody></table>
<p class="src">Sources: <a href="https://neugraphic.com/muller-brockmann/muller-brockmann-text2.html">Müller-Brockmann on the grid</a> · <a href="https://ebsco.com/research-starters/history/de-stijl-advocates-mondrians-neoplasticism">De Stijl and neoplasticism</a> · <a href="https://cary-exhibits.rit.edu/exhibits/show/isotype/isotype">Neurath and Isotype</a> · <a href="https://blakecrosley.com/blog/design-philosophy-kenya-hara">Kenya Hara</a> · <a href="https://makinggood.ac.nz/dieter-rams-principles-of-good-design/">Rams' ten principles</a> · <a href="https://www.cc.gatech.edu/~stasko/7450/16/Notes/tufte.pdf">Tufte's principles</a> · <a href="https://en.wikipedia.org/wiki/Tube_map">Beck's map</a> · <a href="https://secondavenuesagas.com/2012/09/14/from-vignelli-a-map-design-philosophy/">Vignelli's map</a> · <a href="https://uxplanet.org/integrating-japanese-ma-into-modern-ux-principles-9b0646d5b756">Ma in UX</a> · <a href="https://help.superhuman.com/article/480-inbox-zero-philosophy">Superhuman triage</a> · <a href="https://www.getty.edu/research/exhibitions_events/exhibitions/bauhaus/new_artist/form_color/form/">Bauhaus primary forms</a> · <a href="https://qabasat.iict.ac.ir/article_735049_en.html">Islamic geometry and tawhid</a></p></section>
{"".join(card(d) for d in D)}
<section class="blk" id="cons"><h2>Considered and not built</h2><div class="cons">{cons}</div></section></main></body></html>'''
open('index.html','w').write(out); print('ok',len(out))
