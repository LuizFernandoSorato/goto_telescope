# -*- coding: utf-8 -*-
# Revisao 3 da montagem equatorial: le MONTAGEM_EQ_V2.FCStd (nao altera) e grava MONTAGEM_EQ_V3.FCStd.
#
# O que muda:
#   1. apaga as copias duplicadas das pecas dos redutores (soltas dentro de RA e DEC)
#   2. ACOPLADOR1/2: placa 6 mm, cubo conico Ø28->Ø22 com 16,5 mm, furo D com 20 mm de encaixe, parafuso de
#      trava M3 (sem cabeca) contra a face plana do eixo, furos M3 (Ø3,4) e, no ACOPLADOR2, porcas M3 embutidas
#   3. EIXOs de 8 mm alongados na ponta do MANCAL e com face plana (D) no trecho do acoplador; o conjunto DEC
#      se afasta do MANCAL RA e o tubo se afasta do MANCAL DEC para dar 2 mm de folga
#   4. sela Vixen (SELA_DEC) presa no ACOPLADOR2 + barra Vixen 200 mm (comprada) presa na SAPATA: o tubo
#      desliza na sela para balancear o DEC; no modelo ja esta na posicao balanceada (pela massa estimada)
#   5. contrapeso: TAMPA_CW (presa pelas 4 barras M3 do redutor DEC), barra M12 e copo impresso que se enche de
#      esferas de aco/chumbinho; a posicao e a massa sao calculadas para balancear o RA
#   6. tira a sobreposicao do ACOPLADOR3 no MANCAL RA e poe a latitude em LAT (pivo da BASE)
#   7. BASE: 0,25 mm de folga de cada lado da haste do ACOPLADOR3 e furo Ø5,2 para rosca 1/4"-20
#   8. tripe girado 60 graus (o contrapeso fica entre duas pernas)
#
# Rodar (PowerShell):
#   & "C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe" scripts\revisao3.py
import math
import os
import re
import sys
import zipfile

import FreeCAD as App
import Part

V = App.Vector
P = App.Placement
R = App.Rotation

D = r"C:\LUIZ\PROJECTS\GOTO_TELESCOPE\FREECAD\MONTAGEM_EQ"
ORIGEM = os.path.join(D, "MONTAGEM_EQ_V2.FCStd")
DESTINO = os.path.join(D, os.environ.get("V3_NOME", "MONTAGEM_EQ_V3.FCStd"))
STL_DIR = os.path.join(D, "STL_V3")
sys.path.insert(0, os.path.join(D, "scripts"))
import eq_massas as MM  # noqa: E402

LAT = float(os.environ.get("LAT", "28.5"))  # latitude (modulo), graus
FOLGA = 2.0            # folga entre acoplador (gira) e mancal (parado)
T_PLACA = 6.0          # placa do acoplador
L_CUBO = 16.5          # cubo do acoplador (topo em z = 22,5)
D_CUBO_BASE, D_CUBO_TOPO = 28.0, 22.0
ENCAIXE = 20.0         # profundidade do furo D
D_FURO, PLANO_FURO = 8.15, 3.55   # furo D impresso: Ø8,15 com a face plana a 3,55 mm do centro (eixo: Ø8 com plano a 3,5)
FOLGA_PONTA = 0.5      # ponta do eixo ate o fundo do furo
L_BARRA_CW = float(os.environ.get("L_BARRA_CW", "250"))   # barra M12 do contrapeso (comprimento total)
R_COPO, H_COPO = 40.0, 50.0                                 # copo do contrapeso (Ø80 x 50, cabe ~0,85 kg de esferas)
GIRO_TRIPE = 60.0
H_SELA, H_VIXEN = 10.0, 15.0
ESFERAS = 4.6          # g/cm3 aparente de esferas de aco (chumbinho de chumbo ~6,8)

doc = App.openDocument(ORIGEM)
doc.recompute()
L = lambda n: doc.getObjectsByLabel(n)[0]


def gp(o):
    pai = o.getParentGeoFeatureGroup()
    return P() if pai is None else gp(pai).multiply(pai.Placement)


def glob(o):
    return gp(o).multiply(o.Placement)


def forma(o):
    s = Part.getShape(o) if o.TypeId != "Part::Feature" else o.Shape
    s = s.copy(); s.Placement = gp(o).multiply(s.Placement)
    return s


def raiz(o):
    pai = o.getParentGeoFeatureGroup()
    return o if pai is None else raiz(pai)


def move(objs, plc):
    for o in objs:
        o.Placement = plc.multiply(o.Placement)


