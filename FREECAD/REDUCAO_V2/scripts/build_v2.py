# Gera REDUCAO_V2.FCStd (pecas parametricas) e MONTAGEM_V2.FCStd (links posicionados)
import FreeCAD as App, Part, Sketcher, math, os, sys
import InvoluteGearFeature as IG
V = App.Vector
P = App.Placement
R = App.Rotation

XP = float(os.environ.get("XP", "-0.08"))
HF = float(os.environ.get("HF", "1.35"))
RF = float(os.environ.get("RF", "0.2"))
OUT = os.environ.get("OUTDIR", r"C:\LUIZ\PROJECTS\GOTO_TELESCOPE\FREECAD\REDUCAO_V2")
ORIG_DIR = r"C:\LUIZ\PROJECTS\GOTO_TELESCOPE\FREECAD\REDUCAO"
os.makedirs(OUT, exist_ok=True)

doc = App.newDocument("REDUCAO_V2")

# ---------------------------------------------------------------- parametros
ss = doc.addObject("Spreadsheet::Sheet", "Parametros")
rows = [
    ("modulo", "0.9 mm", "Modulo das engrenagens"),
    ("dentes_sol", "12", "Dentes do sol"),
    ("dentes_planeta", "12", "Dentes dos planetas"),
    ("dentes_coroa", "=dentes_sol + 2*dentes_planeta", "Dentes da coroa (calculado)"),
    ("desloc_planeta", str(XP), "Deslocamento de perfil do planeta (negativo = mais folga)"),
    ("raio_pinos", "=modulo*(dentes_sol + dentes_planeta)/2", "Raio dos pinos = distancia sol-planeta (calculado)"),
    ("adendo_sol", "0.95", "Adendo do sol (fracao do modulo)"),
    ("adendo_coroa", "0.55", "Adendo da coroa (curto para evitar interferencia interna)"),
    ("largura", "5 mm", "Largura das engrenagens"),
    ("Dpino", "5 mm", "Diametro dos pinos do porta-planetas"),
    ("Dfuro_planeta", "5.2 mm", "Furo do planeta (ajuste ao pino impresso)"),
    ("Dfuro_sol", "5.2 mm", "Furo central do sol (eixo do motor 5 mm)"),
    ("Drol_ext", "15 mm", "Rolamentos de saida 2x 6700 (10x15x4): diametro externo"),
    ("Hrol", "4 mm", "Largura de cada rolamento 6700 (sao 2 empilhados)"),
    ("reducao_estagio", "=1 + dentes_coroa/dentes_sol", "Reducao por estagio (calculado)"),
    ("reducao_total", "=reducao_estagio^5", "Reducao total, 5 estagios (calculado)"),
]
for i, (alias, val, desc) in enumerate(rows, start=1):
    ss.set("A%d" % i, alias)
    ss.set("B%d" % i, val)
    ss.set("C%d" % i, desc)
    ss.setAlias("B%d" % i, alias)
doc.recompute()

# ---------------------------------------------------------------- helpers
def new_body(name):
    b = doc.addObject("PartDesign::Body", name)
    return b

def plane(body, role="XY_Plane"):
    for f in body.Origin.OriginFeatures:
        if f.Role == role:
            return f

def zaxis(body):
    return plane(body, "Z_Axis")

def sketch(body, name, z=0.0):
    sk = body.newObject("Sketcher::SketchObject", name)
    sk.AttachmentSupport = [(plane(body), "")]
    sk.MapMode = "FlatFace"
    sk.AttachmentOffset = P(V(0, 0, z), R())
    return sk

