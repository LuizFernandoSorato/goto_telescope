# Montagem equatorial alema (GEM) impressa para o Greika 70070 + redutores V2 (1024:1)
# Rodar com: "C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe" build_eq.py
# Variaveis de ambiente opcionais: LAT (graus, padrao 28.5), EXPORT=1 (gera STLs), CHECK=1 (interferencias)
import FreeCAD as App, Part, math, os

V = App.Vector; R = App.Rotation
def P(*a):
    if len(a) == 1 and isinstance(a[0], App.Vector):
        return App.Placement(a[0], App.Rotation())
    return App.Placement(*a)
BASEDIR = r"C:\LUIZ\PROJECTS\GOTO_TELESCOPE\FREECAD"
OUT = os.path.join(BASEDIR, "MONTAGEM_EQ")
GBX = os.path.join(BASEDIR, "REDUCAO_V2")
LAT = float(os.environ.get("LAT", "28.5"))
EXPORT = os.environ.get("EXPORT", "1") == "1"
CHECK = os.environ.get("CHECK", "1") == "1"

# ------------------------------------------------------------------ parametros (mm)
EIXO_D = 25.0          # tubo de aluminio dos eixos
EIXO_ID = 21.0         # parede de 2 mm (so para massa/visual)
FURO_EIXO = 25.1       # furo dos cubos de aperto
ROL_D, ROL_W = 37.15, 7.0   # alojamento do 6805-2RS (25x37x7)
CORPO_OD, CORPO_L = 52.0, 90.0
FLANGE_D, FLANGE_T, FURO_R = 92.0, 6.0, 42.0   # flange com 4x M4
EXT_ID, EXT_OD, EXT_L = 68.0, 80.0, 160.0
ZT = 22.0              # topo do prato da cunha
HP = ZT + 78.0         # altura do pivo de latitude
ZD = 152.0             # cota do eixo DEC ao longo do eixo AR
PIVO_L = V(0, 70, 88)  # pivo de latitude no corpo AR (coord. locais) - ao sul do CG: a roda fica sempre carregada
TRAVA_L = V(0, 60, 30) # parafuso de trava de latitude (arco na cunha)
APOIO_L = V(0, 80, 0)  # quina inferior-norte da quilha: apoia na roda de ajuste
GB_OFF = -100.0        # redutor: z_redutor -> z_eixo
OTA_KG = 1.5
OTA_TUBO_D = 80.0
BARRA_L = 200.0        # barra M12 do contrapeso (comprimento livre)
M12_KG_M = 0.66        # kg por metro de barra roscada M12

def cyl(r, h, p=(0, 0, 0), d=(0, 0, 1)):
    return Part.makeCylinder(r, h, V(*p), V(*d))

def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))

def prism_xy(pts, z0, h):
    w = Part.makePolygon([V(x, y, z0) for x, y in pts] + [V(pts[0][0], pts[0][1], z0)])
    return Part.Face(w).extrude(V(0, 0, h))

def prism_yz(pts, x0, dx):
    w = Part.makePolygon([V(x0, y, z) for y, z in pts] + [V(x0, pts[0][0], pts[0][1])])
    return Part.Face(w).extrude(V(dx, 0, 0))

def hexagon(af, h, rot=0.0):
    rc = af / math.sqrt(3)
    pts = [(rc * math.cos(math.radians(rot + 60 * k)), rc * math.sin(math.radians(rot + 60 * k))) for k in range(6)]
    return prism_xy(pts, 0, h)

def moved(shape, plc):
    s = shape.copy()
    s.Placement = plc.multiply(s.Placement)
    return s

def along(shape, origin, direction):
    """reposiciona um solido construido ao longo de +Z para um eixo qualquer"""
    rot = R(V(0, 0, 1), V(*direction))
    return moved(shape, P(V(*origin), rot))

def fuse(*shapes):
    s = shapes[0]
    for t in shapes[1:]:
        s = s.fuse(t)
    return s.removeSplitter()

def cut(s, *tools):
    for t in tools:
        s = s.cut(t)
    return s.removeSplitter()

def octagon_pts(half=21.0, ch=6.0):
    c = ch / math.sqrt(2); a = half - c
    return [(-a, -half), (a, -half), (half, -a), (half, a), (a, half), (-a, half), (-half, a), (-half, -a)]

def hull2d(pts):
    pts = sorted(set(pts))
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]

