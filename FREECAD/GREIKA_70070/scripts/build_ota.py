# Modelo APROXIMADO do tubo optico (OTA) Greika 70070 - refrator 70 mm / f 700 mm
# Medidas estimadas pela foto e por refratores 70/700 do mesmo projeto: confira com paquimetro e ajuste os parametros.
# Rodar com: "C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe" build_ota.py
# Variaveis de ambiente opcionais: PREVIEW=caminho.png (gera uma imagem de conferencia)
#
# Sistema de coordenadas (o mesmo do OTA_TUBO em MONTAGEM_EQ/build_eq.py):
#   Y = eixo optico, +Y aponta para a objetiva (frente)
#   Z = para cima; Z=0 e a face de baixo da sapata de fixacao
#   origem = ponto medio entre os 2 furos da sapata
import FreeCAD as App, Part, math, os

V = App.Vector
BASEDIR = r"C:\LUIZ\PROJECTS\GOTO_TELESCOPE\FREECAD\GREIKA_70070"
PREVIEW = os.environ.get("PREVIEW", "")

# ------------------------------------------------------------------ parametros (mm) - TODOS ESTIMADOS
TUBO_D, TUBO_PAREDE = 76.0, 1.2     # tubo principal (aluminio)
TUBO_L = 560.0                      # da celula traseira ate a celula da objetiva
CEL_D = 80.0                        # celulas traseira e da objetiva (plastico)
CEL_TRAS_L, CEL_FRENTE_L = 22.0, 28.0
PARASOL_D, PARASOL_PAREDE = 88.0, 1.5
PARASOL_L = 150.0                   # para-sol (encaixa 22 mm sobre a celula da objetiva)
OBJ_D, OBJ_E = 70.0, 10.0           # objetiva (dupla acromatica)
SAPATA_DE_TRAS = 270.0              # centro da sapata medido a partir do fim do tubo (lado do focalizador)
SAPATA_L, SAPATA_W = 90.0, 40.0     # bloco de fixacao sob o tubo
SAPATA_H = 12.0                     # da face de baixo ate o tubo
ANEL_L, ANEL_E = 50.0, 5.0          # abracadeira em volta do tubo
FURO_DIST = 60.0                    # distancia entre os 2 furos da sapata  <-- MEDIR
FURO_D, FURO_P = 5.0, 12.0          # furo para rosca M6 (ou 1/4"-20: 5,1 mm)
FOC_D, FOC_L = 46.0, 45.0           # corpo do focalizador
FOC_TUBO_OD, FOC_TUBO_ID = 36.0, 31.9   # tubo de foco (ocular/diagonal de 1,25")
FOC_CURSO = 40.0                    # quanto o tubo de foco esta para fora do corpo
KNOB_D, KNOB_L = 28.0, 12.0         # manoplas de foco (embaixo do focalizador)
DIAG_CUBO = 38.0                    # corpo da diagonal 90 graus
DIAG_ANG = 0.0                      # giro da diagonal em volta do eixo optico (0 = ocular para cima)
OCULAR_D, OCULAR_L = 36.0, 50.0
BUSCADOR_DE_TRAS = 70.0             # buscador red dot: centro medido a partir do fim do tubo

# massas estimadas (kg) - total ~1,5 kg (valor usado em MONTAGEM_EQ)
MASSA = dict(TUBO=0.42, CELULA_TRASEIRA=0.05, CELULA_OBJETIVA=0.08, OBJETIVA=0.17, PARASOL=0.12,
             SAPATA=0.09, FOCALIZADOR=0.28, TUBO_FOCO=0.06, DIAGONAL=0.10, OCULAR=0.08, BUSCADOR=0.05)

# ------------------------------------------------------------------ geometria
def cylY(r, y0, y1, x=0.0, z=0.0):
    """cilindro ao longo de Y, de y0 a y1"""
    return Part.makeCylinder(r, y1 - y0, V(x, y0, z), V(0, 1, 0))

def tuboY(ro, ri, y0, y1, z):
    return cylY(ro, y0, y1, z=z).cut(cylY(ri, y0, y1, z=z))