def transl(objs, v):
    move(objs, P(v, R()))


def bisseca(f, a, b, n=40):
    """menor t em [a,b] com f(t) verdadeiro (f monotona: falso ... verdadeiro)"""
    for _ in range(n):
        m = 0.5 * (a + b)
        if f(m):
            b = m
        else:
            a = m
    return b


relatorio = []


def rel(txt):
    print(txt)
    relatorio.append(txt)


# =============================================================== 1. duplicadas
apagar = []
for grupo in ("RA", "DEC"):
    g = L(grupo)
    filhos_sub = [o for o in doc.Objects if raiz(o) is g and o.getParentGeoFeatureGroup() is not g and o.TypeId == "Part::Feature"]
    chaves = {}
    for o in filhos_sub:
        s = forma(o); b = s.BoundBox
        chaves[(round(s.Volume), round(b.XMin, 1), round(b.YMin, 1), round(b.ZMin, 1), round(b.XMax, 1), round(b.ZMax, 1))] = o
    for o in list(g.Group):
        if o.TypeId != "Part::Feature":
            continue
        s = forma(o); b = s.BoundBox
        k = (round(s.Volume), round(b.XMin, 1), round(b.YMin, 1), round(b.ZMin, 1), round(b.XMax, 1), round(b.ZMax, 1))
        if k in chaves:
            apagar.append(o.Name)
for n in apagar:
    doc.removeObject(n)
doc.recompute()
rel("1. duplicadas apagadas: %d" % len(apagar))

RA, DEC, OTA = L("RA"), L("DEC"), L("OTA_GREIKA_70070")
A1, A2, A3, BASE, TRIPE = L("ACOPLADOR1"), L("ACOPLADOR2"), L("ACOPLADOR3"), L("BASE"), L("TRIPE_GREIKA_70070")
EIXO_RA, EIXO_DEC = L("EIXO"), L("EIXO001")
MANCAL_RA, MANCAL_DEC = L("MANCAL"), L("MANCAL002")
ROL_M_RA, ROL_M_DEC = L("ROL_608_MANCAL"), L("ROL_608_MANCAL002")
SAPATA = L("SAPATA")


# =============================================================== 2. acopladores (PartDesign, continuam editaveis)
def plano_xy(body):
    return [f for f in body.Origin.OriginFeatures if f.Role == "XY_Plane"][0]


def esboco(body, nome, offset):
    sk = body.newObject("Sketcher::SketchObject", nome)
    sk.AttachmentSupport = [(plano_xy(body), "")]
    sk.MapMode = "FlatFace"
    sk.AttachmentOffset = offset
    return sk


def poligono(sk, pts):
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        sk.addGeometry(Part.LineSegment(V(a[0], a[1], 0), V(b[0], b[1], 0)))


def hexagono(sk, cx, cy, af):
    rc = af / math.sqrt(3)
    poligono(sk, [(cx + rc * math.cos(math.radians(30 + 60 * k)), cy + rc * math.sin(math.radians(30 + 60 * k))) for k in range(6)])


def bolso(body, nome, sk, comp):
    pk = body.newObject("PartDesign::Pocket", nome)
    pk.Profile = sk
    pk.Type = "Length"
    pk.Length = comp
    return pk


def restr(sk, valor_antigo, valor_novo, tipo=None):
    for i, c in enumerate(sk.Constraints):
        if abs(c.Value - valor_antigo) < 1e-6 and (tipo is None or c.Type == tipo):
            sk.setDatum(i, App.Units.Quantity("%g mm" % valor_novo))


