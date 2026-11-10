# Saida por polias GT2 20T/40T do redutor V2: correcoes sobre o que foi desenhado a mao em REDUCAO_V2 / MONTAGEM_V2
#   - 608 em todos os mancais: alojamento Ø22,2 x 7, ressalto Ø15 (apoia so na pista externa)
#   - SAIDA: eixo Ø8 ate a PLACA_SUPERIOR (2o mancal), ressalto no disco para a pista interna, rebaixo no cubo da 20T
#   - EIXO em 608 na PLACA_SUPERIOR e no MANCAL (40T entre os dois); a TAMPA nao tem mais a aba do EIXO
#     travado por 2 aneis DIN 471 (montagem cruzada, folga axial FOLGA_AX no MANCAL)
#   - MANCAL aparafusado na traseira do motor (4 furos +-15,5), sem pilares
#   - correia fechada 120 mm, sem tensor: entre centros fixo C (um pouco acima do nominal = leve pre-tensao)
#   - PLACA_SUPERIOR presa por 4 espacadores nos parafusos do motor. Se ela ja existe (editada a mao), e mantida.
#   - espacador 2,6 para travar a SAIDA no 608 da TAMPA
# Teste numa copia: $env:REDUCAO_V2_DIR = "pasta com copias de REDUCAO_V2.FCStd e MONTAGEM_V2.FCStd"
# Rodar com: & "C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe" saida_polias.py   (pode rodar de novo: refaz o que criou)
import FreeCAD as App, Part, Sketcher, math, os, sys

V = App.Vector; R = App.Rotation; P = App.Placement; Q = App.Units.Quantity
D_SCRIPTS = r"C:\LUIZ\PROJECTS\GOTO_TELESCOPE\FREECAD\REDUCAO_V2\scripts"
D = os.environ.get("REDUCAO_V2_DIR", os.path.dirname(D_SCRIPTS))
sys.path.insert(0, D_SCRIPTS)
import visivel                                  # freecadcmd nao grava o GuiDocument.xml: guarda e devolve
GUI_PD = visivel.ler_gui(os.path.join(D, "REDUCAO_V2.FCStd"))
GUI_DOC = visivel.ler_gui(os.path.join(D, "MONTAGEM_V2.FCStd"))
POL = r"C:\LUIZ\PROJECTS\GOTO_TELESCOPE\FREECAD\POLIAS_GT2\scripts\build_polias.py"

# ------------------------------------------------------------------ parametros (quadro do redutor: z para a saida)
L_CORREIA = 120          # GT2 fechada 120 x 6 (60 dentes)
C = 29.35                # entre centros SAIDA <-> EIXO: nominal 29,306 + 0,044 (correia alonga ~0,09 mm, ~18 N)
DROL, HROL, DRESS = 22.2, 7.0, 15.0     # 608: alojamento, largura, furo do ressalto
Z_SAIDA = 59.0           # posicao da SAIDA na montagem
Z_T0, T_TAMPA = 59.4, 9.0
Z_T1 = Z_T0 + T_TAMPA    # topo da TAMPA (68,4)
Z_POL = 69.0             # base das polias (flange de baixo), 0,6 mm acima da TAMPA
Z_PL0, T_PL = 88.5, 9.0  # PLACA_SUPERIOR (2 mm mais alta: espaco para anel + espacador do EIXO)
Z_MANCAL_TOPO = -51.0
EIXO_Z0, EIXO_Z1 = -70.0, Z_PL0 + HROL  # EIXO ate o topo do 608 da PLACA
Z_HUB40 = Z_POL + 17.0                  # topo do cubo da 40T (86)
R_BRACO = 16.0                          # braco da PLACA ate o EIXO
ESP_T = 1.0                             # espacador entre anel e pista interna (o anel nao toca a blindagem)
S_ANEL, M_RAN, D_RAN = 0.8, 0.9, 7.6    # DIN 471 - 8: espessura do anel, largura e diametro do canal
FOLGA_AX = 0.3                          # folga axial do EIXO (dilatacao do PETG x aco, tolerancia de impressao)
Z_ANEL_SUP0 = Z_PL0 - ESP_T - S_ANEL                       # anel de cima (empurra o 608 da PLACA para cima)
Z_ANEL_INF1 = Z_MANCAL_TOPO + ESP_T + FOLGA_AX + S_ANEL    # anel de baixo (empurra o 608 do MANCAL para baixo)
assert Z_ANEL_SUP0 > Z_HUB40 + 0.3
STANDOFFS = [(-15.5, 15.5), (-15.5, -15.5), (15.5, -15.5), (15.5, 15.5)]
ESP_D, ESP_d = 11.5, 8.2                # espacadores que apoiam so na pista interna do 608
OCT = [(-16.757, -21.0), (16.757, -21.0), (21.0, -16.757), (21.0, 16.757), (16.757, 21.0), (-16.757, 21.0), (-21.0, 16.757), (-21.0, -16.757)]