def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))

def fuse(*s):
    r = s[0]
    for t in s[1:]:
        r = r.fuse(t)
    return r.removeSplitter()

ZA = SAPATA_H + TUBO_D / 2                      # altura do eixo optico
Y_TRAS = -SAPATA_DE_TRAS                        # fim do tubo (lado do focalizador)
Y_FRENTE = Y_TRAS + TUBO_L                      # inicio da celula da objetiva
R = TUBO_D / 2
parts = {}

parts["TUBO"] = tuboY(R, R - TUBO_PAREDE, Y_TRAS, Y_FRENTE, ZA)

# celula traseira: abraca o tubo e fecha com um disco furado para o focalizador
ct = fuse(tuboY(CEL_D / 2, R, Y_TRAS, Y_TRAS + CEL_TRAS_L - 6, ZA),
          cylY(CEL_D / 2, Y_TRAS - 6, Y_TRAS, z=ZA))
parts["CELULA_TRASEIRA"] = ct.cut(cylY(FOC_TUBO_OD / 2 + 1, Y_TRAS - 7, Y_TRAS + 1, z=ZA))

# celula da objetiva
y_cf = Y_FRENTE - 6
cf = fuse(tuboY(CEL_D / 2, R, y_cf, Y_FRENTE, ZA),
          tuboY(CEL_D / 2, OBJ_D / 2 - 3, Y_FRENTE, Y_FRENTE + CEL_FRENTE_L, ZA))
cf = cf.cut(cylY(OBJ_D / 2 + 0.5, Y_FRENTE + 6, Y_FRENTE + 6 + OBJ_E, z=ZA))
parts["CELULA_OBJETIVA"] = cf
parts["OBJETIVA"] = cylY(OBJ_D / 2, Y_FRENTE + 6, Y_FRENTE + 6 + OBJ_E, z=ZA)

# para-sol: encaixa por fora da celula da objetiva
y_ps = Y_FRENTE + CEL_FRENTE_L - 22
ps = tuboY(PARASOL_D / 2, PARASOL_D / 2 - PARASOL_PAREDE, y_ps, y_ps + PARASOL_L, ZA)
ps = fuse(ps, tuboY(PARASOL_D / 2 - PARASOL_PAREDE, CEL_D / 2, y_ps, y_ps + 8, ZA))   # anel de encaixe
parts["PARASOL"] = ps

# sapata: abracadeira em volta do tubo + bloco de fixacao com 2 furos roscados
anel = tuboY(R + ANEL_E, R, -ANEL_L / 2, ANEL_L / 2, ZA)
bloco = box(-SAPATA_W / 2, SAPATA_W / 2, -SAPATA_L / 2, SAPATA_L / 2, 0, ZA).cut(cylY(R, -SAPATA_L, SAPATA_L, z=ZA))
sap = fuse(anel, bloco)
for s in (-1, 1):
    sap = sap.cut(Part.makeCylinder(FURO_D / 2, FURO_P, V(0, s * FURO_DIST / 2, 0)))
parts["SAPATA"] = sap

# focalizador cremalheira: corpo, caixa da cremalheira embaixo, eixo e 2 manoplas
y_f1 = Y_TRAS - 6; y_f0 = y_f1 - FOC_L
corpo = tuboY(FOC_D / 2, FOC_TUBO_OD / 2 + 0.3, y_f0, y_f1, ZA)
crem = box(-12, 12, y_f0 + 5, y_f1 - 5, ZA - FOC_D / 2 - 14, ZA - FOC_D / 2 + 6)
crem = crem.cut(cylY(FOC_TUBO_OD / 2 + 0.3, y_f0, y_f1, z=ZA))
y_k = (y_f0 + y_f1) / 2; z_k = ZA - FOC_D / 2 - 6
eixo_k = Part.makeCylinder(3, 2 * (12 + KNOB_L) + 2, V(-12 - KNOB_L - 1, y_k, z_k), V(1, 0, 0))
knobs = [Part.makeCylinder(KNOB_D / 2, KNOB_L, V(s * 13 if s > 0 else -13 - KNOB_L, y_k, z_k), V(1, 0, 0)) for s in (-1, 1)]
parts["FOCALIZADOR"] = fuse(corpo, crem, eixo_k, *knobs)