def flange_holes(z0=0.0, h=FLANGE_T, r=FURO_R, d=4.4):
    return [cyl(d / 2, h, (r * math.cos(math.radians(45 + 90 * k)), r * math.sin(math.radians(45 + 90 * k)), z0)) for k in range(4)]

# ------------------------------------------------------------------ transformacoes de montagem
def M_RA(lat):
    rot = R(V(1, 0, 0), -(90.0 - lat))
    t = V(0, 0, HP) - rot.multVec(PIVO_L)
    return P(t, rot)

ROT_X180 = R(V(1, 0, 0), 180)
P_D = P(V(0, 45, ZD), R(App.Matrix(1, 0, 0, 0, 0, 0, -1, 0, 0, 1, 0, 0, 0, 0, 0, 1)))   # quadro DEC -> quadro AR
P_CUBO = P(V(0, 0, -1), ROT_X180)      # cubo de acoplamento no lado do redutor
P_EXT = P(V(0, 0, 0), ROT_X180)        # extensao (carcaca do redutor)
P_CAP = P_EXT.multiply(P(V(0, 0, EXT_L - 5)))
P_GB = P(V(0, 0, GB_OFF))
P_COLAR = P_GB.multiply(P(V(0, 0, 20)))

# ================================================================== PECAS (cada uma no seu quadro de impressao)
parts = {}

# ---------------- BASE (vai no tripe, porca 1/4" presa por baixo)
# ajuste de azimute no lado NORTE (o lado sul fica livre para a carcaca DEC passar no estacionamento)
AY = M_RA(LAT).multVec(APOIO_L).y          # o bloco da roda de latitude serve de aba para os parafusos
b = fuse(cyl(55, 12), box(-34, 34, AY - 8, -40, 0, 12), box(-34, -20, AY - 8, AY + 8, 12, 32), box(20, 34, AY - 8, AY + 8, 12, 32), cyl(20, 6, (0, 0, 12)))
b = cut(b, hexagon(11.3, 6.5), cyl(3.3, 40))
b = cut(b, along(cyl(2.6, 80), (-40, AY, 24), (1, 0, 0)))
for sx in (-1, 1):
    b = cut(b, moved(along(hexagon(8.2, 4.4, 30), (0, 0, 0), (1, 0, 0)), P(V(sx * 34 - (4.4 if sx > 0 else 0), AY, 24), R())))
    b = cut(b, cyl(2.7, 12, (sx * 40, 0, 0)), moved(hexagon(8.2, 4.5), P(V(sx * 40, 0, 0), R())))
parts["BASE"] = dict(shape=b, plc=P(), grp="S", print=P(), qty=1)

# ---------------- CUNHA (prato giratorio + bochechas do pivo de latitude)
def cunha(lat):
    m = M_RA(lat)
    piv = V(0, 0, HP)
    trava = [m.multVec(TRAVA_L)]
    # arco de trava: amostras de latitude
    amostras = [lat + d for d in range(-12, 13, 1)]
    pts_trava = [M_RA(a).multVec(TRAVA_L) for a in amostras]
    pts = []
    for k in range(36):
        a = math.radians(10 * k)
        pts.append((piv.y + 14 * math.cos(a), piv.z + 14 * math.sin(a)))
        for q in pts_trava[::4] + [pts_trava[-1]]:
            pts.append((q.y + 10 * math.cos(a), q.z + 10 * math.sin(a)))
    ymin = min(p[0] for p in pts); ymax = max(p[0] for p in pts)
    pts += [(ymin, ZT - 1), (ymax, ZT - 1)]
    pts = [(y, max(z, ZT - 1)) for y, z in pts]
    poly = hull2d(pts)
    bochecha = fuse(prism_yz(poly, 10.5, 8), prism_yz(poly, -18.5, 8))
    # folgas para o corpo AR girar em toda a faixa de latitude
    folga = fuse(cyl(29, 86, (0, 0, 6)), cyl(48, 15, (0, 0, -8)), cyl(42, 180, (0, 0, -174)))
    for a in amostras[::2]:
        bochecha = bochecha.cut(moved(folga, M_RA(a)))
    c = fuse(cyl(55, 10, (0, 0, 12)), bochecha)
    c = cut(c, cyl(20.3, 6.5, (0, 0, 12)))
    for ang0 in (0, 180):
        for d in range(-10, 11, 1):
            a = math.radians(ang0 + d)
            c = c.cut(cyl(2.75, 12, (40 * math.cos(a), 40 * math.sin(a), 11)))
    c = cut(c, along(cyl(4.15, 60), (-30, 0, HP), (1, 0, 0)))
    for q in pts_trava:
        c = c.cut(along(cyl(3.2, 60), (-30, q.y, q.z), (1, 0, 0)))
    # bloco da roda de ajuste fino de latitude
    ap = m.multVec(APOIO_L)
    bloco = box(-8, 8, ap.y - 10, ap.y + 10, ZT - 1, ZT + 12)
    bloco = cut(bloco, cyl(3.25, 10, (0, ap.y, ZT + 3)), box(-5.9, 9, ap.y - 5.1, ap.y + 5.1, ZT + 5, ZT + 10.4))
    c = fuse(c, bloco)
    return c.removeSplitter(), ap