# ------------------------------------------------------------------ 1) polias e correia (sem tensor)
os.environ.update(C_FIXO=str(C), IDLER_X="0", FURO1="8", FURO2="8", L_CORREIA=str(L_CORREIA), ROT1="180", ROT2="0", SALVAR="1")
ns = {"__name__": "build_polias"}
exec(compile(open(POL, encoding="utf-8").read(), POL, "exec"), ns)
pol = ns["doc"]
ANG2 = ns["ANG_PARAFUSO"][2]


# ------------------------------------------------------------------ utilitarios PartDesign
def origem(body, role):
    for f in body.Origin.OriginFeatures:
        if f.Role == role:
            return f


def esboco(body, nome, z=0.0):
    sk = body.newObject("Sketcher::SketchObject", nome)
    sk.AttachmentSupport = [(origem(body, "XY_Plane"), "")]
    sk.MapMode = "FlatFace"
    sk.AttachmentOffset = P(V(0, 0, z), R())
    return sk


def circulo(sk, x, y, d, xexpr=None, yexpr=None, dexpr=None):
    g = sk.addGeometry(Part.Circle(V(x, y, 0), V(0, 0, 1), d / 2.0), False)
    c = sk.addConstraint(Sketcher.Constraint("Diameter", g, d))
    if dexpr:
        sk.setExpression("Constraints[%d]" % c, dexpr)
    if abs(x) < 1e-9 and abs(y) < 1e-9:
        sk.addConstraint(Sketcher.Constraint("Coincident", g, 3, -1, 1))
    else:
        c = sk.addConstraint(Sketcher.Constraint("DistanceX", -1, 1, g, 3, x))
        if xexpr:
            sk.setExpression("Constraints[%d]" % c, xexpr)
        c = sk.addConstraint(Sketcher.Constraint("DistanceY", -1, 1, g, 3, y))
        if yexpr:
            sk.setExpression("Constraints[%d]" % c, yexpr)
    return g


def poligono(sk, pts):
    n = len(pts)
    g0 = sk.GeometryCount
    for i in range(n):
        sk.addGeometry(Part.LineSegment(V(*pts[i], 0), V(*pts[(i + 1) % n], 0)), False)
    for i in range(n):
        sk.addConstraint(Sketcher.Constraint("Coincident", g0 + i, 2, g0 + (i + 1) % n, 1))


def rasgo(sk, x, y0, y1, w):
    """rasgo oblongo ao longo de y"""
    r = w / 2.0
    g0 = sk.GeometryCount
    sk.addGeometry(Part.LineSegment(V(x - r, y0, 0), V(x - r, y1, 0)), False)
    sk.addGeometry(Part.ArcOfCircle(Part.Circle(V(x, y1, 0), V(0, 0, 1), r), 0, math.pi), False)
    sk.addGeometry(Part.LineSegment(V(x + r, y1, 0), V(x + r, y0, 0)), False)
    sk.addGeometry(Part.ArcOfCircle(Part.Circle(V(x, y0, 0), V(0, 0, 1), r), math.pi, 2 * math.pi), False)
    for a, pa, b, pb in ((0, 2, 1, 2), (1, 1, 2, 1), (2, 2, 3, 2), (3, 1, 0, 1)):
        sk.addConstraint(Sketcher.Constraint("Coincident", g0 + a, pa, g0 + b, pb))


def pad(body, nome, sk, h, rev=False):
    f = body.newObject("PartDesign::Pad", nome)
    f.Profile = sk; f.Length = h; f.Reversed = rev
    sk.Visibility = False
    return f