def acoplador(body, sk_placa, pad_placa, sk_cubo, pad_cubo, sk_furo, pk_furo, porcas):
    z_topo = T_PLACA + L_CUBO
    pad_placa.Length = T_PLACA
    restr(sk_placa, 4.0, 3.4, "Diameter")                     # furos M3
    sk_cubo.AttachmentSupport = [(plano_xy(body), "")]
    sk_cubo.MapMode = "FlatFace"
    sk_cubo.AttachmentOffset = P(V(0, 0, T_PLACA), R())
    restr(sk_cubo, 16.0, D_CUBO_BASE, "Diameter")
    pad_cubo.Length = L_CUBO
    pad_cubo.TaperAngle = -math.degrees(math.atan((D_CUBO_BASE - D_CUBO_TOPO) / 2.0 / L_CUBO))
    sk_furo.AttachmentSupport = [(plano_xy(body), "")]
    sk_furo.MapMode = "FlatFace"
    sk_furo.AttachmentOffset = P(V(0, 0, z_topo), R())
    restr(sk_furo, 8.0, D_FURO, "Diameter")                 # folga de impressao no furo D
    restr(sk_furo, 3.5, PLANO_FURO, "Distance")
    pk_furo.Length = ENCAIXE
    body.Tip = pk_furo
    doc.recompute()
    # conferir o cone (o sinal de TaperAngle)
    s = body.Shape.copy(); s.Placement = P()
    if s.isInside(V(D_CUBO_TOPO / 2 + 1.5, 0, z_topo - 0.5), 0.01, True):
        pad_cubo.TaperAngle = -pad_cubo.TaperAngle
        doc.recompute()
    pref = body.Label[-1]
    z_meio = z_topo - ENCAIXE / 2.0
    # parafuso de trava M3 (sem cabeca) do lado da face plana (y+)
    sk = esboco(body, "Trava_M3_sk%s" % pref, P(V(0, 15, 0), R(V(1, 0, 0), -90)))
    sk.addGeometry(Part.Circle(V(0, -z_meio, 0), V(0, 0, 1), 1.6))
    pk = bolso(body, "Trava_M3_%s" % pref, sk, 15 - 3.5)
    body.Tip = pk
    doc.recompute()
    s = body.Shape.copy(); s.Placement = P()
    if s.isInside(V(0, 9, z_meio), 0.01, True) or not s.isInside(V(0, -9, z_meio), 0.01, True):
        sk.AttachmentOffset = P(V(0, 15, 0), R(V(1, 0, 0), 90))
        sk.Geometry = []
        sk.addGeometry(Part.Circle(V(0, z_meio, 0), V(0, 0, 1), 1.6))
        pk.Reversed = True
        doc.recompute()
        s = body.Shape.copy(); s.Placement = P()
    assert not s.isInside(V(0, 9, z_meio), 0.01, True) and s.isInside(V(0, -9, z_meio), 0.01, True), "furo da trava errado"
    # rasgo da porca M3 (aberto no topo do cubo)
    sk = esboco(body, "Porca_trava_sk%s" % pref, P(V(0, 0, z_topo), R()))
    poligono(sk, [(-2.9, 6.0), (2.9, 6.0), (2.9, 8.7), (-2.9, 8.7)])
    pk = bolso(body, "Porca_trava_%s" % pref, sk, z_topo - (z_meio - 3.0))
    body.Tip = pk
    if porcas:
        sk = esboco(body, "Porcas_M3_sk%s" % pref, P(V(0, 0, T_PLACA), R()))
        for x in (-15, 15):
            for y in (-10, 10):
                hexagono(sk, x, y, 5.7)
        pk = bolso(body, "Porcas_M3_%s" % pref, sk, 2.6)
        body.Tip = pk
    doc.recompute()
    for f in body.Group:
        f.Visibility = (f == body.Tip)
    s = body.Shape.copy(); s.Placement = P()
    assert s.isValid() and len(s.Solids) == 1, body.Label
    return s


acoplador(A1, *[doc.getObject(n) for n in ("Sketch", "Pad", "Sketch001", "Pad001", "Sketch002", "Pocket")], porcas=False)
acoplador(A2, *[doc.getObject(n) for n in ("Sketch003", "Pad002", "Sketch004", "Pad003", "Sketch005", "Pocket001")], porcas=True)
rel("2. ACOPLADOR1/2: placa %.0f mm, cubo Ø%.0f->Ø%.0f x %.1f mm, furo D com %.0f mm, trava M3, furos Ø3,4" % (
    T_PLACA, D_CUBO_BASE, D_CUBO_TOPO, L_CUBO, ENCAIXE))


def eixo_z(o):
    return glob(o).Rotation.multVec(V(0, 0, 1))


def centra(acop, eixo):
    """poe o cubo do acoplador coaxial com o eixo (na V2 estavam 0,1 mm fora)"""
    s = forma(eixo)
    cil = max((f for f in s.Faces if isinstance(f.Surface, Part.Cylinder) and abs(f.Surface.Radius - 4) < 0.05), key=lambda f: f.Area)
    c, d = V(cil.Surface.Center), V(cil.Surface.Axis)
    d.normalize()
    o = glob(acop).Base
    off = (c - o) - d * (c - o).dot(d)
    transl([acop], off)
    return off.Length


rel("   acopladores centrados nos eixos: ACOPLADOR1 %.2f mm, ACOPLADOR2 %.2f mm" % (centra(A1, EIXO_RA), centra(A2, EIXO_DEC)))


def sobrepos(a, b):
    sa, sb = forma(a), forma(b)
    if not sa.BoundBox.intersect(sb.BoundBox):
        return 0.0
    return sa.common(sb).Volume