cun, apoio = cunha(LAT)
parts["CUNHA"] = dict(shape=cun, plc=P(), grp="S", print=P(V(0, 0, -12), R()), qty=1)

# ---------------- RODA de ajuste fino de latitude (porca M6 presa)
rd = cyl(9.8, 8)                      # cabe entre as bochechas da cunha (x = +-10,5)
for k in range(16):
    a = math.radians(22.5 * k)
    rd = rd.cut(cyl(1.0, 8, (10.3 * math.cos(a), 10.3 * math.sin(a), 0)))
rd = cut(rd, cyl(3.3, 8), hexagon(10.2, 5.2))
parts["RODA_LAT"] = dict(shape=rd, plc=P(V(0, apoio.y, apoio.z - 8), R()), grp="S", print=P(), qty=1)

# ---------------- CORPO_AR (2x 6805 + quilha do pivo)
c = fuse(cyl(CORPO_OD / 2, CORPO_L), cyl(FLANGE_D / 2, FLANGE_T), box(-10, 10, 0, 80, 0, 90), box(-10, 10, 24, 80, 90, 98))
c = cut(c, cyl(ROL_D / 2, ROL_W), cyl(ROL_D / 2, ROL_W, (0, 0, CORPO_L - ROL_W)), cyl(15, CORPO_L), *flange_holes())
c = cut(c, along(cyl(4.15, 30), (-15, PIVO_L.y, PIVO_L.z), (1, 0, 0)), along(cyl(3.2, 30), (-15, TRAVA_L.y, TRAVA_L.z), (1, 0, 0)))
parts["CORPO_AR"] = dict(shape=c, plc=P(), grp="SA", print=P(), qty=1)

# ---------------- CORPO_DEC (2x 6805 + cubo de aperto no eixo AR)
c = fuse(cyl(CORPO_OD / 2, CORPO_L), cyl(FLANGE_D / 2, FLANGE_T))
boss_end = -(ZD - (CORPO_L + 1))           # x onde o cubo termina (1 mm acima do corpo AR)
c = fuse(c, along(cyl(22, -boss_end - 20), (-20, 0, 45), (-1, 0, 0)))
c = fuse(c, along(cyl(14.5, 1).cut(cyl(12.6, 1)), (boss_end, 0, 45), (-1, 0, 0)))
c = cut(c, cyl(ROL_D / 2, ROL_W), cyl(ROL_D / 2, ROL_W, (0, 0, CORPO_L - ROL_W)), cyl(15, CORPO_L), *flange_holes())
c = cut(c, along(cyl(FURO_EIXO / 2, -boss_end - 28 + 1), (-28, 0, 45), (-1, 0, 0)))
c = cut(c, box(boss_end - 1, -30, 0, 23, 44.25, 45.75))
for x in (-40, -54):
    c = cut(c, cyl(2.75, 50, (x, 16, 20)), cyl(4.75, 8, (x, 16, 53)), moved(hexagon(8.2, 6.5), P(V(x, 16, 29), R())))
parts["CORPO_DEC"] = dict(shape=c, plc=P(V(0, 0, 0), R(V(0, 0, 1), 90)), grp="RD", print=P(), qty=1)

# ---------------- EXT (carcaca que envolve redutor + motor; canal do braco anti-giro)
e = fuse(cyl(EXT_OD / 2, EXT_L), cyl(FLANGE_D / 2, FLANGE_T))
e = cut(e, cyl(EXT_ID / 2, EXT_L), *flange_holes())
e = cut(e, box(EXT_ID / 2 - 1, EXT_ID / 2 + 2.6, -4.3, 4.3, 60, EXT_L))
e = cut(e, along(cyl(1.25, 20), (35.2, 0, 77), (0, 1, 0)))                 # parafuso M3 de ajuste do braco
for a in (60, 180, 300):
    e = e.cut(along(cyl(1.7, 10), (34 * math.cos(math.radians(a)), 34 * math.sin(math.radians(a)), EXT_L - 2.5), (math.cos(math.radians(a)), math.sin(math.radians(a)), 0)))