def pocket(body, nome, sk, h=None, rev=False, through=False):
    f = body.newObject("PartDesign::Pocket", nome)
    f.Profile = sk
    if through:
        f.Type = "ThroughAll"; f.Midplane = True
    else:
        f.Length = h
    f.Reversed = rev
    sk.Visibility = False
    return f


def remove_feat(doc, body, nomes):
    for n in nomes:
        o = doc.getObject(n)
        if o is not None:
            if o in body.Group:
                body.removeObject(o)
            doc.removeObject(n)


def checa(sk, i, tipo, valor):
    k = sk.Constraints[i]
    if k.Type != tipo or abs(k.Value - valor) > 1e-3:
        raise SystemExit("restricao inesperada em %s[%d]: %s %.3f (esperado %s %.3f)" % (sk.Label, i, k.Type, k.Value, tipo, valor))


# ------------------------------------------------------------------ 2) REDUCAO_V2: planilha, TAMPA e SAIDA
pd = App.openDocument(os.path.join(D, "REDUCAO_V2.FCStd"))
pd.recompute()
ss = pd.getObject("Parametros")
linhas = {13: ("Drol_ext", "22.2 mm", "Alojamento dos 608 (8x22x7). Imprima um anel de teste e ajuste"),
          14: ("Hrol", "7 mm", "Largura do 608 = profundidade do alojamento"),
          17: ("D_ressalto", "15 mm", "Furo do ressalto dos 608 (apoia so na pista externa)"),
          18: ("entre_centros", "%g mm" % C, "Entre centros SAIDA <-> EIXO (polias 20T/40T, correia %g, sem tensor)" % L_CORREIA)}
# TAMPA: tira o que versoes anteriores deste script criaram (pilares, tensor, corte da aba), se ainda existir
tampa = pd.getObject("TAMPA")
remove_feat(pd, tampa, ["Insertos_pilares", "Insertos_pilares_sk", "Escareado_fundo", "Escareado_fundo_sk",
                        "Rasgo_tensor", "Rasgo_tensor_sk", "Remove_aba_eixo", "Remove_aba_eixo_sk"])
usadas = " ".join(e for o in pd.Objects for _, e in o.ExpressionEngine)
for r in (19, 20, 21, 22):                                     # linhas antigas (pilares, tensor, D_passagem)
    al = ss.getAlias("B%d" % r) if ss.getContents("B%d" % r) else None
    if al and ("Parametros." + al) in usadas:
        print("AVISO: linha %d (%s) ainda e usada; mantida" % (r, al))
        continue
    for col in "ABC":
        ss.clear("%s%d" % (col, r))
for r, (al, val, desc) in linhas.items():
    ss.set("A%d" % r, al); ss.set("B%d" % r, val); ss.set("C%d" % r, desc)
    ss.setAlias("B%d" % r, al)
pd.recompute()


def liga_diametro_centro(sk, expr):
    """liga a expr o diametro de cada circulo centrado na origem (furo/alojamento da SAIDA); retorna quantos"""
    n = 0
    for i, k in enumerate(sk.Constraints):
        if k.Type == "Diameter" and 0 <= k.First < sk.GeometryCount:
            c = getattr(sk.Geometry[k.First], "Center", None)
            if c is not None and c.Length < 1e-6:
                sk.setExpression("Constraints[%d]" % i, expr)
                n += 1
    return n


# TAMPA (contorno ja sem a aba do EIXO): so o 608 da SAIDA
n1 = liga_diametro_centro(pd.getObject("Contorno_sk"), "Parametros.D_ressalto")
n2 = liga_diametro_centro(pd.getObject("Alojamento_rolamento_sk"), "Parametros.Drol_ext")
pd.getObject("Alojamento_rolamento").setExpression("Length", "Parametros.Hrol")
pd.recompute()
print("TAMPA: ressalto ligado em %d circulo(s), alojamento em %d; bbox x %.2f..%.2f" % (
    n1, n2, tampa.Shape.BoundBox.XMin, tampa.Shape.BoundBox.XMax))
if tampa.Shape.BoundBox.XMax > 21.05:
    print("AVISO: a TAMPA ainda passa do octogono do motor (x max %.2f)" % tampa.Shape.BoundBox.XMax)