# =============================================================== 3. afastamentos (folga de 2 mm) e sobreposicoes
z1 = eixo_z(A1)                       # aponta para o MANCAL RA
z2 = eixo_z(A2)                       # aponta para o MANCAL DEC
# ACOPLADOR1 encostado (sem invadir) no MANCAL DEC
dec_lado = [DEC, A2, OTA]
v0 = sobrepos(A1, MANCAL_DEC)
if v0 > 0.01:
    t = bisseca(lambda t: (transl(dec_lado, z1 * -t), sobrepos(A1, MANCAL_DEC) < 0.01, transl(dec_lado, z1 * t))[1], 0, 3)
    transl(dec_lado, z1 * -t)
    rel("   ACOPLADOR1 x MANCAL DEC: %.1f mm3 -> afastado %.2f mm" % (v0, t))
# conjunto DEC (com o ACOPLADOR1) se afasta do MANCAL RA ate FOLGA
fixos_ra = [forma(MANCAL_RA), forma(ROL_M_RA)]
mov1 = [DEC, A1, A2, OTA]


def folga1():
    s = forma(A1)
    return min(s.distToShape(f)[0] for f in fixos_ra)


t1 = bisseca(lambda t: (transl(mov1, z1 * -t), folga1() >= FOLGA, transl(mov1, z1 * t))[1], 0, 40)
transl(mov1, z1 * -t1)
mov2 = [A2, OTA]
fixos_dec = [forma(MANCAL_DEC), forma(ROL_M_DEC)]


def folga2():
    s = forma(A2)
    return min(s.distToShape(f)[0] for f in fixos_dec)


t2 = bisseca(lambda t: (transl(mov2, z2 * -t), folga2() >= FOLGA, transl(mov2, z2 * t))[1], 0, 40)
transl(mov2, z2 * -t2)
rel("3. conjunto DEC afastado %.2f mm ao longo do RA; tubo afastado %.2f mm ao longo do DEC (folga %.1f mm)" % (t1, t2, FOLGA))


# =============================================================== 4. sela Vixen + barra Vixen
def cyl(r, h, p=(0, 0, 0), d=(0, 0, 1)):
    return Part.makeCylinder(r, h, V(*p), V(*d))


def box(x0, x1, y0, y1, z0, z1_):
    return Part.makeBox(x1 - x0, y1 - y0, z1_ - z0, V(x0, y0, z0))


def hexa(af, h, p=(0, 0, 0), d=(0, 0, 1), rot=30.0):
    rc = af / math.sqrt(3)
    w = Part.makePolygon([V(rc * math.cos(math.radians(rot + 60 * k)), rc * math.sin(math.radians(rot + 60 * k)), 0) for k in range(7)])
    s = Part.Face(w).extrude(V(0, 0, h))
    s.Placement = P(V(*p), R(V(0, 0, 1), V(*d)))
    return s


GB = 44.6; ANG = math.radians(75); HJ = 12.0
sela = box(-35, 35, -55, 55, 0, H_SELA)
xa = -GB / 2; xb = xa + HJ / math.tan(ANG)
jaw_fixa = Part.Face(Part.makePolygon([V(-35, -55, H_SELA), V(xa, -55, H_SELA), V(xb, -55, H_SELA + HJ), V(-35, -55, H_SELA + HJ),
                                      V(-35, -55, H_SELA)])).extrude(V(0, 110, 0))
sela = sela.fuse([jaw_fixa, box(26, 35, -55, 55, H_SELA, H_SELA + HJ)])
for y in (-30, 30):                                  # 2 parafusos M6 de aperto com porca embutida
    sela = sela.cut(cyl(3.25, 14, (23, y, H_SELA + 6), (1, 0, 0))).cut(hexa(10.3, 5.5, (29.5, y, H_SELA + 6), (1, 0, 0)))
for x in (-10, 10):                                  # 4 M3 para o ACOPLADOR2 (cabeca embutida, fica sob a barra)
    for y in (-15, 15):
        sela = sela.cut(cyl(1.7, H_SELA, (x, y, 0))).cut(cyl(3.3, 3.5, (x, y, H_SELA - 3.5)))