y_t1 = y_f1 - 2; y_t0 = y_f0 - FOC_CURSO               # tubo de foco (fica dentro do corpo + curso)
parts["TUBO_FOCO"] = tuboY(FOC_TUBO_OD / 2, FOC_TUBO_ID / 2, y_t0, y_t1, ZA)

# diagonal 90 graus + ocular; gira DIAG_ANG em volta do eixo optico
y_d1 = y_t0 - 4; y_dc = y_d1 - DIAG_CUBO / 2
diag = fuse(cylY(FOC_TUBO_OD / 2 + 2, y_t0 - 4, y_t0, z=ZA),                       # anel de aperto
            box(-DIAG_CUBO / 2, DIAG_CUBO / 2, y_d1 - DIAG_CUBO, y_d1, ZA - DIAG_CUBO / 2, ZA + DIAG_CUBO / 2),
            Part.makeCylinder(DIAG_CUBO / 2 - 1, 18, V(0, y_dc, ZA + DIAG_CUBO / 2), V(0, 0, 1)))
# chanfro a 45 graus atras (onde fica o espelho)
ch = box(-30, 30, -30, 30, -30, 30)
ch.rotate(V(0, 0, 0), V(1, 0, 0), 45)
ch.translate(V(0, y_d1 - DIAG_CUBO - 21, ZA - DIAG_CUBO / 2 - 21 + 14))
diag = diag.cut(ch).removeSplitter()
z_oc = ZA + DIAG_CUBO / 2 + 18
ocular = fuse(Part.makeCylinder(OCULAR_D / 2 - 4, 8, V(0, y_dc, z_oc), V(0, 0, 1)),
              Part.makeCylinder(OCULAR_D / 2, OCULAR_L - 8, V(0, y_dc, z_oc + 8), V(0, 0, 1)),
              Part.makeCylinder(OCULAR_D / 2 + 1.5, 10, V(0, y_dc, z_oc + OCULAR_L - 2), V(0, 0, 1)))
ocular = ocular.cut(Part.makeCylinder(OCULAR_D / 2 - 8, 4, V(0, y_dc, z_oc + OCULAR_L + 4), V(0, 0, 1)))
for nm, s in (("DIAGONAL", diag), ("OCULAR", ocular)):
    s.rotate(V(0, 0, ZA), V(0, 1, 0), DIAG_ANG)
    parts[nm] = s

# buscador red dot sobre o tubo, perto do focalizador
y_b = Y_TRAS + BUSCADOR_DE_TRAS; zt = ZA + R
sapata_b = box(-10, 10, y_b - 25, y_b + 25, zt - 2, zt + 6).cut(cylY(R, y_b - 30, y_b + 30, z=ZA))
corpo_b = box(-12, 12, y_b - 45, y_b + 30, zt + 6, zt + 30)
janela = box(-14, 14, y_b + 30, y_b + 45, zt + 6, zt + 40).cut(box(-10, 10, y_b + 29, y_b + 46, zt + 10, zt + 36))
parts["BUSCADOR"] = fuse(sapata_b, corpo_b, janela)

# ------------------------------------------------------------------ relatorio
mt = sum(MASSA.values())
cg = V()
for nm, s in parts.items():
    c = s.CenterOfMass if s.ShapeType == "Solid" else s.BoundBox.Center
    cg += c * (MASSA[nm] / mt)
bb = Part.makeCompound(list(parts.values())).BoundBox
print("Pecas: %d   massa estimada: %.2f kg" % (len(parts), mt))
print("Envelope X %.0f..%.0f  Y %.0f..%.0f  Z %.0f..%.0f mm (comprimento total %.0f mm)"
      % (bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax, bb.YLength))
