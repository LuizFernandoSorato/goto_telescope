# Conjunto de polias GT2 (passo 2 mm) + correia fechada (+ tensor opcional), como o kit 20T/40T comercial
# Rodar (PowerShell): & "C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe" build_polias.py
# Mudar um parametro (PowerShell): $env:L_CORREIA = "130"; & "C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe" build_polias.py
# Variaveis de ambiente opcionais:
#   Z1, Z2 (dentes), FURO1, FURO2 (mm), L_CORREIA (mm, multiplo de 2), LARG (largura da correia)
#   C_FIXO  : distancia entre centros fixa (mm). "0" (padrao) = calculada pela correia, sem tensor.
#   IDLER_X : posicao x do tensor (2x F623) no ramo de cima. "0" (padrao) = sem tensor. Exige C_FIXO.
#   ROT1, ROT2: giro extra das polias (graus, multiplo do passo angular) para posicionar os parafusos
#   SALVAR  : "0" nao grava arquivo nem STEP (uso como biblioteca)
import FreeCAD as App, Part, math, os

V = App.Vector
OUT = r"C:\LUIZ\PROJECTS\GOTO_TELESCOPE\FREECAD\POLIAS_GT2"

# ------------------------------------------------------------------ parametros (padrao = saida do redutor V2)
Z1 = int(os.environ.get("Z1", "20"))            # polia pequena (saida do redutor)
Z2 = int(os.environ.get("Z2", "40"))            # polia grande (EIXO)
FURO1 = float(os.environ.get("FURO1", "8"))
FURO2 = float(os.environ.get("FURO2", "8"))
L_CORREIA = float(os.environ.get("L_CORREIA", "120"))   # comprimento primitivo da correia fechada
LARG = float(os.environ.get("LARG", "6"))       # largura da correia


def _vazio(v):
    """PowerShell apaga variavel vazia: "0" tambem vale como vazio"""
    v = v.strip()
    return "" if v.lower() in ("", "0", "nao", "none") else v


C_FIXO = _vazio(os.environ.get("C_FIXO", ""))
IDLER_X = _vazio(os.environ.get("IDLER_X", ""))
ROT1 = float(os.environ.get("ROT1", "180"))
ROT2 = float(os.environ.get("ROT2", "0"))
SALVAR = os.environ.get("SALVAR", "1") == "1"
PASSO = 2.0
PLD = 0.254            # distancia da linha primitiva ao fundo da correia (GT2 2 mm)
H_DENTE_C = 0.75       # altura do dente da correia
ESP_C = 1.38           # espessura total da correia
COSTA = ESP_C - H_DENTE_C - PLD                 # linha primitiva -> costas da correia (0,376)
LARG_DENTES = LARG + 1.0                        # largura da parte dentada da polia
R_IDLER, R_IDLER_FL, H_F623 = 5.0, 5.75, 4.0    # F623ZZ: 3 x 10 x 4, flange 11,5 x 1

# polia: (flange Ø, cubo Ø, altura do cubo, parafuso de fixacao Ø, comprimento max do parafuso, flange superior?)
POLIA = {
    1: dict(z=Z1, furo=FURO1, flange=16.0, cubo=16.0, h_cubo=8.0, m=3.0, l_par=4.0, flange_sup=False),
    2: dict(z=Z2, furo=FURO2, flange=30.0, cubo=20.0, h_cubo=8.0, m=4.0, l_par=5.0, flange_sup=True),
}
T_FLANGE = 1.0

# perfil do vao GT2 2 mm (x tangencial, y radial para dentro a partir do diametro externo)
GT2 = [(0.747183, -0.5), (0.747183, 0), (0.647876, 0.037218), (0.598311, 0.130528), (0.578556, 0.238423),
       (0.547158, 0.343077), (0.504649, 0.443762), (0.451556, 0.53975), (0.358229, 0.636924), (0.2484, 0.707276),
       (0.127259, 0.750044), (0, 0.76447), (-0.127259, 0.750044), (-0.2484, 0.707276), (-0.358229, 0.636924),
       (-0.451556, 0.53975), (-0.504797, 0.443762), (-0.547291, 0.343077), (-0.578605, 0.238423),
       (-0.598311, 0.130528), (-0.648009, 0.037218), (-0.747183, 0), (-0.747183, -0.5)]