parts["EXT_AR"] = dict(shape=e, plc=P_EXT, grp="SA", print=P(), qty=2, stl="EXT")
parts["EXT_DEC"] = dict(shape=e, plc=P_EXT, grp="RD", print=None, qty=0)

# ---------------- TAMPA_EXT (fecha a extensao; porca M12 da barra de contrapeso)
t = fuse(cyl(EXT_ID / 2 - 0.1, 5), Part.makeCone(EXT_ID / 2 - 0.1, EXT_OD / 2, 6.1, V(0, 0, 5)), cyl(EXT_OD / 2, 3, (0, 0, 11.1)), cyl(16, 14, (0, 0, 14.1)))
t = cut(t, cyl(6.25, 40), moved(hexagon(19.3, 10.5), P(V(0, 0, 17.6), R())), cyl(6, 20, (-24, 0, 0)))
for a in (60, 180, 300):
    t = t.cut(along(cyl(1.25, 10), (25 * math.cos(math.radians(a)), 25 * math.sin(math.radians(a)), 2.5), (math.cos(math.radians(a)), math.sin(math.radians(a)), 0)))
parts["TAMPA_EXT_AR"] = dict(shape=t, plc=P_CAP, grp="SA", print=P(), qty=2, stl="TAMPA_EXT")
parts["TAMPA_EXT_DEC"] = dict(shape=t, plc=P_CAP, grp="RD", print=None, qty=0)

# ---------------- CUBO de acoplamento (sextavado da saida do redutor + eixo 25)
h = fuse(cyl(22, 30), cyl(14.5, 1, (0, 0, -1)).cut(cyl(12.6, 1, (0, 0, -1))))
h = cut(h, cyl(FURO_EIXO / 2, 21, (0, 0, -1)), moved(hexagon(8.8, 8, 90), P(V(0, 0, 22), R())), cyl(2, 3, (0, 0, 20)))
h = cut(h, box(0, 23, -0.75, 0.75, -1, 30))
for z, dd, cb, af, x in ((6, 4.4, 8.0, 7.1, 17), (14, 4.4, 8.0, 7.1, 17), (26, 3.4, 6.5, 5.6, 11)):
    ext = math.sqrt(22 ** 2 - x ** 2)
    h = cut(h, along(cyl(dd / 2, 2 * ext + 2), (x, -ext - 1, z), (0, 1, 0)), along(cyl(cb / 2, ext - 6), (x, -ext - 1, z), (0, 1, 0)),
            moved(along(hexagon(af, ext - 6, 30), (0, 0, 0), (0, 1, 0)), P(V(x, 7, z), R())))
parts["CUBO_AR"] = dict(shape=h, plc=P_CUBO, grp="RA", print=P(V(0, 0, 30), ROT_X180), qty=2, stl="CUBO")
parts["CUBO_DEC"] = dict(shape=h, plc=P_CUBO, grp="D", print=None, qty=0)

# ---------------- COLAR do braco anti-giro (abraca a CAIXA octogonal do redutor)
oct_in = prism_xy(octagon_pts(21.15, 6.0), 0, 6)
co = fuse(cyl(31, 6), box(0, 35.5, -4, 4, 0, 6))
co = cut(co, oct_in, box(-33, -20, -0.75, 0.75, 0, 6))
co = cut(co, along(cyl(1.7, 30), (-27, -15, 3), (0, 1, 0)), moved(along(hexagon(5.6, 4, 30), (0, 0, 0), (0, 1, 0)), P(V(-27, 6, 3), R())))
parts["COLAR_AR"] = dict(shape=co, plc=P_COLAR, grp="SA", print=P(), qty=2, stl="COLAR_BRACO")
parts["COLAR_DEC"] = dict(shape=co, plc=P_COLAR, grp="RD", print=None, qty=0)

