import html
def esc(s): return html.escape(s)
# ref, name, item, tnd, tier, score, next, stage(0-5), line
O=[("#2609","Mehdi","mixeur",129,"High",89,"Confirm the address",2),
   ("#2601","Sami","casque bluetooth",220,"High",87,"Confirm the address",2),
   ("#2604","Hedi","tablette",450,"High",85,"Ask for prepayment",2),
   ("#2605","Nour","aspirateur",349,"High",71,"Ask for prepayment",2),
   ("#2603","سارة","crème visage",35,"Medium",42,"Quick check",2),
   ("#2608","كريم","montre connectée",149,"Low",14,"Ship",4),
   ("#2606","Yassine","jean slim",59,"Low",9,"Ship",4),
   ("#2602","Leila","montre connectée",149,"Low",4,"Ship",4),
   ("#2607","Rim","sac en cuir",99,"Low",4,"Ship",4)]
SHAPE={"High":"●","Medium":"◆","Low":"▲"}
REASONS=[("3 warning signs: “9rib el jemaa”",17),("rural delivery zone",13),("vague address “Douar Ouled Ali”",12),("new customer",7)]
# squarified treemap
def squarify(vals,x,y,w,h):
    tot=sum(vals); items=[(v*w*h/tot,i) for i,v in enumerate(vals)]
    out={}
    def worst(row,side):
        s=sum(a for a,_ in row); mx=max(a for a,_ in row); mn=min(a for a,_ in row)
        return max(side*side*mx/(s*s), s*s/(side*side*mn))
    def layout(row,x,y,w,h):
        s=sum(a for a,_ in row)
        if w>=h:
            rw=s/h; yy=y
            for a,i in row: rh=a/rw; out[i]=(x,yy,rw,rh); yy+=rh
            return x+rw,y,w-rw,h
        else:
            rh=s/w; xx=x
            for a,i in row: rw=a/rh; out[i]=(xx,y,rw,rh); xx+=rw
            return x,y+rh,w,h-rh
    rest=sorted(items,reverse=True); row=[]
    while rest:
        side=min(w,h); c=rest[0]
        if not row or worst(row+[c],side)<=worst(row,side): row.append(c); rest.pop(0)
        else: x,y,w,h=layout(row,x,y,w,h); row=[]
    if row: layout(row,x,y,w,h)
    return out