# dente da correia: o mesmo perfil um pouco menor (folga no vao), ancorado 0,3 mm dentro do corpo da correia
DENTE_C = [(x * 0.93, (y * H_DENTE_C / 0.76447 * 0.98) if y > 0 else (-0.3 if y < 0 else 0.0)) for x, y in GT2]


def r_prim(z):
    return z * PASSO / (2 * math.pi)


def r_ext(z):
    return r_prim(z) - PLD


def poly_face(pts):
    return Part.Face(Part.makePolygon([V(*p) for p in pts] + [V(*pts[0])]))


def cyl(r, h, p=(0, 0, 0), d=(0, 0, 1)):
    return Part.makeCylinder(r, h, V(*p), V(*d))


def hexagon(af, h, p, d):
    rc = af / math.sqrt(3)
    f = poly_face([(rc * math.cos(math.radians(60 * k)), rc * math.sin(math.radians(60 * k)), 0) for k in range(6)])
    s = f.extrude(V(0, 0, h))
    s.Placement = App.Placement(V(*p), App.Rotation(V(0, 0, 1), V(*d)))
    return s


# ------------------------------------------------------------------ polia
def polia(k):
    c = POLIA[k]
    z, re = c["z"], r_ext(c["z"])
    z0 = T_FLANGE                                   # inicio da parte dentada
    dentada = cyl(re, LARG_DENTES, (0, 0, z0))
    vaos = []
    for i in range(z):
        a = 2 * math.pi * i / z
        u = (math.cos(a), math.sin(a)); t = (-math.sin(a), math.cos(a))
        pts = [((re - y) * u[0] + x * t[0], (re - y) * u[1] + x * t[1], z0 - 0.1) for x, y in GT2]
        vaos.append(poly_face(pts).extrude(V(0, 0, LARG_DENTES + 0.2)))
    dentada = dentada.cut(vaos)
    partes = [cyl(c["flange"] / 2, T_FLANGE), dentada]
    zc = z0 + LARG_DENTES
    if c["flange_sup"]:
        partes.append(cyl(c["flange"] / 2, T_FLANGE, (0, 0, zc)))
        zc += T_FLANGE
    partes.append(cyl(c["cubo"] / 2, c["h_cubo"], (0, 0, zc)))
    s = partes[0].fuse(partes[1:])
    altura = zc + c["h_cubo"]
    s = s.cut(cyl(c["furo"] / 2, altura + 2, (0, 0, -1)))
    zp = zc + c["h_cubo"] / 2                        # altura dos parafusos de fixacao
    l_par = min(c["l_par"], c["cubo"] / 2 - c["furo"] / 2 - 0.5)
    parafusos = []
    for ang in (0, 90):
        d = (math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0)
        s = s.cut(cyl(c["m"] / 2, c["cubo"], (0, 0, zp), d))
        r0 = c["furo"] / 2
        p0 = (d[0] * r0, d[1] * r0, zp)
        par = cyl(c["m"] / 2, l_par, p0, d)
        pe = (d[0] * (r0 + l_par - 0.4 * c["m"]), d[1] * (r0 + l_par - 0.4 * c["m"]), zp)
        par = par.cut(hexagon(c["m"] / 2, 0.5 * c["m"], pe, d))   # sextavado interno
        parafusos.append(par)
    return s.removeSplitter(), parafusos, altura, zp


# ------------------------------------------------------------------ percurso da correia (linha primitiva)
r1, r2 = r_prim(Z1), r_prim(Z2)
N_DENTES_C = L_CORREIA / PASSO
if abs(N_DENTES_C - round(N_DENTES_C)) > 1e-9:
    raise SystemExit("L_CORREIA precisa ser multiplo de %.0f mm" % PASSO)
N_DENTES_C = int(round(N_DENTES_C))