def circle(sk, cx, cy, d, dexpr=None, xexpr=None, yexpr=None, onV=False, center=False):
    g = sk.addGeometry(Part.Circle(V(cx, cy, 0), V(0, 0, 1), d / 2.0), False)
    c = sk.addConstraint(Sketcher.Constraint("Diameter", g, d))
    if dexpr:
        sk.setExpression("Constraints[%d]" % c, dexpr)
    if center:
        sk.addConstraint(Sketcher.Constraint("Coincident", g, 3, -1, 1))
    else:
        if onV:
            sk.addConstraint(Sketcher.Constraint("PointOnObject", g, 3, -2))
        else:
            c = sk.addConstraint(Sketcher.Constraint("DistanceX", -1, 1, g, 3, cx))
            if xexpr:
                sk.setExpression("Constraints[%d]" % c, xexpr)
        c = sk.addConstraint(Sketcher.Constraint("DistanceY", -1, 1, g, 3, cy))
        if yexpr:
            sk.setExpression("Constraints[%d]" % c, yexpr)
    return g

def polyline(sk, pts):
    n = len(pts)
    for i in range(n):
        sk.addGeometry(Part.LineSegment(V(*pts[i], 0), V(*pts[(i + 1) % n], 0)), False)
    base = sk.GeometryCount - n
    for i in range(n):
        sk.addConstraint(Sketcher.Constraint("Coincident", base + i, 2, base + (i + 1) % n, 1))

def octagon(sk, half=21.0, ch=6.0):
    c = ch / math.sqrt(2)
    a = half - c
    pts = [(-a, -half), (a, -half), (half, -a), (half, a), (a, half), (-a, half), (-half, a), (-half, -a)]
    polyline(sk, pts)

def pad(body, name, prof, L, rev=False, lexpr=None):
    p = body.newObject("PartDesign::Pad", name)
    p.Profile = prof
    p.Length = L
    p.Reversed = rev
    if lexpr:
        p.setExpression("Length", lexpr)
    prof.Visibility = False
    return p

def pocket(body, name, prof, L=None, through=False, rev=False):
    p = body.newObject("PartDesign::Pocket", name)
    p.Profile = prof
    if through:
        p.Type = "ThroughAll"
        p.Midplane = True
    else:
        p.Length = L
    p.Reversed = rev
    prof.Visibility = False
    return p

def polar(body, name, feats, n=3):
    pp = body.newObject("PartDesign::PolarPattern", name)
    pp.Originals = feats
    pp.Axis = (zaxis(body), [""])
    pp.Angle = 360
    pp.Occurrences = n
    for f in feats:
        f.Visibility = False
    body.Tip = pp
    pp.Visibility = True
    doc.recompute()
    return pp

def gear(body, name, zexpr, ext=True, xexpr=None, z0=0.0, haexpr=None):
    o = doc.addObject("Part::Part2DObjectPython", name)
    IG._InvoluteGear(o)
    body.addObject(o)
    o.MapMode = "Deactivated"
    o.Placement = P(V(0, 0, z0), R())
    o.ExternalGear = ext
    o.HighPrecision = True
    o.AddendumCoefficient = 1.0
    if haexpr:
        o.setExpression("AddendumCoefficient", haexpr)
    o.DedendumCoefficient = HF
    o.RootFilletCoefficient = RF
    o.setExpression("Modules", "Parametros.modulo")
    o.setExpression("NumberOfTeeth", zexpr)
    if xexpr:
        o.setExpression("ProfileShiftCoefficient", xexpr)
    return o

RC = "Parametros.raio_pinos"
PIN_Y = RC
SCR_X = "Parametros.raio_pinos * cos(30 deg)"
SCR_Y = "Parametros.raio_pinos * sin(30 deg)"
rc0 = 0.9 * 24 / 2

def holes_pins_screws(body, tag, dpin=5.2, dscr=2.2):
    """furos para os pinos (3x) e parafusos M2 (3x) no disco que encaixa sobre o porta-planetas"""
    s1 = sketch(body, "Furos_pinos_" + tag, 0)
    circle(s1, 0, rc0, dpin, yexpr=PIN_Y, onV=True)
    p1 = pocket(body, "Furo_pino_" + tag, s1, through=True)
    s2 = sketch(body, "Furos_parafusos_" + tag, 0)
    circle(s2, rc0 * math.cos(math.radians(30)), rc0 * 0.5, dscr, xexpr=SCR_X, yexpr=SCR_Y)
    p2 = pocket(body, "Furo_parafuso_" + tag, s2, through=True)
    return polar(body, "Padrao_furos_" + tag, [p1, p2])