sela = sela.removeSplitter()
# quadro da sela -> quadro do ACOPLADOR2: x_sela = y_acop, y_sela = x_acop (ao longo do tubo), z_sela = -z_acop
P_SA = P(V(), R(App.Matrix(0, 1, 0, 0, 1, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 1)))
G_SA = glob(A2).multiply(P_SA)
# tubo sobre a barra: o fundo da SAPATA (z local 0) fica em z_sela = H_SELA + H_VIXEN
g_sap = glob(SAPATA)
p_sap = G_SA.inverse().multVec(g_sap.Base)
transl([OTA], G_SA.Rotation.multVec(V(0, 0, H_SELA + H_VIXEN - p_sap.z)))
g_sap = glob(SAPATA)
p_sap = G_SA.inverse().multVec(g_sap.Base)
meia = 22.0 - H_VIXEN / math.tan(ANG)
perfil = Part.Face(Part.makePolygon([V(-22, 0, H_SELA), V(22, 0, H_SELA), V(meia, 0, H_SELA + H_VIXEN), V(-meia, 0, H_SELA + H_VIXEN), V(-22, 0, H_SELA)]))
vixen = perfil.extrude(V(0, 200, 0))
vixen.translate(V(0, p_sap.y - 100, 0))
for y in (-30, 30):
    vixen = vixen.cut(cyl(3.2, H_VIXEN, (0, p_sap.y + y, H_SELA)))
o_sela = doc.addObject("Part::Feature", "SELA_DEC"); o_sela.Shape = sela; o_sela.Placement = G_SA
o_vix = doc.addObject("Part::Feature", "BARRA_VIXEN_200"); o_vix.Shape = vixen; o_vix.Placement = G_SA
rel("4. SELA_DEC (impressa) + BARRA_VIXEN_200 (comprada); a SAPATA assenta na barra (tubo subiu %.1f mm)" % (H_SELA + H_VIXEN))


# =============================================================== 5. eixos alongados com face plana
def alonga(eixo, acop):
    ga = glob(acop)
    za = ga.Rotation.multVec(V(0, 0, 1))
    s = forma(eixo)
    ponta = min((v.Point for v in s.Vertexes), key=lambda p: (p - ga.Base).dot(za))
    s_ponta = (ponta - ga.Base).dot(za)
    alvo = T_PLACA + L_CUBO - ENCAIXE + FOLGA_PONTA
    e = s_ponta - alvo
    # centro da ponta no eixo do acoplador
    c = ga.Base + za * s_ponta
    novo = s.fuse(Part.makeCylinder(4.0, e + 0.01, c + za * 0.01, za * -1))
    plano = box(-6, 6, 3.5, 6, alvo - 0.2, T_PLACA + L_CUBO + 2.0)
    plano.Placement = ga
    novo = novo.cut(plano).removeSplitter()
    assert novo.isValid() and len(novo.Solids) == 1
    comp_antigo = max((v.Point - c).dot(za) for v in s.Vertexes) - min((v.Point - c).dot(za) for v in s.Vertexes)
    novo.Placement = gp(eixo).inverse().multiply(novo.Placement)
    eixo.Shape = novo
    return e, comp_antigo + e


e1, c1 = alonga(EIXO_RA, A1)
e2, c2 = alonga(EIXO_DEC, A2)
rel("5. EIXO RA +%.1f mm (total %.1f mm), EIXO DEC +%.1f mm (total %.1f mm); face plana de 0,5 mm nos ultimos %.0f mm" % (
    e1, c1, e2, c2, ENCAIXE + 1))


# =============================================================== 6. contrapeso (dentro do App::Part DEC, quadro local)
grp_imp = L("Saida_impressas001")
pl = L("PLACA_SUPERIOR002").Shape.BoundBox                   # local DEC (Part::Feature dentro de App::Part sem giro)
ZP = pl.ZMax                                                  # topo da placa (lado do contrapeso)
XE = 29.35                                                    # linha do EIXO DEC
tampa = box(pl.XMin, pl.XMax, pl.YMin, pl.YMax, ZP, ZP + 8)
tampa = tampa.fuse(cyl(14, 16, (XE, 0, ZP + 8))).removeSplitter()
for x in (-15.5, 15.5):
    for y in (-15.5, 15.5):
        tampa = tampa.cut(cyl(1.7, 8, (x, y, ZP)))
tampa = tampa.cut(hexa(18.4, 10.5, (XE, 0, ZP + 24 - 10.5))).cut(cyl(6.3, 20, (XE, 0, ZP + 4)))
tampa = tampa.removeSplitter()
o_tcw = doc.addObject("Part::Feature", "TAMPA_CW"); o_tcw.Shape = tampa
barra = cyl(6.0, L_BARRA_CW, (XE, 0, ZP + 4))
o_bar = doc.addObject("Part::Feature", "BARRA_M12_CW"); o_bar.Shape = barra
porca_tampa = hexa(18, 10, (XE, 0, ZP + 24 - 10.5)).cut(cyl(6, 10, (XE, 0, ZP + 24 - 10.5)))
porca_trava = hexa(18, 10, (XE, 0, ZP + 24)).cut(cyl(6, 10, (XE, 0, ZP + 24)))
o_pt = doc.addObject("Part::Feature", "PORCAS_M12_TAMPA"); o_pt.Shape = Part.makeCompound([porca_tampa, porca_trava])