def tangente(ca, ra, cb, rb):
    """reta tangente do circulo a ao b (raios com sinal: + anti-horario, - horario). n = normal para fora do laco"""
    d = cb - ca; D = d.Length
    dh = d * (1.0 / D); dp = V(-dh.y, dh.x, 0)
    k = (ra - rb) / D
    for s in (1, -1):
        n = dh * k + dp * (s * math.sqrt(max(0.0, 1 - k * k)))
        pa = ca + n * ra; pb = cb + n * rb
        t = pb - pa
        if t.x * n.y - t.y * n.x < 0:
            return n, pa, pb
    raise RuntimeError("tangente nao encontrada")


def percurso(circs, dr=0.0):
    """circs: [(centro, raio_com_sinal)] no sentido anti-horario do laco. Devolve segmentos e comprimento."""
    cs = [(c, r + dr) for c, r in circs]
    m = len(cs)
    tans = [tangente(cs[i][0], cs[i][1], cs[(i + 1) % m][0], cs[(i + 1) % m][1]) for i in range(m)]
    segs = []
    for i in range(m):
        c, r = cs[i]
        n_in, n_out = tans[i - 1][0], tans[i][0]
        u_in = n_in if r > 0 else n_in * -1
        u_out = n_out if r > 0 else n_out * -1
        a_in, a_out = math.atan2(u_in.y, u_in.x), math.atan2(u_out.y, u_out.x)
        if r > 0:
            sw = (a_out - a_in) % (2 * math.pi)
        else:
            sw = -((a_in - a_out) % (2 * math.pi))
        segs.append(("arco", c, abs(r), a_in, sw))
        n, pa, pb = tans[i]
        segs.append(("reta", pa, pb, n))
    comp = sum((s[2] * abs(s[4])) if s[0] == "arco" else (s[2] - s[1]).Length for s in segs)
    return segs, comp


def comprimento_aberto(C):
    return percurso([(V(0, 0, 0), r1), (V(C, 0, 0), r2)])[1]


# distancia entre centros
if C_FIXO:
    C = float(C_FIXO)
else:
    lo, hi = (r2 - r1) + 1e-6, L_CORREIA
    if comprimento_aberto(lo) > L_CORREIA:
        raise SystemExit("Correia curta demais para estas polias")
    for _ in range(200):
        mid = (lo + hi) / 2
        if comprimento_aberto(mid) < L_CORREIA:
            lo = mid
        else:
            hi = mid
    C = (lo + hi) / 2
O1, O2 = V(0, 0, 0), V(C, 0, 0)
L_ABERTO = comprimento_aberto(C)

# tensor: posicao y em que a correia fica com o comprimento exato (tracao zero)
IDLER = None
if IDLER_X:
    if not C_FIXO:
        raise SystemExit("IDLER_X exige C_FIXO")
    xi = float(IDLER_X)
    if L_ABERTO >= L_CORREIA:
        raise SystemExit("Com C=%.3f a correia de %g ja fica esticada sem tensor (%.3f mm)" % (C, L_CORREIA, L_ABERTO))
    ri = -(R_IDLER + COSTA)                     # linha primitiva em volta do tensor (sentido horario)
    # ramo de cima sem tensor: normal e ponto
    n_up, pa_up, _ = tangente(O2, r2, O1, r1)
    y_toque = pa_up.y + (abs(ri) - (xi - pa_up.x) * n_up.x) / n_up.y

    def L_idler(y):
        return percurso([(O1, r1), (O2, r2), (V(xi, y, 0), ri)])[1]
    lo, hi = y_toque - 10.0, y_toque - 1e-6     # L diminui quando o tensor sobe (y maior)
    for _ in range(200):
        mid = (lo + hi) / 2
        if L_idler(mid) > L_CORREIA:
            lo = mid
        else:
            hi = mid
    yi = (lo + hi) / 2
    IDLER = dict(x=xi, y=yi, y_toque=y_toque, r=ri)
    CIRCS = [(O1, r1), (O2, r2), (V(xi, yi, 0), ri)]