# ---------------- SELA (cubo + placa Vixen)
sc = fuse(cyl(22, 30), cyl(35, 6, (0, 0, 30)), cyl(14.5, 1, (0, 0, -1)).cut(cyl(12.6, 1, (0, 0, -1))))
sc = cut(sc, cyl(FURO_EIXO / 2, 26, (0, 0, -1)), box(0, 23, -0.75, 0.75, -1, 28))
for z in (6, 16):
    ext = math.sqrt(22 ** 2 - 17 ** 2)
    sc = cut(sc, along(cyl(2.2, 2 * ext + 2), (17, -ext - 1, z), (0, 1, 0)), along(cyl(4, ext - 6), (17, -ext - 1, z), (0, 1, 0)),
             moved(along(hexagon(7.1, ext - 6, 30), (0, 0, 0), (0, 1, 0)), P(V(17, 7, z), R())))
for k in range(4):
    a = math.radians(45 + 90 * k)
    sc = sc.cut(cyl(2.2, 6, (27 * math.cos(a), 27 * math.sin(a), 30)))
parts["SELA_CUBO"] = dict(shape=sc, plc=P(V(0, 0, CORPO_L + 1)), grp="D", print=P(V(0, 0, 36), ROT_X180), qty=1)

GB = 44.6; ANG = math.radians(75); HJ = 12.0
sp = fuse(box(-35, 35, -55, 55, 0, 10),
          prism_yz([(-55, 10), (55, 10), (55, 10 + HJ), (-55, 10 + HJ)], -35, 35 - 26),  # placeholder, substituido abaixo
          )
sp = box(-35, 35, -55, 55, 0, 10)
xa = -GB / 2; xb = xa + HJ / math.tan(ANG)
jaw_fixa = Part.Face(Part.makePolygon([V(-35, -55, 10), V(xa, -55, 10), V(xb, -55, 10 + HJ), V(-35, -55, 10 + HJ), V(-35, -55, 10)])).extrude(V(0, 110, 0))
jaw_aperto = box(26, 35, -55, 55, 10, 10 + HJ)
sp = fuse(sp, jaw_fixa, jaw_aperto)
for y in (-30, 30):
    sp = cut(sp, along(cyl(3.25, 14), (23, y, 16), (1, 0, 0)), moved(along(hexagon(10.2, 5.5, 30), (0, 0, 0), (1, 0, 0)), P(V(29.5, y, 16), R())))
for k in range(4):
    a = math.radians(45 + 90 * k)
    x, y = 27 * math.cos(a), 27 * math.sin(a)
    sp = cut(sp, cyl(2.2, 10, (x, y, 0)), moved(hexagon(7.1, 3.5), P(V(x, y, 6.5), R())))
parts["SELA_PLACA"] = dict(shape=sp, plc=P(V(0, 0, CORPO_L + 1 + 36)), grp="D", print=P(), qty=1)

# ---------------- BUCHA do contrapeso (anilha furo 25 mm -> barra M12)
bu = cut(fuse(cyl(12.4, 8), cyl(18, 3, (0, 0, 8))), cyl(6.3, 12))
parts["BUCHA_CW"] = dict(shape=bu, plc=None, grp=None, print=P(), qty=2)

# ---------------- itens comprados / referencia (nao imprimir)
tubo = lambda L: cyl(EIXO_D / 2, L).cut(cyl(EIXO_ID / 2, L))
rol = cyl(18.5, 7).cut(cyl(12.5, 7))
ref = {}
ref["EIXO_AR"] = (moved(tubo(ZD - 29 + 20.5), P(V(0, 0, -20.5))), "RA")
ref["EIXO_DEC"] = (moved(tubo(115 + 20.5), P(V(0, 0, -20.5))), "D")
ref["ROL_AR_1"] = (rol.copy(), "SA"); ref["ROL_AR_2"] = (moved(rol, P(V(0, 0, 83))), "SA")
ref["ROL_DEC_1"] = (rol.copy(), "RD"); ref["ROL_DEC_2"] = (moved(rol, P(V(0, 0, 83))), "RD")
ref["BARRA_M12"] = (cyl(6, BARRA_L + 15, (0, 0, -EXT_L - 10), (0, 0, -1)), "RD")
trilho = Part.Face(Part.makePolygon([V(-22, -100, 0), V(22, -100, 0), V(22 - 12 / math.tan(ANG), -100, 12), V(-22 + 12 / math.tan(ANG), -100, 12), V(-22, -100, 0)])).extrude(V(0, 200, 0))
ota_z = CORPO_L + 1 + 36 + 10
ref["OTA_TRILHO"] = (moved(trilho, P(V(0, 0, ota_z))), "D")
ref["OTA_TUBO"] = (cyl(OTA_TUBO_D / 2, 700, (0, -350, ota_z + 12 + 15 + OTA_TUBO_D / 2), (0, 1, 0)), "D")