# SAIDA
saida = pd.getObject("SAIDA")
eixo_s = pd.getObject("Eixo_10mm")
eixo_s.Length = (Z_PL0 + HROL) - Z_SAIDA                       # ate o topo do 608 da PLACA_SUPERIOR
eixo_s.Label = "Eixo_8mm"
reb_sk = pd.getObject("Sketch")                               # rebaixo desenhado a mao: reposiciona no cubo da 20T
reb = pd.getObject("Pocket")
z_reb1 = (Z_POL + 16.0) - Z_SAIDA                              # topo do cubo da 20T
reb_sk.AttachmentSupport = [(origem(saida, "XY_Plane"), "")]
reb_sk.MapMode = "FlatFace"
reb_sk.AttachmentOffset = P(V(0, 0, z_reb1), R())
reb.Length = 7.5
reb.Label = "Rebaixo_parafuso_20T"
remove_feat(pd, saida, ["Ressalto_rolamento", "Ressalto_rolamento_sk"])
sk = esboco(saida, "Ressalto_rolamento_sk", 0)
circulo(sk, 0, 0, ESP_D)
pad(saida, "Ressalto_rolamento", sk, Z_T0 - Z_SAIDA)            # encosta na pista interna do 608 da TAMPA
pd.recompute()
for b in (tampa, saida):
    bad = [f.Name for f in b.Group if "Invalid" in f.State or "Error" in f.State]
    print("%s: valido=%s solidos=%d erros=%s" % (b.Name, b.Shape.isValid(), len(b.Shape.Solids), bad))
visivel.normaliza(pd, ocultar=("SOL_MOTOR_cubo_original",))
pd.save()
visivel.devolve_gui(pd, GUI_PD)

# ------------------------------------------------------------------ 3) MONTAGEM_V2
doc = App.openDocument(os.path.join(D, "MONTAGEM_V2.FCStd"))
doc.recompute()

# MANCAL
mancal = doc.getObject("Body")
assert mancal.Label == "MANCAL"
msk = doc.getObject("Sketch")
checa(msk, 13, "DistanceX", msk.Constraints[13].Value)
checa(msk, 18, "Diameter", msk.Constraints[18].Value)
msk.setDatum(13, Q(C, "mm"))
msk.setDatum(18, Q(DRESS, "mm"))
msk1 = doc.getObject("Sketch001")
msk1.AttachmentSupport = [(origem(mancal, "XY_Plane"), "")]     # sem depender da face do Pad
msk1.MapMode = "FlatFace"
msk1.AttachmentOffset = P(V(0, 0, 10.0), R())
checa(msk1, 0, "Diameter", msk1.Constraints[0].Value)
checa(msk1, 2, "DistanceX", msk1.Constraints[2].Value)
msk1.setDatum(0, Q(DROL, "mm"))
msk1.setDatum(2, Q(C, "mm"))
doc.getObject("Pocket").Length = HROL
remove_feat(doc, mancal, ["Furos_pilares", "Furos_pilares_sk", "Orelhas_pilares", "Orelhas_pilares_sk"])   # sem pilares
# o MANCAL e preso na traseira do motor pelos 4 furos de +-15,5 do proprio esboco

# EIXO
eixo = doc.getObject("Body001")
assert eixo.Label == "EIXO"
esk = doc.getObject("Sketch002")
for i, k in enumerate(list(esk.Constraints)):
    if k.Type == "DistanceX":
        esk.delConstraint(i)
        break
esk.addConstraint(Sketcher.Constraint("DistanceX", -1, 1, 0, 3, C))
doc.getObject("Pad001").Length = EIXO_Z1 - EIXO_Z0
ZB = eixo.Placement.Base.z
remove_feat(doc, eixo, ["Rebaixo_polia_40T", "Rebaixo_polia_40T_sk", "Canal_anel_placa", "Canal_anel_placa_sk",
                        "Canal_anel_mancal", "Canal_anel_mancal_sk"])
sk = esboco(eixo, "Rebaixo_polia_40T_sk", Z_HUB40 - ZB)
u = V(math.cos(math.radians(ANG2)), math.sin(math.radians(ANG2)), 0); w = V(-u.y, u.x, 0); c0 = V(C, 0, 0)
poligono(sk, [tuple(c0 + u * a + w * b)[:2] for a, b in ((3, -5), (5, -5), (5, 5), (3, 5))])
pocket(eixo, "Rebaixo_polia_40T", sk, 7.5)                     # parafuso M4 da 40T aperta aqui (cubo z 78,5..86)
for nome, ztopo in (("Canal_anel_placa", Z_ANEL_SUP0 + M_RAN), ("Canal_anel_mancal", Z_ANEL_INF1)):
    sk = esboco(eixo, nome + "_sk", ztopo - ZB)                 # canais DIN 471: Ø7,6 x 0,9
    circulo(sk, C, 0, 10.0); circulo(sk, C, 0, D_RAN)
    pocket(eixo, nome, sk, M_RAN)

