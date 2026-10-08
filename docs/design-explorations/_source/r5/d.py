import html
def esc(s): return html.escape(str(s))
def bdi(s): return f'<bdi dir="auto">{esc(s)}</bdi>'
# ref,name,item,tnd,tier,score,next,zone,age_min,state
O=[("#2609","Mehdi","mixeur",129,"High",89,"Confirm address","Rural",195,"Question sent"),
   ("#2601","Sami","casque bluetooth",220,"High",87,"Confirm address","Rural",190,"Question sent"),
   ("#2604","Hedi","tablette",450,"High",85,"Ask prepayment","Rural",130,"Question sent"),
   ("#2605","Nour","aspirateur",349,"High",71,"Ask prepayment","Urban",70,"Question sent"),
   ("#2603","سارة","crème visage",35,"Medium",42,"Quick check","Urban",40,"Scored"),
   ("#2608","كريم","montre connectée",149,"Low",14,"Ship","Urban",25,"Ready"),
   ("#2606","Yassine","jean slim",59,"Low",9,"Ship","Urban",20,"Ready"),
   ("#2602","Leila","montre connectée",149,"Low",4,"Ship","Urban",15,"Ready"),
   ("#2607","Rim","sac en cuir",99,"Low",4,"Ship","Urban",10,"Ready")]
REAS=[("3 warning signs: “9rib el jemaa”",17),("rural delivery zone",13),("vague address “Douar Ouled Ali”",12),("new customer",7)]
SH={"High":"●","Medium":"◆","Low":"▲"}
def fmt_age(m): return f"{m//60}h {m%60:02d}" if m>=60 else f"{m} min"