# redutores (copia de MONTAGEM_V2)
gdoc_p = App.openDocument(os.path.join(GBX, "REDUCAO_V2.FCStd"), True)
gdoc = App.openDocument(os.path.join(GBX, "MONTAGEM_V2.FCStd"), True)
gdoc.recompute()
env, inner, saida = [], [], None
gb_vol = 0.0
for o in gdoc.Objects:
    if o.TypeId not in ("App::Link", "Part::Feature"):
        continue
    s = Part.getShape(o)
    if o.Name == "SAIDA":
        saida = s
    elif o.Name in ("CAIXA", "TAMPA", "NEMA17_referencia"):
        env.append(s)
    else:
        inner.append(s)
    if o.Name != "NEMA17_referencia":
        gb_vol += s.Volume
gb_env = Part.makeCompound(env); gb_inner = Part.makeCompound(inner)
App.closeDocument(gdoc.Name); App.closeDocument(gdoc_p.Name)
for tag, g_s, g_r in (("AR", "SA", "RA"), ("DEC", "RD", "D")):
    ref["REDUTOR_%s" % tag] = (moved(gb_env, P_GB), g_s)
    ref["REDUTOR_%s_interno" % tag] = (moved(gb_inner, P_GB), g_s)
    ref["REDUTOR_%s_saida" % tag] = (moved(saida, P_GB), g_r)

# ================================================================== montagem
def group_plc(grp, lat, a_ra=0.0, a_dec=0.0):
    m = M_RA(lat)
    if grp in ("S",):
        return P()
    if grp == "SA":
        return m
    mr = m.multiply(P(V(), R(V(0, 0, 1), a_ra)))
    if grp == "RA":
        return mr
    md = mr.multiply(P_D)
    if grp == "RD":
        return md
    if grp == "D":
        return md.multiply(P(V(), R(V(0, 0, 1), a_dec)))

def world(name, lat=LAT, a_ra=0.0, a_dec=0.0):
    if name in parts:
        d = parts[name]
        return moved(d["shape"], group_plc(d["grp"], lat, a_ra, a_dec).multiply(d["plc"]))
    s, g = ref[name]
    return moved(s, group_plc(g, lat, a_ra, a_dec))

def grp_of(name):
    return parts[name]["grp"] if name in parts else ref[name][1]

names = [n for n in parts if parts[n]["grp"]] + list(ref)

# ------------------------------------------------------------------ massas e balanceamento (AR)
RHO_PETG = 1.27e-3          # g/mm3
FATOR = 0.6                 # 4 paredes + 40% gyroid (estimativa)
massa = {}
for n in names:
    if n in parts:
        massa[n] = parts[n]["shape"].Volume * RHO_PETG * FATOR / 1000
massa["EIXO_AR"] = ref["EIXO_AR"][0].Volume * 2.7e-3 / 1000
massa["EIXO_DEC"] = ref["EIXO_DEC"][0].Volume * 2.7e-3 / 1000
for n in ("ROL_AR_1", "ROL_AR_2", "ROL_DEC_1", "ROL_DEC_2"):
    massa[n] = 0.022
massa["BARRA_M12"] = (BARRA_L + 15) / 1000 * M12_KG_M
massa["OTA_TUBO"] = OTA_KG
massa["OTA_TRILHO"] = ref["OTA_TRILHO"][0].Volume * RHO_PETG * FATOR / 1000
for tag in ("AR", "DEC"):
    massa["REDUTOR_%s" % tag] = 0.35 + gb_vol * RHO_PETG * 0.8 / 1000   # motor + redutor impresso
    massa["REDUTOR_%s_interno" % tag] = 0.0
    massa["REDUTOR_%s_saida" % tag] = 0.0

m_ra = M_RA(LAT)
mom = 0.0; mtot_gira = 0.0
for n in names:
    if grp_of(n) in ("RA", "RD", "D") and massa.get(n, 0) > 0:
        s = world(n)
        loc = m_ra.inverse().multVec(s.CenterOfMass if hasattr(s, "CenterOfMass") and s.ShapeType == "Solid" else s.BoundBox.Center)
        if s.ShapeType != "Solid" and s.Solids:
            vol = sum(x.Volume for x in s.Solids)
            c = V(0, 0, 0)
            for x in s.Solids:
                c = c + x.CenterOfMass * (x.Volume / vol)
            loc = m_ra.inverse().multVec(c)
        if n == "OTA_TUBO":
            loc = m_ra.inverse().multVec(world(n).BoundBox.Center)
        mom += massa[n] * (-loc.y)
        mtot_gira += massa[n]