# objetos novos (refeitos a cada execucao; a PLACA_SUPERIOR existente e mantida, pois pode ter sido editada a mao)
placa = doc.getObject("PLACA_SUPERIOR")
NOVOS = ["Saida_impressas", "Saida_comprados", "PILAR", "PILAR_2", "ESPACADOR_PLACA", "ESPACADOR_PLACA_2",
         "ESPACADOR_PLACA_3", "ESPACADOR_PLACA_4", "ESPACADOR_608_2_6", "ESPACADOR_608_2_6_EIXO", "ESPACADOR_608_1_0", "ESPACADOR_608_1_0_MANCAL",
         "ESPACADOR_TENSOR", "ROL_608_SAIDA", "ROL_608_SAIDA_TOPO", "ROL_608_EIXO", "ROL_608_EIXO_PLACA", "ROL_608_MANCAL",
         "COLAR_EIXO_8", "ANEL_DIN471_PLACA", "ANEL_DIN471_MANCAL", "PARAFUSO_TENSOR"]
for n in NOVOS:
    o = doc.getObject(n)
    if o is None:
        continue
    if o.TypeId == "PartDesign::Body":
        o.removeObjectsFromDocument()
    doc.removeObject(n)

g_imp = doc.addObject("App::DocumentObjectGroup", "Saida_impressas")
g_com = doc.addObject("App::DocumentObjectGroup", "Saida_comprados")


def corpo(nome, plc):
    b = doc.addObject("PartDesign::Body", nome)
    b.Placement = plc
    g_imp.addObject(b)
    return b


def tubo(nome, De, Di, h, pos):
    b = corpo(nome, P(V(*pos), R()))
    sk = esboco(b, nome + "_sk")
    circulo(sk, 0, 0, De); circulo(sk, 0, 0, Di)
    pad(b, nome + "_pad", sk, h)
    return b


def link(nome, alvo, pos):
    l = doc.addObject("App::Link", nome)
    l.LinkedObject = alvo
    l.Placement = P(V(*pos), R())
    g_imp.addObject(l)
    return l


# PLACA_SUPERIOR: 2o mancal da SAIDA, 1o mancal do EIXO (braco); 4 espacadores nos parafusos do motor
if placa is None:
    placa = corpo("PLACA_SUPERIOR", P(V(0, 0, Z_PL0), R()))
    sk = esboco(placa, "Contorno_sk")
    poligono(sk, OCT)
    pad(placa, "Placa", sk, T_PL)
    sk = esboco(placa, "Braco_eixo_sk")
    x0 = 12.0
    g0 = sk.GeometryCount
    sk.addGeometry(Part.LineSegment(V(x0, -R_BRACO, 0), V(C, -R_BRACO, 0)), False)
    sk.addGeometry(Part.ArcOfCircle(Part.Circle(V(C, 0, 0), V(0, 0, 1), R_BRACO), -math.pi / 2, math.pi / 2), False)
    sk.addGeometry(Part.LineSegment(V(C, R_BRACO, 0), V(x0, R_BRACO, 0)), False)
    sk.addGeometry(Part.LineSegment(V(x0, R_BRACO, 0), V(x0, -R_BRACO, 0)), False)
    for a, pa, b, pb in ((0, 2, 1, 1), (1, 2, 2, 1), (2, 2, 3, 1), (3, 2, 0, 1)):
        sk.addConstraint(Sketcher.Constraint("Coincident", g0 + a, pa, g0 + b, pb))
    pad(placa, "Braco_eixo", sk, T_PL)
    sk = esboco(placa, "Alojamento_608_sk")
    circulo(sk, 0, 0, DROL)
    circulo(sk, C, 0, DROL)
    pocket(placa, "Alojamento_608", sk, HROL, rev=True)
    sk = esboco(placa, "Furos_sk")
    circulo(sk, 0, 0, DRESS)
    circulo(sk, C, 0, DRESS)
    for x, y in STANDOFFS:
        circulo(sk, x, y, 3.4)
    pocket(placa, "Furos", sk, through=True)
    print("PLACA_SUPERIOR criada")