else:
    if C_FIXO:
        print("Sem tensor: com C=%.3f o percurso mede %.3f mm (correia %g): %s de %.3f mm" % (
            C, L_ABERTO, L_CORREIA, "esticada" if L_ABERTO > L_CORREIA else "folga", abs(L_ABERTO - L_CORREIA)))
    CIRCS = [(O1, r1), (O2, r2)]

SEGS, L_PRIM = percurso(CIRCS)


def ponto(s):
    """ponto na linha primitiva e normal para fora do laco, a distancia s ao longo do percurso"""
    s %= L_PRIM
    for sg in SEGS:
        if sg[0] == "arco":
            _, c, r, a0, sw = sg
            l = r * abs(sw)
            if s <= l:
                a = a0 + math.copysign(s / r, sw)
                u = V(math.cos(a), math.sin(a), 0)
                return c + u * r, (u if sw > 0 else u * -1)
        else:
            _, pa, pb, n = sg
            l = (pb - pa).Length
            if s <= l:
                return pa + (pb - pa) * (s / l), n
        s -= l
    return ponto(0)


def contorno(dr):
    segs, _ = percurso(CIRCS, dr)
    e = []
    for sg in segs:
        if sg[0] == "arco":
            _, c, r, a0, sw = sg
            a1, a2 = (a0, a0 + sw) if sw > 0 else (a0 + sw, a0)
            e.append(Part.ArcOfCircle(Part.Circle(c, V(0, 0, 1), r), a1, a2).toShape())
        else:
            if (sg[2] - sg[1]).Length > 1e-6:
                e.append(Part.LineSegment(sg[1], sg[2]).toShape())
    return Part.Face(Part.Wire(Part.__sortEdges__(e)))


def correia():
    a_in = SEGS[0][3]                               # inicio do arco da polia pequena
    s0 = r1 * ((math.pi - a_in) % (2 * math.pi))    # dente da correia no ponto mais a esquerda da polia pequena
    dentes = []
    for i in range(N_DENTES_C):
        p, n = ponto(s0 + PASSO * i)
        t = V(-n.y, n.x, 0)
        q = p - n * PLD
        dentes.append(poly_face([tuple(q + t * x - n * y) for x, y in DENTE_C]).extrude(V(0, 0, LARG)))
    s = contorno(COSTA).cut(contorno(-PLD)).extrude(V(0, 0, LARG)).fuse(dentes).removeSplitter()
    s = Part.Solid(Part.Shell(s.Faces)) if len(s.Solids) == 1 else s
    s.translate(V(0, 0, T_FLANGE + (LARG_DENTES - LARG) / 2))
    return s, s0


def tensor():
    """2x F623 costas com costas (flanges para fora), centrados na correia"""
    z0 = T_FLANGE + (LARG_DENTES - LARG) / 2 - T_FLANGE   # flange de baixo termina na borda da correia
    p = V(IDLER["x"], IDLER["y"], 0)
    um = cyl(R_IDLER, H_F623).fuse(cyl(R_IDLER_FL, 1.0)).cut(cyl(1.5, H_F623))
    a = um.copy(); a.translate(p + V(0, 0, z0))
    b = um.mirror(V(0, 0, H_F623 / 2), V(0, 0, 1)); b.translate(p + V(0, 0, z0 + H_F623))
    return a, b, z0


# ------------------------------------------------------------------ montagem
doc = App.newDocument("POLIAS_GT2")
cor, s0 = correia()

# fase das polias: um vao em cada dente da correia
fase = {1: 180.0}                                   # dente s0 esta no angulo 180 graus da polia pequena
s_b = SEGS[0][2] * abs(SEGS[0][4]) + (SEGS[1][2] - SEGS[1][1]).Length   # inicio do arco da polia grande
l_b = SEGS[2][2] * abs(SEGS[2][4])
for i in range(N_DENTES_C):
    s = (s0 + PASSO * i) % L_PRIM - s_b
    if 0 <= s < l_b:
        fase[2] = math.degrees(SEGS[2][3] + s / r2)
        break
ROTS = {1: ROT1, 2: ROT2}