RC, HC = R_COPO, H_COPO
RI = RC - 2.4                      # parede


def copo_formas(z0, h_ench):
    copo = cyl(RC, HC, (XE, 0, z0)).cut(cyl(RI, HC - 2.99, (XE, 0, z0 + 3))).fuse(cyl(9, HC, (XE, 0, z0))).cut(cyl(6.3, HC, (XE, 0, z0)))
    copo = copo.removeSplitter()
    tp = cyl(RC, 3, (XE, 0, z0 + HC)).fuse(cyl(RI - 0.2, 3, (XE, 0, z0 + HC - 3)).cut(cyl(RI - 2.0, 3, (XE, 0, z0 + HC - 3))))
    tp = tp.cut(cyl(9.2, 6, (XE, 0, z0 + HC - 3))).removeSplitter()
    ench = cyl(RI - 0.2, h_ench, (XE, 0, z0 + 3)).cut(cyl(9.2, h_ench, (XE, 0, z0 + 3)))
    porcas = Part.makeCompound([hexa(18, 10, (XE, 0, z0 - 10)).cut(cyl(6, 10, (XE, 0, z0 - 10))),
                                hexa(18, 10, (XE, 0, z0 + HC + 3)).cut(cyl(6, 10, (XE, 0, z0 + HC + 3)))])
    return copo, tp, ench, porcas


o_copo = doc.addObject("Part::Feature", "CONTRAPESO_COPO")
o_tcopo = doc.addObject("Part::Feature", "CONTRAPESO_TAMPA")
o_ench = doc.addObject("Part::Feature", "CONTRAPESO_ENCHIMENTO")
o_pcopo = doc.addObject("Part::Feature", "PORCAS_M12_CONTRAPESO")
for o in (o_tcw, o_bar, o_pt, o_copo, o_tcopo, o_ench, o_pcopo):
    grp_imp.addObject(o)


def poe_copo(z0, h_ench):
    copo, tp, ench, porcas = copo_formas(z0, max(h_ench, 0.2))
    o_copo.Shape, o_tcopo.Shape, o_ench.Shape, o_pcopo.Shape = copo, tp, ench, porcas


AREA_ENCH = math.pi * ((RI - 0.2) ** 2 - 9.2 ** 2)
H_MAX = HC - 6.0
M_MAX = AREA_ENCH * H_MAX / 1000 * ESFERAS

# =============================================================== 7. balanceamento


def eixo_cil(o):
    s = forma(o); melhor = None
    for f in s.Faces:
        if isinstance(f.Surface, Part.Cylinder) and abs(f.Surface.Radius - 4.0) < 0.05 and (melhor is None or f.Area > melhor.Area):
            melhor = f
    d = V(melhor.Surface.Axis); d.normalize()
    return V(melhor.Surface.Center), d if d.z > 0 else d * -1


def cruzamento():
    pra, dra = eixo_cil(EIXO_RA); pde, dde = eixo_cil(EIXO_DEC)
    w = pra - pde; b_ = dra.dot(dde); d_, e_ = dra.dot(w), dde.dot(w)
    return pra + dra * ((b_ * e_ - d_) / (1 - b_ * b_)), pra, dra, pde, dde


def direcao_tubo():
    cil = max((f for f in forma(L("TUBO")).Faces if isinstance(f.Surface, Part.Cylinder)), key=lambda f: f.Area)
    t = V(cil.Surface.Axis); t.normalize()
    return t


# DEC: desliza o tubo (com a barra Vixen) ao longo do tubo ate o CM ficar no eixo DEC
I, pra, dra, pde, dde = cruzamento()
td = direcao_tubo()
for _ in range(3):
    M, c = MM.cm(doc, MM.conjunto_dec(doc))
    perp = (c - I) - dde * (c - I).dot(dde)
    transl([OTA, o_vix], td * -perp.dot(td))
M, c = MM.cm(doc, MM.conjunto_dec(doc))
perp = (c - I) - dde * (c - I).dot(dde)
desl = (glob(SAPATA).Base - G_SA.Base).dot(td)
rel("7. DEC: conjunto %.0f g; tubo deslizado na sela, SAPATA a %+.1f mm do eixo DEC ao longo do tubo; sobra %.2f mm (%.3f N.m)" % (
    M, desl, perp.Length, M / 1000 * 9.81 * perp.Length / 1000))