# ---------------------------------------------------------------- PLANETA
b = new_body("PLANETA")
g = gear(b, "Engrenagem_planeta", "Parametros.dentes_planeta", xexpr="Parametros.desloc_planeta")
pad(b, "Pad_planeta", g, 5, lexpr="Parametros.largura")
s = sketch(b, "Furo_planeta_sk", 0)
circle(s, 0, 0, 5.2, dexpr="Parametros.Dfuro_planeta", center=True)
pocket(b, "Furo_planeta", s, through=True)

# ---------------------------------------------------------------- SOL_MOTOR (cubo original reaproveitado)
od = App.openDocument(os.path.join(ORIG_DIR, "REDUCAO.FCStd"), True)
orig = od.getObject("Body001")  # SOL_MOTOR
hub = orig.Shape.copy()
hub.Placement = P()
hub = hub.common(Part.makeBox(100, 100, 22.2, V(-50, -50, -20)))  # z <= 2.2 (cubo + espacador)
App.closeDocument(od.Name)
base = doc.addObject("Part::Feature", "SOL_MOTOR_cubo_original")
base.Shape = hub
base.Visibility = False
b = new_body("SOL_MOTOR")
b.BaseFeature = base
g = gear(b, "Engrenagem_sol_motor", "Parametros.dentes_sol", z0=2.2, haexpr="Parametros.adendo_sol")
pad(b, "Pad_sol_motor", g, 5, lexpr="Parametros.largura")
s = sketch(b, "Furo_eixo_motor_sk", 0)
circle(s, 0, 0, 5.2, dexpr="Parametros.Dfuro_sol", center=True)
pocket(b, "Furo_eixo_motor", s, through=True)

# ---------------------------------------------------------------- SOL (estagios intermediarios, era SOL2)
b = new_body("SOL")
s = sketch(b, "Disco_sk", 0)
circle(s, 0, 0, 28.5, center=True)
pad(b, "Disco", s, 2, rev=True)
s = sketch(b, "Espacador_sk", 0)
circle(s, 0, 0, 13.2, center=True)
pad(b, "Espacador", s, 2.2)
g = gear(b, "Engrenagem_sol", "Parametros.dentes_sol", z0=2.2, haexpr="Parametros.adendo_sol")
pad(b, "Pad_sol", g, 5, lexpr="Parametros.largura")
s = sketch(b, "Furo_central_sk", 0)
circle(s, 0, 0, 5.2, dexpr="Parametros.Dfuro_sol", center=True)
pocket(b, "Furo_central", s, through=True)
holes_pins_screws(b, "sol")

# ---------------------------------------------------------------- SUPORTE (porta-planetas)
b = new_body("SUPORTE")
s = sketch(b, "Disco_sk", 0)
circle(s, 0, 0, 28.5, center=True)
circle(s, 0, 0, 14.0, center=True)
pad(b, "Disco", s, 2, rev=True)
s = sketch(b, "Alma_sk", 0)
circle(s, 0, 0, 27.0, center=True)
circle(s, 0, 0, 15.0, center=True)
pad(b, "Alma", s, 5.5)
s = sketch(b, "Alivio_planeta_sk", 5.5)
circle(s, 0, rc0, 16.0, yexpr=PIN_Y, onV=True)
pk = pocket(b, "Alivio_planeta", s, L=5.5)
polar(b, "Padrao_alivio", [pk])
s = sketch(b, "Pino_sk", 0)
circle(s, 0, rc0, 5.0, dexpr="Parametros.Dpino", yexpr=PIN_Y, onV=True)
pd = pad(b, "Pino", s, 7.5)
polar(b, "Padrao_pinos", [pd])
s = sketch(b, "Furo_M2_sk", 5.5)
circle(s, rc0 * math.cos(math.radians(30)), rc0 * 0.5, 2.0, xexpr=SCR_X, yexpr=SCR_Y)
pk = pocket(b, "Furo_M2", s, L=4)
polar(b, "Padrao_M2", [pk])