objs = {}
locais = {}
ANG_PARAFUSO = {}
for k, centro in ((1, O1), (2, O2)):
    c = POLIA[k]
    s, pars, alt, zp = polia(k)
    nome = "POLIA_GT2_%dT_furo%g" % (c["z"], c["furo"])
    locais[nome] = s.copy()
    ang = fase[k] % (360.0 / c["z"]) + ROTS[k]
    ANG_PARAFUSO[k] = ang % 360.0
    plc = App.Placement(centro, App.Rotation(V(0, 0, 1), ang))
    s.Placement = plc
    o = doc.addObject("Part::Feature", nome); o.Shape = s; objs[nome] = o
    for j, p in enumerate(pars):
        p.Placement = plc.multiply(p.Placement)
        o = doc.addObject("Part::Feature", "PARAFUSO_M%g_%dT_%d" % (c["m"], c["z"], j + 1)); o.Shape = p; objs[o.Name] = o
nome_c = "CORREIA_GT2_%gx%g" % (L_CORREIA, LARG)
o = doc.addObject("Part::Feature", nome_c); o.Shape = cor; objs[nome_c] = o
if IDLER:
    a, b, z_idler = tensor()
    for nm, sh in (("TENSOR_F623_1", a), ("TENSOR_F623_2", b)):
        o = doc.addObject("Part::Feature", nm); o.Shape = sh; objs[nm] = o
doc.recompute()

# ------------------------------------------------------------------ relatorio
print("GT2 %dT (furo %g) x %dT (furo %g), reducao %.3f:1" % (Z1, FURO1, Z2, FURO2, Z2 / Z1))
print("Diametro primitivo: %.3f / %.3f mm; externo: %.3f / %.3f mm" % (2 * r1, 2 * r2, 2 * r_ext(Z1), 2 * r_ext(Z2)))
print("Correia %g mm (%d dentes) x %g mm; distancia entre centros %.3f mm%s" % (L_CORREIA, N_DENTES_C, LARG, C, " (fixa)" if C_FIXO else ""))
if IDLER:
    print("Sem tensor a correia pediria %.3f mm -> folga de %.3f mm" % (L_ABERTO, L_CORREIA - L_ABERTO))
    print("Tensor (2x F623) em x=%.2f: encosta na correia reta em y=%.2f; tracao zero em y=%.2f (desloc. %.2f mm)" % (
        IDLER["x"], IDLER["y_toque"], IDLER["y"], IDLER["y_toque"] - IDLER["y"]))
arco1 = math.degrees(abs(SEGS[0][4]))
print("Abracamento na polia pequena: %.1f graus (%.1f dentes engrenados)" % (arco1, arco1 / 360 * Z1))
print("Parafuso 1 das polias (angulo em torno do proprio eixo): 20T %.2f graus, 40T %.2f graus" % (ANG_PARAFUSO[1], ANG_PARAFUSO[2]))


def inter(a, b):
    if not a.BoundBox.intersect(b.BoundBox):
        return 0.0
    return a.common(b).Volume


print("\n== interferencias")
nomes = list(objs); achou = 0
for i in range(len(nomes)):
    for j in range(i + 1, len(nomes)):
        v = inter(objs[nomes[i]].Shape, objs[nomes[j]].Shape)
        if v > 0.01:
            achou += 1
            print("   %-28s x %-28s %.3f mm3" % (nomes[i], nomes[j], v))
print("   total:", achou)
for n, o in objs.items():
    print("   %-28s valido=%s solidos=%d" % (n, o.Shape.isValid(), len(o.Shape.Solids)))

if SALVAR:
    os.makedirs(OUT, exist_ok=True)
    doc.saveAs(os.path.join(OUT, "POLIAS_GT2.FCStd"))
    sd = os.path.join(OUT, "STEP"); os.makedirs(sd, exist_ok=True)
    for n, s in locais.items():
        s.exportStep(os.path.join(sd, n + ".step"))
    objs[nome_c].Shape.exportStep(os.path.join(sd, nome_c + ".step"))
    Part.makeCompound([o.Shape for o in objs.values()]).exportStep(os.path.join(sd, "CONJUNTO_POLIAS_GT2.step"))
    print("salvo:", OUT)