else:
    g_imp.addObject(placa)
    doc.recompute()
    ok = placa.Shape.isInside(V(C, 0, Z_PL0 + 3.5), 1e-6, True) is False and placa.Shape.isInside(V(C + 12.0, 0, Z_PL0 + 3.5), 1e-6, True)
    print("PLACA_SUPERIOR existente mantida; alojamento do EIXO em x=%.2f: %s" % (C, "ok" if ok else
          "NAO CONFERE - ajuste a PLACA a mao para o novo entre centros"))
# espacadores da placa (encaixam no escareado de 1,5 mm da TAMPA)
z_esc = Z_T1 - 1.5
esp = tubo("ESPACADOR_PLACA", 5.8, 3.4, Z_PL0 - z_esc, (STANDOFFS[0][0], STANDOFFS[0][1], z_esc))
for i, (x, y) in enumerate(STANDOFFS[1:], 2):
    link("ESPACADOR_PLACA_%d" % i, esp, (x, y, z_esc))
# espacadores dos 608 (so na pista interna)
tubo("ESPACADOR_608_2_6", ESP_D, ESP_d, Z_POL - (Z_T0 + HROL), (0, 0, Z_T0 + HROL))
e10 = tubo("ESPACADOR_608_1_0", ESP_D, ESP_d, ESP_T, (C, 0, Z_PL0 - ESP_T))      # anel -> 608 da PLACA
link("ESPACADOR_608_1_0_MANCAL", e10, (C, 0, Z_MANCAL_TOPO))                  # 608 do MANCAL <- anel


# comprados (referencia)
def ref(nome, shape):
    o = doc.addObject("Part::Feature", nome)
    o.Shape = shape
    g_com.addObject(o)
    return o


def anel(De, Di, h, pos):
    s = Part.makeCylinder(De / 2, h).cut(Part.makeCylinder(Di / 2, h))
    s.translate(V(*pos))
    return s


ref("ROL_608_SAIDA", anel(22, 8, 7, (0, 0, Z_T0)))
ref("ROL_608_SAIDA_TOPO", anel(22, 8, 7, (0, 0, Z_PL0)))
ref("ROL_608_EIXO_PLACA", anel(22, 8, 7, (C, 0, Z_PL0)))
ref("ROL_608_MANCAL", anel(22, 8, 7, (C, 0, Z_MANCAL_TOPO - HROL)))
ref("ANEL_DIN471_PLACA", anel(13.4, D_RAN, S_ANEL, (C, 0, Z_ANEL_SUP0)))
ref("ANEL_DIN471_MANCAL", anel(13.4, D_RAN, S_ANEL, (C, 0, Z_ANEL_INF1 - S_ANEL)))
print("C %.3f | " % C, end="")
print("EIXO z %.1f..%.1f | canal PLACA z %.2f..%.2f | canal MANCAL z %.2f..%.2f | PLACA z %.1f..%.1f" % (
    EIXO_Z0, EIXO_Z1, Z_ANEL_SUP0, Z_ANEL_SUP0 + M_RAN, Z_ANEL_INF1 - M_RAN, Z_ANEL_INF1, Z_PL0, Z_PL0 + T_PL))

# polias, correia e tensor (do POLIAS_GT2) dentro do App::Part existente
part = doc.getObject("POLIAS_GT2")
for o in list(part.Group):
    if o.TypeId == "Part::Feature":
        part.removeObject(o)
        doc.removeObject(o.Name)
part.Placement = P(V(0, 0, Z_POL), R())
for o in pol.Objects:
    if o.TypeId == "Part::Feature":
        n = doc.addObject("Part::Feature", o.Name)
        n.Label = o.Label
        n.Shape = o.Shape.copy()
        part.addObject(n)

doc.recompute()
erros = [o.Name for o in doc.Objects if "Invalid" in o.State or "Error" in o.State]
print("MONTAGEM_V2 objetos com erro:", erros)
for b in (mancal, eixo, placa):
    print("%s: valido=%s solidos=%d" % (b.Label, b.Shape.isValid(), len(b.Shape.Solids)))
visivel.normaliza(doc)
doc.save()
visivel.devolve_gui(doc, GUI_DOC)
print("salvo")