# ---------------------------------------------------------------- SAIDA
b = new_body("SAIDA")
s = sketch(b, "Disco_sk", 0)
circle(s, 0, 0, 28.5, center=True)
pad(b, "Disco", s, 2, rev=True)
holes_pins_screws(b, "saida")
s = sketch(b, "Eixo_sk", 0)
circle(s, 0, 0, 10.0, center=True)
pad(b, "Eixo_10mm", s, 10)
s = sketch(b, "Sextavado_sk", 10)
hx = [(5 * math.cos(math.radians(90 + 60 * k)), 5 * math.sin(math.radians(90 + 60 * k))) for k in range(6)]
polyline(s, hx)
pad(b, "Sextavado", s, 8)
s = sketch(b, "Furo_topo_sk", 18)
circle(s, 0, 0, 3.0, center=True)
pocket(b, "Furo_topo", s, L=5)

# ---------------------------------------------------------------- TAMPA (com 2 rolamentos 6700 empilhados)
b = new_body("TAMPA")
s = sketch(b, "Contorno_sk", 0)
octagon(s)
for sx, sy in ((-1, 1), (1, 1), (1, -1), (-1, -1)):
    circle(s, 15.5 * sx, 15.5 * sy, 3.2)
circle(s, 0, 0, 12.0, center=True)
pad(b, "Tampa", s, 9)
s = sketch(b, "Escareado_sk", 9)
for sx, sy in ((-1, 1), (1, 1), (1, -1), (-1, -1)):
    circle(s, 15.5 * sx, 15.5 * sy, 6.0)
pocket(b, "Escareado", s, L=1.5)
s = sketch(b, "Alojamento_rolamento_sk", 0)
circle(s, 0, 0, 15.0, dexpr="Parametros.Drol_ext", center=True)
p = pocket(b, "Alojamento_rolamento", s, L=8, rev=True)
p.setExpression("Length", "2*Parametros.Hrol")

# ---------------------------------------------------------------- CAIXA (coroa interna real)
b = new_body("CAIXA")
s = sketch(b, "Contorno_sk", 0)
octagon(s)
for sx, sy in ((-1, 1), (1, 1), (1, -1), (-1, -1)):
    circle(s, 15.5 * sx, 15.5 * sy, 3.5)
pad(b, "Caixa", s, 62.8)
g = gear(b, "Coroa_interna", "Parametros.dentes_coroa", ext=False, z0=0, haexpr="Parametros.adendo_coroa")
pocket(b, "Coroa", g, through=True)

doc.recompute()
for o in doc.Objects:
    if o.TypeId == "PartDesign::Body":
        chain = []
        f = o.Tip
        while f is not None and len(chain) < 60:
            chain.append(f.Name)
            f = getattr(f, "BaseFeature", None)
        feats = [x for x in o.Group if x.isDerivedFrom("PartDesign::Feature")]
        print("%s tip=%s chain_len=%d feats=%d" % (o.Name, o.Tip.Name, len(chain), len(feats)))
bad = [o.Name for o in doc.Objects if "Invalid" in o.State or "Error" in o.State]
print("objetos com erro:", bad)
for o in doc.Objects:
    if o.TypeId == "PartDesign::Body":
        sh = o.Shape
        print("%-10s valid=%s solids=%d vol=%.1f bb=%.2fx%.2fx%.2f z=[%.2f,%.2f]" % (
            o.Name, sh.isValid(), len(sh.Solids), sh.Volume, sh.BoundBox.XLength, sh.BoundBox.YLength,
            sh.BoundBox.ZLength, sh.BoundBox.ZMin, sh.BoundBox.ZMax))
doc.saveAs(os.path.join(OUT, "REDUCAO_V2.FCStd"))
print("salvo")