print("Eixo optico a %.1f mm da face de baixo da sapata" % ZA)
print("CG estimado: Y=%+.0f mm (positivo = para a frente da sapata), Z=%.0f mm" % (cg.y, cg.z))
bad = [nm for nm, s in parts.items() if not s.isValid()]
print("Solidos invalidos: %s" % (", ".join(bad) or "nenhum"))
names = list(parts)
hits = []
for i, a in enumerate(names):
    for b in names[i + 1:]:
        v = parts[a].common(parts[b]).Volume
        if v > 1.0:
            hits.append("%s x %s (%.0f mm3)" % (a, b, v))
print("Interferencias: %s" % ("; ".join(hits) or "nenhuma"))

# ------------------------------------------------------------------ salvar
doc = App.newDocument("GREIKA_70070")
part = doc.addObject("App::Part", "OTA_GREIKA_70070")
objs = []
for nm, s in parts.items():
    o = doc.addObject("Part::Feature", nm)
    o.Shape = s
    part.addObject(o)
    objs.append(o)
doc.recompute()
doc.saveAs(os.path.join(BASEDIR, "GREIKA_70070.FCStd"))
import Import
os.makedirs(os.path.join(BASEDIR, "STEP"), exist_ok=True)
Import.export([part], os.path.join(BASEDIR, "STEP", "GREIKA_70070.step"))
print("Salvo: GREIKA_70070.FCStd e STEP/GREIKA_70070.step")

# ------------------------------------------------------------------ imagem de conferencia
if PREVIEW:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    cores = dict(TUBO="#3a3d42", PARASOL="#1c1c1c", CELULA_TRASEIRA="#222", CELULA_OBJETIVA="#222", OBJETIVA="#6fa8dc",
                 SAPATA="#555", FOCALIZADOR="#2a2a2a", TUBO_FOCO="#bbbbbb", DIAGONAL="#202020", OCULAR="#303030",
                 BUSCADOR="#444")
    import numpy as np
    from matplotlib.colors import to_rgb
    from matplotlib.collections import PolyCollection
    fig = plt.figure(figsize=(14, 9))
    ax = fig.add_subplot(2, 1, 1, projection="3d")
    ax2 = fig.add_subplot(2, 1, 2)
    luz = np.array([0.4, -0.5, 0.75]); luz /= np.linalg.norm(luz)
    T3, C3 = [], []
    for nm, s in parts.items():
        pts, tris = s.tessellate(0.5)
        A = np.array([(p.x, p.y, p.z) for p in pts]); t = np.array(tris)
        tri = A[t]
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
        k = 0.35 + 0.65 * np.abs(n @ luz)
        base = np.array(to_rgb(cores[nm])) * 1.6
        T3.extend(tri); C3.extend(np.clip(base[None, :] * k[:, None], 0, 1))
        ax2.add_collection(PolyCollection(tri[:, :, 1:], facecolor=cores[nm], edgecolor="none"))
    ax.add_collection3d(Poly3DCollection(T3, facecolors=C3, edgecolors="none"))
    L = bb.YLength
    ax.set_xlim(-L * 0.15, L * 0.15); ax.set_ylim(bb.YMin, bb.YMax); ax.set_zlim(ZA - L * 0.15, ZA + L * 0.15)
    ax.set_box_aspect((0.3, 1, 0.3), zoom=1.15); ax.view_init(elev=20, azim=-25); ax.set_axis_off()
    ax2.plot([0, 0], [0, -15], "r-"); ax2.plot([cg.y], [cg.z], "r+", ms=14)
    for s in (-1, 1):
        ax2.plot([s * FURO_DIST / 2] * 2, [0, FURO_P], "y-")
    ax2.set_xlim(bb.YMin - 10, bb.YMax + 10); ax2.set_ylim(bb.ZMin - 20, bb.ZMax + 20)
    ax2.set_aspect("equal"); ax2.grid(alpha=0.3); ax2.set_xlabel("Y (mm)  -> objetiva"); ax2.set_ylabel("Z (mm)")
    ax2.set_title("Vista lateral (cruz vermelha = CG estimado, amarelo = furos da sapata)")
    fig.tight_layout(); fig.savefig(PREVIEW, dpi=110)
    print("Preview:", PREVIEW)
