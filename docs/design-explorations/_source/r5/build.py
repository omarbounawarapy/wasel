import p_a,p_b,p_c
from d import esc
F=[
 (1,"Bloomberg Terminal","Financial trading terminal","https://en.wikipedia.org/wiki/Bloomberg_Terminal","md",
  "Density is not about cramming more; it is maximising value in time and space. Pure black with amber and cyan, a keyboard whose keys carry names and colours (Esc is red Cancel, Enter is green GO), and a religious consistency that users have grown attached to.",
  "A multi-panel desk. A command line takes an order code and GO; each panel carries a three-letter mnemonic (ORD, RSN, MSG, MON); the bottom row is a function-key bar. Everything is one keystroke away and nothing is hidden behind a menu.",
  "Best for an owner or assistant at a desk all day. Poor on a phone. Copy the density, the consistency and the keyboard; do not copy the amber-on-black, which is the terminal's costume, not its function."),
 (2,"Observability (Grafana, Datadog)","Site-reliability dashboards","https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/best-practices/","hi",
  "Four golden signals: latency, traffic, errors, saturation. One row per service following the data flow, template variables instead of a dashboard per node, hierarchy with drill-downs, a Z-pattern reading order and thresholds that colour a number.",
  "The business as a service. Orders per day is traffic, refused-at-door is errors, time to confirm is latency, backlog is saturation, each with a threshold. Variables for zone and tier, a time-range picker, time-series panels, and a table of the riskiest orders at the bottom.",
  "The right overview for an owner who wants to know how the day is going. Weak at handling a single order. It rewards a time series, so it needs history that the prototype only has as synthetic data."),
 (3,"Order blotter (trading workstations)","Order-management systems","https://www.interactivebrokers.co.uk/en/software/tws.bak/usersguidebook/realtimeactivitymonitoring/order_status_colors.htm","hi",
  "Colours encode the order lifecycle, not the market: light grey while creating, light blue transmitted, green working, magenta cancel pending, red cancelled. A blotter lists every order and a ticket acts on the selected one.",
  "Every order is a line with a lifecycle colour (scored, question sent, awaiting reply, ready, cancel pending). Risk is a separate column. The ticket docks at the bottom with the three actions. Status lives in the row's colour, which frees the risk column for the score.",
  "Excellent for a person who must always know where each order is in its life. The colour key must be learned, and two colour systems (status and risk) can collide."),
 (4,"Fraud review queue (Stripe Radar)","Risk and payments review","https://docs.stripe.com/radar/reviews","hi",
  "A review queue shows the risk level, customer, amount and date so a reviewer can assess quickly; J and K move between payments; the detail page carries the metadata for the decision; closing the review records the outcome.",
  "The nearest cousin to Wasel. A queue of open reviews on the left, the selected case on the right: the customer's own words, an address check, history, and the reasons as bars. A decision bar at the bottom with J/K to move on.",
  "This is the structure to beat: it matches the job exactly. Risk is that it looks like every payments dashboard, so the distinctiveness has to come from the evidence cards and the customer's quoted words."),
 (5,"Logistics control tower","Supply-chain visibility (project44, FourKites)","https://www.fretron.com/blog/logistics-control-tower-dashboard-complete-end-to-end-visibility/","md",
  "A centralised command centre that flags deviations from plan and routes them to people or playbooks. Map-based UX with colour-coded at-risk deliveries and predictive ETAs; the winner becomes embedded in daily exception management.",
  "An exceptions queue on the left, a map of the orders in the middle coloured by risk, and the selected order on the right, with a KPI strip on top. The unit of work is the exception, not the order.",
  "Worth it only once orders carry real locations or couriers. Today Wasel knows rural versus urban, so the map is schematic and the page must say so."),
 (6,"Incident console (PagerDuty)","Incident response","https://support.pagerduty.com/main/docs/operations-console","hi",
  "Incidents move Triggered, Acknowledged, Resolved. Severity is P1 to P5 with the lower number more urgent. Escalation policies tell the next person automatically; custom views let a team triage and act.",
  "Orders as incidents: grouped by state, each with a P1 to P3 badge, an acknowledge, escalate, snooze and resolve bar, a timeline, a runbook (ask, wait an hour, call) and an on-call line saying who owns it until 18:00.",
  "Very strong when an assistant shares the work, because ownership and escalation are first-class. 'Incident' is an odd word for a sales order; keep the state model and drop the vocabulary."),
 (7,"Dispatch console (911 CAD)","Computer-aided dispatch","https://geonet.esri.com/ccqpr47374/attachments/ccqpr47374/public-safety-docs/9/1/J9699%20Geospatial%20Computer%20Aided%20Dispatch.pdf","md",
  "CAD identifies the most appropriate and available resource for each call and manages resource status. Ergonomics aim to keep focus on the caller, not on the search for a control; dispatchers work across several screens and a command line.",
  "An incident list, a unit board (owner, assistant, couriers, the LLM) with live status, an event log and a command line (ASSIGN 2601 ASSISTANT). The question it answers is who should take this, and is that person free.",
  "Fits if several people or couriers share the queue. For a solo seller the unit board is empty decoration."),
 (8,"Clinical central station","Patient monitoring (IEC 60601-1-8)","https://international.johner-institute.com/articles/product-development/and-more/iec-60601-1-8/","md",
  "Alarms are often the last chance to prevent harm. High priority is red, medium is yellow, low is cyan, with consistent signals and control states. The standard exists to reduce alarm risk and, implicitly, alarm fatigue.",
  "A row per order, each with a trace of its score over time, a large score, and an alarm marker by priority (!!! red, !! yellow, ! cyan). A red banner names the one that needs you, with Silence 2 min. Adopting the standard's red, yellow and cyan for tiers is the useful part.",
  "Powerful for tiers and silencing. The ECG traces are decoration unless they show a real score history, which only rescored orders have. Easily a costume."),
 (9,"High-performance HMI (ISA-101)","Industrial process control","https://processonline.com.au/content/process-control-systems/sponsored/best-design-practices-creating-a-high-performance-hmi-1374659233","hi",
  "The screen is deliberately grey; colour, motion and blinking are reserved for abnormal situations. A grey screen means a healthy process. Analog indicators with alarm zones replace bare numbers so a glance gives the state.",
  "Wasel's AI pipeline drawn as equipment: ingest, extract, fallback, score, draft and checks, each with analog bars showing range and alarm zones. Everything is grey except one amber item (fallback active since 13:40).",
  "The best fit for the AI-health pages (live monitor, quality, call log): it makes abnormal visible by making normal quiet. It is a poor fit for the order list."),
 (10,"Air-traffic control display","Radar scope and flight strips","https://patents.google.com/patent/US5732384","lo",
  "An icon, a tag and a leader line connect each object to its data block. Performance trends down when data blocks exceed three lines. Dense overlays clutter as traffic grows. Flight strips are organised by posting fix.",
  "A scope where each order is a track with a three-line data block (name and score, value, action) on a leader line, plus a strip bay at the side. Axes are waiting time and order value. The alert strip says four high tracks have waited over an hour.",
  "Good for spotting stalls and for discipline about data-block length. The axes are my invention, labelled schematic, and the scope gets cluttered quickly. Low fit for routine work."),
 (11,"Support inbox with SLAs (Zendesk, Front)","Customer-support operations","https://support.zendesk.com/hc/en-us/articles/4408883355546-Introduction-to-the-Support-agent-interface-standard-agent-interface","hi",
  "The left list of views (unsolved, unassigned, at-risk SLA) is the queue agents pull from, triage in and clear down to zero. Every ticket has a timer; agents are alerted when one risks breaching. Macros and internal notes speed the reply.",
  "Conversation-first. Views for needs reply, SLA at risk, waiting on customer and ready; a list with a countdown per customer; the thread with Wasel's draft, an internal note and macro chips (Ask for address, Ask prepayment, Call instead). The unit of work is the conversation, which is where the seller already lives (WhatsApp).",
  "High fit: it matches how sellers think. The SLA clock is a new idea for them and needs a sensible default."),
 (12,"Merchant admin (Shopify Polaris)","E-commerce back office","https://www.shopify.com/partners/blog/polaris-update","hi",
  "Merchant-focused: design for efficiency and clarity because merchants run their business in it. An index table of orders gives an at-a-glance view with actions; badges carry tones like critical, warning, success.",
  "The back office a Tunisian online seller may already know: tabs (All, Needs review, Awaiting reply, Ready), a filter bar with pills, bulk select, tone badges. The least surprising choice.",
  "Highest familiarity and lowest distinctiveness. It is the category standard played straight, the quiet exit the skill keeps open."),
 (13,"SAP Fiori","Enterprise worklist and object page","https://www.sap.com/design-system/fiori-design-web/v1-71/page-types/floorplans/work-list/usage","md",
  "A worklist shows items a user must process and lets them act: review the details, then complete or delegate. An object page shows and categorises everything about one object, with a header, anchor tabs and a footer action bar.",
  "A worklist with KPI tags beside an object page with header facets (score, zone, waiting, customer), tabs (General, Evidence, Messages, History) and a footer action bar. It is the structure of formal enterprise tools.",
  "Reassuring for someone who wants a proper business tool; heavy for a solo seller and the most corporate of the set."),
 (14,"IBM Carbon data table","Enterprise design system","https://carbondesignsystem.com/components/data-table/usage/","hi",
  "Data tables support sorting, expandable rows and single or batch actions. When rows are selected, a batch-action toolbar appears. The look is productive density: gray layers, 40px rows, a blue primary.",
  "A dense table with a batch bar that appears on selection (2 items selected: ask for address, ask for prepayment, cancel) and a density control. The main idea is doing one thing to many orders at once.",
  "The best fit for bulk handling: ask ten customers for their address in one move. It is a table first, so it gives up the order-as-story approach."),
 (15,"NOC and SOC wall display","Operations-centre wallboard","https://www.barco.com/ko/inspiration/news-insights/2022-06-23-noc-soc-video-wall-how-to-choose","lo",
  "A wallboard is for passive viewing and instant situational awareness, not exploration. Large type, colour-coded severity, zero interaction, minimal information, readable at distance.",
  "For a screen on the shop wall: six huge status cells and an escalation ticker. No buttons, no scroll. It is the hero-number layout, correct here because nobody is clicking.",
  "Only if a team has a screen to put it on. It is a complement to a working dashboard, never the product."),
 (16,"Linear","Issue tracking","https://blakecrosley.com/guides/design/linear","hi",
  "Software should be opinionated and fast. Keyboard-first: C creates, G then I goes to the inbox, the command palette on Cmd+K is the real product. Dense but clean through consistent spacing, muted colour and progressive disclosure; transitions under 100 ms.",
  "An inbox grouped by state with tiny priority marks, a side peek for the selected order, and a command palette (Ask for the address, Approve, Cancel) opened by one key. The interface is mostly keyboard and almost no chrome.",
  "A joy for a power user and mystifying to a first-time seller. It demands local-first speed that a server-polled prototype cannot give yet."),
]
MK={i:getattr(p_a,'p%d'%i,None) or getattr(p_b,'p%d'%i,None) or getattr(p_c,'p%d'%i) for i in range(1,17)}
FIT={"hi":("High fit","hi"),"md":("Medium fit","md"),"lo":("Low fit","lo")}
FONTS="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;600;700&family=Roboto+Mono:wght@400;700&family=Roboto:wght@400;500&family=Public+Sans:wght@400;600;700&family=Source+Sans+3:wght@400;600&family=IBM+Plex+Sans:wght@400;600&family=Geist:wght@400;500;600&display=swap"
def card(f):
    n,name,cat,url,fit,logic,becomes,verdict=f
    t,c=FIT[fit]
    return f'''<article class="cx" id="s{n}"><input type="checkbox" id="z{n}" class="zt"><header><span class="no">{n:02d}</span><div><h2>{esc(name)}<span class="fit {c}">{t}</span></h2><p>{esc(cat)} · <a href="{url}">source</a></p></div><label for="z{n}" class="zb">Enlarge</label></header>
<div class="tx"><div><h4>The design logic of this family</h4><p>{esc(logic)}</p></div><div><h4>So Wasel becomes</h4><p>{esc(becomes)}</p></div></div>
<div class="frame"><div class="zoomer">{MK[n]()}</div></div><div class="ft1"><p><b>Verdict:</b> {esc(verdict)}</p></div></article>'''
jump=''.join(f'<a href="#s{f[0]}">{f[0]} {esc(f[1].split("(")[0].strip())}</a>' for f in F)
css=open('page.css').read()+open('mocks.css').read()
rec='''<section class="rec"><h2>How I would read this</h2><p>These sixteen are real operations-dashboard families, not metaphors. They are not alternatives so much as parts of one serious product, because each solves a different job:</p><ul>
<li><b>The daily working surface:</b> the review queue (04) or the support inbox with timers (11). Both put the customer's own words next to the decision. 06 adds ownership and escalation if an assistant shares the work.</li>
<li><b>The owner's overview:</b> observability (02), with 03's lifecycle colours if status matters more than risk.</li>
<li><b>Bulk work:</b> the Carbon batch bar (14), so ten orders can be asked at once.</li>
<li><b>The AI-health pages:</b> the grey high-performance HMI (09), because it makes abnormal visible by keeping normal quiet.</li>
<li><b>The category-standard exit:</b> Polaris (12), which sellers already know and which is the least distinctive.</li>
<li><b>Power-user layer:</b> Linear's keyboard and command palette (16) and Bloomberg's density and consistency (01).</li></ul></section>'''
out=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Wasel: 16 ops dashboard families</title><link rel="preconnect" href="https://fonts.googleapis.com"><link href="{FONTS}" rel="stylesheet"><style>{css}</style></head><body>
<header class="top"><h1>Wasel: 16 operations-dashboard families</h1><p class="lead">Serious, professional, real-ops. Each family was researched on its own (source on each card), then built to its actual structure: a blotter and a ticket, golden-signal panels, a review queue, an exception map, an incident console, a dispatch board, a clinical alarm station, a grey process screen, a radar scope, an SLA inbox, a merchant admin, a worklist and object page, a batch-action table, a wallboard and a keyboard-first inbox. The same nine orders appear everywhere, labelled synthetic. Click Enlarge for full size.</p>
<p class="lead small">Fit is my judgement for a Tunisian seller handling cash-on-delivery orders on a phone and a laptop. Several families copy their original's fonts, which are the original's own; the mock-ups are static and untested.</p><nav class="jump">{jump}</nav></header>
<main class="pg">{rec}<div class="grid">{"".join(card(f) for f in F)}</div></main></body></html>'''
open('index.html','w').write(out); print('ok',len(out))