assert abs(desl) < 100 - 55, "a barra Vixen sairia da sela"

# RA: posicao do copo e massa de enchimento
z_min = ZP + 24 + 10 + 12          # depois da porca de trava + porca do copo
z_max = ZP + 4 + L_BARRA_CW - (HC + 3) - 10 - 3
melhor = None
for frac in (1.0, 0.75, 0.5, 0.25, 0.0):            # o mais longe possivel: menos massa, sobra para camera
    z0 = z_min + frac * (z_max - z_min)
    h = 17.0
    for _ in range(25):
        poe_copo(z0, h)
        doc.recompute()
        MM.DENS_ESPECIAL["CONTRAPESO_ENCHIMENTO"] = ESFERAS
        M, c = MM.cm(doc, MM.conjunto_ra(doc))
        I, pra, dra, pde, dde = cruzamento()
        s_dec = ((c - I) - dra * (c - I).dot(dra)).dot(dde)
        # momento que falta / braco do enchimento
        me, ce = MM.cm(doc, [o_ench])
        braco = -(ce - I).dot(dde)
        dm = M * s_dec / braco                       # g a mais de enchimento
        h_novo = h + dm / (AREA_ENCH * ESFERAS / 1000)
        if abs(h_novo - h) < 0.01:
            break
        h = h_novo
    if 2.0 <= h <= H_MAX:
        melhor = (z0, h)
        break
assert melhor, "contrapeso nao cabe: aumente L_BARRA_CW"
z0, h = melhor
poe_copo(z0, h)
doc.recompute()
M, c = MM.cm(doc, MM.conjunto_ra(doc))
I, pra, dra, pde, dde = cruzamento()
perp_ra = (c - I) - dra * (c - I).dot(dra)
m_ench = AREA_ENCH * h / 1000 * ESFERAS
mcw, ccw = MM.cm(doc, [o_copo, o_tcopo, o_ench, o_pcopo])
rel("   RA: conjunto %.0f g; contrapeso (copo+tampa+porcas+enchimento) %.0f g a %.0f mm do cruzamento; enchimento %.0f g "
    "de esferas de aco (copo cheio: ~%.0f g); sobra %.2f mm" % (M, mcw, -(ccw - I).dot(dde), m_ench, M_MAX, perp_ra.Length))

# =============================================================== 8. ACOPLADOR3 x MANCAL RA e latitude
z3 = eixo_z(A3)
todos = [RA, DEC, A1, A2, OTA, o_sela, o_vix]
v0 = sobrepos(A3, MANCAL_RA)
if v0 > 0.01:
    t3 = bisseca(lambda t: (transl(todos, z3 * -t), sobrepos(A3, MANCAL_RA) < 0.01, transl(todos, z3 * t))[1], 0, 3)
    transl(todos, z3 * -t3)
    rel("8. ACOPLADOR3 x MANCAL RA: %.0f mm3 -> afastado %.2f mm" % (v0, t3))
# pivo: furo Ø5 da BASE que coincide com um furo do ACOPLADOR3
fb = [f for f in forma(BASE).Faces if isinstance(f.Surface, Part.Cylinder) and abs(f.Surface.Radius - 2.5) < 0.02]
fa = [f for f in forma(A3).Faces if isinstance(f.Surface, Part.Cylinder) and abs(f.Surface.Radius - 2.5) < 0.02]
piv = None
for f in fb:
    for g in fa:
        c1_, c2_ = V(f.Surface.Center), V(g.Surface.Center)
        dd = c1_ - c2_; ax = V(f.Surface.Axis)
        if (dd - ax * dd.dot(ax)).Length < 0.5:
            piv = (c1_, ax)
assert piv, "pivo nao encontrado"
I, pra, dra, pde, dde = cruzamento()
lat0 = math.degrees(math.asin(dra.z))
giro = None
for sinal in (1, -1):
    r = R(piv[1], sinal * (LAT - lat0))
    if abs(math.degrees(math.asin(r.multVec(dra).z)) - LAT) < 1e-6:
        giro = sinal * (LAT - lat0)