# braco do contrapeso: distancia ao eixo AR ao longo do eixo DEC (lado oposto ao telescopio)
ota_dist = 45 - (ota_z + 12 + 15 + OTA_TUBO_D / 2)            # y_AR do centro do tubo (negativo = lado do tubo)
barra_ini = 45 + EXT_L + 10 + 14 + 2      # face livre da tampa (onde a anilha pode encostar)
barra_fim = 45 + EXT_L + 10 + BARRA_L
cw_info = []
for carga in (1.5, 2.0, 2.5, 3.0):
    m_need = mom + (carga - OTA_KG) * (-ota_dist)
    cw_info.append((carga, m_need, m_need / (barra_fim - 10), m_need / (barra_ini + 10)))
cw_m, cw_esp = 0.5, 8.0
cw_d = max(mom / cw_m, barra_ini + cw_esp / 2)
cw = cyl(55, cw_esp).cut(cyl(12.5, cw_esp))
# anilha de 0,5 kg no quadro DEC (z_D = 45 - y_AR)
ref["CONTRAPESO"] = (moved(cw, P(V(0, 0, 45 - cw_d - cw_esp / 2))), "RD")
massa["CONTRAPESO"] = cw_m
names.append("CONTRAPESO")

# ------------------------------------------------------------------ documento
doc = App.newDocument("MONTAGEM_EQ")
grupos = {}
rot_nome = {"S": "Fixo_tripe", "SA": "Fixo_corpo_AR", "RA": "Gira_AR", "RD": "Gira_AR_corpo_DEC", "D": "Gira_DEC"}
for g, nm in rot_nome.items():
    grupos[g] = doc.addObject("App::DocumentObjectGroup", nm)
gref = doc.addObject("App::DocumentObjectGroup", "Referencia_comprados")
for n in names:
    o = doc.addObject("Part::Feature", n)
    o.Shape = world(n)
    (grupos[grp_of(n)] if n in parts else gref).addObject(o)
doc.recompute()
os.makedirs(OUT, exist_ok=True)
doc.saveAs(os.path.join(OUT, "MONTAGEM_EQ.FCStd"))

# ------------------------------------------------------------------ relatorio
print("LAT=%.1f  pivo a %.0f mm do topo do tripe" % (LAT, HP))
print("Massa girando no eixo AR: %.2f kg (sem contrapeso)" % mtot_gira)
print("Momento a equilibrar (tubo %.1f kg, barra %.0f mm incluida): %.0f kg.mm" % (OTA_KG, BARRA_L, mom))
print("Contrapeso necessario (anilha na ponta da barra .. encostada na tampa):")
for carga, m_need, m_min, m_max in cw_info:
    print("  carga %.1f kg: momento %3.0f kg.mm -> contrapeso %.2f .. %.2f kg" % (carga, m_need, m_min, m_max))
# centro de gravidade de tudo que apoia no pivo de latitude (com anilha de 1 kg balanceada)
cg = V(0, 0, 0); mt = 0.0
for n in names:
    if grp_of(n) != "S" and massa.get(n, 0) > 0:
        s_ = world(n)
        c = s_.BoundBox.Center if n == "OTA_TUBO" else (s_.CenterOfMass if s_.ShapeType == "Solid" else sum((x.CenterOfMass * (x.Volume / s_.Volume) for x in s_.Solids), V()))
        cg = cg + c * massa[n]; mt += massa[n]
cg = cg * (1.0 / mt)
print("CG sobre o pivo: %.2f kg, %.1f mm %s do pivo (roda de latitude %s)" % (mt, abs(cg.y), "ao NORTE" if cg.y < 0 else "ao SUL",
      "carregada - OK" if cg.y < 0 else "ALIVIADA: depende do aperto das travas"))
for n in sorted(massa):
    if massa[n] > 0:
        print("   massa %-20s %.3f kg" % (n, massa[n]))
# faixa de latitude da roda de ajuste
for d in (-12, -6, 0, 6, 12):
    ap = M_RA(LAT + d).multVec(APOIO_L)
    print("lat %.1f: apoio da roda em z=%.1f (bloco ate %.1f; roda 8 mm) %s" % (LAT + d, ap.z, ZT + 12, "OK" if ap.z - 8 >= ZT + 12 else "fora da faixa"))