G_LAT = P(piv[0], R(piv[1], giro)).multiply(P(piv[0] * -1, R()))
move(todos + [A3], G_LAT)
I, pra, dra, pde, dde = cruzamento()
# o furo de trava do ACOPLADOR3 continua no arco da BASE?
ftrava = [V(g.Surface.Center) for g in fa]
ftrava = [G_LAT.multVec(p) for p in ftrava if (p - piv[0] - piv[1] * (p - piv[0]).dot(piv[1])).Length > 1]
rel("   latitude: %.2f -> %.2f graus (giro de %+.2f no pivo da BASE)" % (lat0, math.degrees(math.asin(dra.z)), giro))

# =============================================================== 9. BASE e tripe
sk7 = doc.getObject("Sketch007")
restr(sk7, 5.0, 5.25)
sk = esboco(BASE, "Furo_1_4_sk", P(V(0, 0, 8), R()))
sk.addGeometry(Part.Circle(V(0, 0, 0), V(0, 0, 1), 2.6))
pk = bolso(BASE, "Furo_1_4", sk, 8)
fil = doc.getObject("Fillet")
# o furo vai depois do arredondamento (para nao mexer nas arestas do Fillet)
BASE.Tip = pk
doc.recompute()
for f in BASE.Group:
    f.Visibility = (f == BASE.Tip)
sb = BASE.Shape.copy(); sb.Placement = P()
assert sb.isValid() and len(sb.Solids) == 1 and not sb.isInside(V(0, 0, 4), 0.01, True), "BASE"
TRIPE.Placement = P(TRIPE.Placement.Base, R(V(0, 0, 1), GIRO_TRIPE).multiply(TRIPE.Placement.Rotation))
rel("9. BASE: vao das bochechas 10,5 mm, furo Ø5,2 para rosca 1/4\"-20; tripe girado %.0f graus" % GIRO_TRIPE)

doc.recompute()
erros = [o.Label for o in doc.Objects if "Invalid" in o.State or "Error" in o.State]
assert not erros, erros

# =============================================================== salvar (+ GuiDocument da V2)
gui = None
with zipfile.ZipFile(ORIGEM) as z:
    if "GuiDocument.xml" in z.namelist():
        gui = z.read("GuiDocument.xml").decode("utf-8")
doc.saveAs(DESTINO)
if gui:
    nomes = {o.Name: o for o in doc.Objects}
    forcar = {}
    for b in (A1, A2, BASE):
        for f in b.Group:
            forcar[f.Name] = f.Visibility

    def troca(m):
        nome, corpo = m.group(1), m.group(2)
        if nome not in nomes:
            return ""
        if nome in forcar:
            corpo = re.sub(r'(<Property name="Visibility"[^>]*>\s*<Bool value=")(?:true|false)(")',
                           lambda k: k.group(1) + ("true" if forcar[nome] else "false") + k.group(2), corpo, count=1)
        return '<ViewProvider name="%s"%s</ViewProvider>' % (nome, corpo)

    txt = re.sub(r'<ViewProvider name="([^"]+)"((?:(?!</ViewProvider>).)*)</ViewProvider>', troca, gui, flags=re.S)
    txt = re.sub(r'(<ViewProviderData Count=")\d+(")', lambda m: m.group(1) + str(txt.count("<ViewProvider name=")) + m.group(2), txt)
    with zipfile.ZipFile(DESTINO) as z:
        tem = "GuiDocument.xml" in z.namelist()
    if not tem:
        with zipfile.ZipFile(DESTINO, "a", zipfile.ZIP_DEFLATED) as z:
            z.writestr("GuiDocument.xml", txt)
rel("salvo: %s" % DESTINO)

# =============================================================== STLs (orientacao de impressao)
os.makedirs(STL_DIR, exist_ok=True)
import Mesh  # noqa: E402


def stl(nome, s, qtd=1):
    s = s.copy()
    bb = s.BoundBox
    s.translate(V(-bb.Center.x, -bb.Center.y, -bb.ZMin))
    m = Mesh.Mesh(s.tessellate(0.05))
    m.write(os.path.join(STL_DIR, "%s_x%d.stl" % (nome, qtd)))


def local(o):
    s = o.Shape.copy(); s.Placement = P(); return s


stl("ACOPLADOR1", local(A1))
stl("ACOPLADOR2", local(A2))
stl("ACOPLADOR3", local(A3))
stl("BASE", local(BASE))
stl("SELA_DEC", sela)
stl("TAMPA_CW", tampa)
c_, t_, _, _ = copo_formas(0, 1)
stl("CONTRAPESO_COPO", c_)
t_.rotate(V(XE, 0, 41.5), V(1, 0, 0), 180)
stl("CONTRAPESO_TAMPA", t_)
rel("STLs em %s" % STL_DIR)
with open(os.path.join(D, "scripts", "revisao3_relatorio.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(relatorio) + "\n")