if CHECK:
    def inter(a, b):
        if not a.BoundBox.intersect(b.BoundBox):
            return 0.0
        try:
            return a.common(b).Volume
        except Exception:
            return -1.0
    skip_int = lambda n: n.endswith("_interno") or n.startswith("OTA") or n == "CONTRAPESO"
    chk = [n for n in names if not skip_int(n)]
    print("\n== interferencias dentro de cada conjunto (posicao inicial)")
    shp = {n: world(n) for n in names}
    found = 0
    for i in range(len(chk)):
        for j in range(i + 1, len(chk)):
            a, b = chk[i], chk[j]
            if grp_of(a) == grp_of(b) or {grp_of(a), grp_of(b)} in ({"S", "SA"}, {"RA", "RD"}):
                v = inter(shp[a], shp[b])
                if abs(v) > 0.01:
                    found += 1
                    print("   %-18s x %-18s %.3f mm3" % (a, b, v))
    print("   total:", found)
    print("\n== interferencias entre partes moveis (AR -120..+120 a cada 30 graus; DEC 0/90/180/270)")
    fixos = [n for n in names if grp_of(n) in ("S", "SA") and not skip_int(n)]
    gira_ar = [n for n in names if grp_of(n) in ("RA", "RD") and not (n.endswith("_interno"))]
    gira_dec = [n for n in names if grp_of(n) == "D" and not n.endswith("_interno")]
    fixos_s = {n: world(n) for n in fixos}
    found = 0
    for a_ra in range(-120, 121, 30):
        for a_dec in (0, 90, 180, 270):
            ga = {n: world(n, a_ra=a_ra, a_dec=a_dec) for n in gira_ar} if a_dec == 0 else ga
            gd = {n: world(n, a_ra=a_ra, a_dec=a_dec) for n in gira_dec}
            pares = []
            if a_dec == 0:
                pares += [(f, g, fixos_s[f], ga[g]) for f in fixos for g in gira_ar]
            pares += [(f, g, fixos_s[f], gd[g]) for f in fixos for g in gd]
            pares += [(f, g, ga[f], gd[g]) for f in gira_ar for g in gd]
            for f, g, sa, sb in pares:
                if {f, g} & {"REDUTOR_AR_saida", "CUBO_AR"} == {"REDUTOR_AR_saida", "CUBO_AR"}:
                    continue
                if {f, g} == {"REDUTOR_DEC_saida", "CUBO_DEC"}:
                    continue
                v = inter(sa, sb)
                if abs(v) > 0.01:
                    found += 1
                    print("   AR=%3d DEC=%3d  %-18s x %-18s %.2f mm3" % (a_ra, a_dec, f, g, v))
    print("   total:", found)
    print("\n== telescopio (referencia) vs partes fixas")
    for a_ra in range(0, 360, 45):
        for a_dec in range(0, 360, 45):
            ota = world("OTA_TUBO", a_ra=a_ra, a_dec=a_dec)
            hit = [f for f in fixos if inter(fixos_s[f], ota) > 0.01]
            if hit:
                print("   AR=%3d DEC=%3d  tubo toca: %s" % (a_ra, a_dec, ", ".join(hit)))
    print("   (fim)")

    print("\n== faixa de latitude: corpo AR vs cunha")
    for d in (-12, -6, 6, 12):
        cun_s = shp["CUNHA"]
        hits = []
        for n in ("CORPO_AR", "EXT_AR", "TAMPA_EXT_AR", "REDUTOR_AR"):
            v = inter(cun_s, world(n, lat=LAT + d))
            if v > 0.01:
                hits.append("%s %.1f" % (n, v))
        print("   lat %.1f: %s" % (LAT + d, ", ".join(hits) if hits else "livre"))

if EXPORT:
    import MeshPart
    sd = os.path.join(OUT, "STL"); os.makedirs(sd, exist_ok=True)
    for n, d in parts.items():
        if d.get("print") is None:
            continue
        s = moved(d["shape"], d["print"])
        bb = s.BoundBox
        s = moved(s, P(V(-bb.Center.x, -bb.Center.y, -bb.ZMin), R()))
        msh = MeshPart.meshFromShape(Shape=s, LinearDeflection=0.02, AngularDeflection=0.0872665, Relative=False)
        fn = os.path.join(sd, "%s_x%d.stl" % (d.get("stl", n), d["qty"]))
        msh.write(fn)
        print("STL", os.path.basename(fn), "vol=%.0f cm3" % (s.Volume / 1000), "valido=%s" % s.isValid())
