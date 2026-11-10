# Modelo APROXIMADO do tripe de aluminio do Greika 70070 (sem a cabeca azimutal) + parafuso 1/4"-20
# Medidas estimadas pela foto: confira e ajuste os parametros.
# Rodar com: "C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe" build_tripe.py
# Variaveis de ambiente opcionais: PREVIEW=caminho.png (gera uma imagem de conferencia)
#
# Sistema de coordenadas: Z = para cima; Z = 0 e a face de cima do prato (onde apoia a BASE da MONTAGEM_EQ),
# origem no centro do parafuso. A perna 1 aponta para +X.
import FreeCAD as App, Part, math, os

V = App.Vector
BASEDIR = r"C:\LUIZ\PROJECTS\GOTO_TELESCOPE\FREECAD\TRIPE"
PREVIEW = os.environ.get("PREVIEW", "")

# ------------------------------------------------------------------ parametros (mm) - TODOS ESTIMADOS
PRATO_D, PRATO_E = 100.0, 10.0      # prato de cima (a BASE da montagem tem Ø110)
CORPO_D, CORPO_H = 60.0, 20.0       # corpo central embaixo do prato
PIVO_R, PIVO_Z = 50.0, -20.0        # raio e altura do pino de articulacao das pernas
PINO_D = 6.0
ABERTURA = 23.0                     # angulo das pernas em relacao a vertical (graus)
PERNA_RAD, PERNA_TAN = 16.0, 22.0   # secao externa da perna (radial x tangencial)
PERNA_PAREDE = 1.5
PERNA_L = 620.0                     # secao externa, do pino ate a trava
INT_RAD, INT_TAN = 12.0, 18.0       # secao interna (desliza dentro da externa)
EXTENSAO = 300.0                    # quanto a secao interna esta para fora (0 = fechado)
SOBREPOSICAO = 80.0                 # quanto da secao interna fica dentro da externa
PE_D, PE_L = 26.0, 30.0             # ponteira de borracha
ESPAL_S = 310.0                     # distancia ao longo da perna (a partir do pino) onde prende o espalhador
BANDEJA_D, BANDEJA_E = 140.0, 6.0   # bandeja central do espalhador
FURO_OCULAR_D = 32.0                # 3 furos para oculares de 1,25"
BRACO_W, BRACO_E = 20.0, 4.0        # bracos do espalhador
# parafuso 1/4"-20 UNC (rosca nao modelada: cilindro com o diametro nominal)
PARAF_D = 6.35
PARAF_ACIMA = 10.0                  # quanto sai acima do prato (a porca 1/4" da BASE tem 6,5 mm)
MANOPLA_D, MANOPLA_H = 30.0, 12.0   # manopla serrilhada embaixo do corpo central

A = math.radians(ABERTURA)
parts = {}

def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))

def cylZ(r, z0, z1, x=0.0, y=0.0):
    return Part.makeCylinder(r, z1 - z0, V(x, y, z0), V(0, 0, 1))

def cylY(r, y0, y1, x=0.0, z=0.0):
    return Part.makeCylinder(r, y1 - y0, V(x, y0, z), V(0, 1, 0))

def fuse(*s):
    r = s[0]
    for t in s[1:]:
        r = r.fuse(t)
    return r.removeSplitter()

def no_pivo(s, th, inclina=True):
    """coord. locais da perna (X radial, Y tangencial, pino na origem) -> mundo"""
    s = s.copy()
    if inclina:
        s.rotate(V(), V(0, 1, 0), -ABERTURA)
    s.rotate(V(), V(0, 0, 1), th)
    s.translate(V(PIVO_R * math.cos(math.radians(th)), PIVO_R * math.sin(math.radians(th)), PIVO_Z))
    return s

# ---------------- cabeca: prato + corpo + 3 pares de orelhas
cab = fuse(cylZ(PRATO_D / 2, -PRATO_E, 0), cylZ(CORPO_D / 2, -PRATO_E - CORPO_H, -PRATO_E))
gt = PERNA_TAN / 2 + 0.5
for th in (0, 120, 240):
    for sy in (-1, 1):
        ore = box(-12, 10, gt if sy > 0 else -gt - 4, gt + 4 if sy > 0 else -gt, -12, -PIVO_Z - PRATO_E + 0.5)
        ore = fuse(ore, cylY(8, gt if sy > 0 else -gt - 4, gt + 4 if sy > 0 else -gt))   # ponta redonda em volta do pino
        cab = cab.fuse(no_pivo(ore, th, inclina=False))
    cab = cab.cut(no_pivo(cylY(PINO_D / 2 + 0.1, -30, 30), th, inclina=False))
cab = cab.removeSplitter()

# ---------------- parafuso 1/4"-20 com manopla serrilhada (por baixo do corpo)
z_man1 = -PRATO_E - CORPO_H - 0.5
man = cylZ(MANOPLA_D / 2, z_man1 - MANOPLA_H, z_man1)
for k in range(12):
    a = math.radians(30 * k)
    man = man.cut(cylZ(2.5, z_man1 - MANOPLA_H, z_man1, MANOPLA_D / 2 * math.cos(a), MANOPLA_D / 2 * math.sin(a)))
paraf = fuse(man, cylZ(PARAF_D / 2, z_man1 - 1, PARAF_ACIMA))
parts["PARAFUSO_1-4"] = paraf
cab = cab.cut(cylZ(PARAF_D / 2 + 0.4, -60, 1)).removeSplitter()
parts["CABECA"] = cab

# ---------------- pernas (locais: pino na origem, perna para -Z)
hr, ht = PERNA_RAD / 2, PERNA_TAN / 2
ir, it = INT_RAD / 2, INT_TAN / 2
z_fim = -PERNA_L                     # fim da secao externa
z_int0 = z_fim - EXTENSAO            # fim da secao interna
ext_env = box(-hr, hr, -ht, ht, z_fim, 0)
perna_ext = fuse(ext_env, cylY(hr, -ht, ht))
perna_ext = perna_ext.cut(box(-hr + PERNA_PAREDE, hr - PERNA_PAREDE, -ht + PERNA_PAREDE, ht - PERNA_PAREDE, z_fim - 1, -30))
perna_ext = perna_ext.cut(cylY(PINO_D / 2 + 0.1, -ht - 1, ht + 1)).removeSplitter()
int_env = box(-ir, ir, -it, it, z_int0, z_fim + SOBREPOSICAO)
trava = box(-hr - 4, hr + 4, -ht - 4, ht + 4, z_fim - 20, z_fim + 20)
trava = trava.cut(ext_env).cut(int_env)
trava = fuse(trava, cylY(5, ht + 4, ht + 16, x=0, z=z_fim))          # manipulo da trava (lado tangencial)
pe = cylZ(PE_D / 2, z_int0 - PE_L + 8, z_int0 + 8).cut(int_env)
abr = box(-hr - 3, hr + 3, -ht - 3, ht + 3, -ESPAL_S - 15, -ESPAL_S + 15).cut(ext_env)
pino = cylY(PINO_D / 2, -gt - 4, gt + 4)

for i, th in enumerate((0, 120, 240), 1):
    parts["PERNA%d_EXTERNA" % i] = no_pivo(perna_ext, th)
    parts["PERNA%d_INTERNA" % i] = no_pivo(int_env, th)
    parts["PERNA%d_TRAVA" % i] = no_pivo(trava, th)
    parts["PERNA%d_PONTEIRA" % i] = no_pivo(pe, th)
    parts["PERNA%d_ABRACADEIRA" % i] = no_pivo(abr, th)
    parts["PINO%d" % i] = no_pivo(pino, th, inclina=False)

# ---------------- espalhador: bandeja central + 3 bracos horizontais
z_s = PIVO_Z - ESPAL_S * math.cos(A)
r_eixo = PIVO_R + ESPAL_S * math.sin(A)
r_fim = r_eixo - (hr + 3) / math.cos(A) - BRACO_E / 2 * math.tan(A) - 0.2
band = cylZ(BANDEJA_D / 2, z_s - BANDEJA_E / 2, z_s + BANDEJA_E / 2)
for th in (60, 180, 300):
    a = math.radians(th)
    band = band.cut(cylZ(FURO_OCULAR_D / 2, z_s - 5, z_s + 5, 42 * math.cos(a), 42 * math.sin(a)))
parts["BANDEJA"] = band
for i, th in enumerate((0, 120, 240), 1):
    b = box(BANDEJA_D / 2, r_fim, -BRACO_W / 2, BRACO_W / 2, z_s - BRACO_E / 2, z_s + BRACO_E / 2)
    b.rotate(V(), V(0, 0, 1), th)
    parts["BRACO%d" % i] = b

# ------------------------------------------------------------------ relatorio
bb = Part.makeCompound(list(parts.values())).BoundBox
r_pe = PIVO_R + (PERNA_L + EXTENSAO + PE_L - 8) * math.sin(A)
print("Pecas: %d" % len(parts))
print("Altura do prato acima do chao: %.0f mm   (pes num circulo de raio %.0f mm)" % (-bb.ZMin, r_pe))
print("Envelope X %.0f..%.0f  Y %.0f..%.0f  Z %.0f..%.0f mm" % (bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax))
print("Espalhador a %.0f mm abaixo do prato" % -z_s)
bad = [nm for nm, s in parts.items() if not s.isValid()]
print("Solidos invalidos: %s" % (", ".join(bad) or "nenhum"))
names = list(parts)
hits = []
for i, a in enumerate(names):
    for b in names[i + 1:]:
        if not parts[a].BoundBox.intersect(parts[b].BoundBox):
            continue
        v = parts[a].common(parts[b]).Volume
        if v > 1.0:
            hits.append("%s x %s (%.0f mm3)" % (a, b, v))
print("Interferencias: %s" % ("; ".join(hits) or "nenhuma"))

# ------------------------------------------------------------------ salvar
doc = App.newDocument("TRIPE")
part = doc.addObject("App::Part", "TRIPE_GREIKA_70070")
for nm, s in parts.items():
    o = doc.addObject("Part::Feature", nm.replace("-", "_"))
    o.Label = nm
    o.Shape = s
    part.addObject(o)
doc.recompute()
doc.saveAs(os.path.join(BASEDIR, "TRIPE.FCStd"))
import Import
os.makedirs(os.path.join(BASEDIR, "STEP"), exist_ok=True)
Import.export([part], os.path.join(BASEDIR, "STEP", "TRIPE.step"))
print("Salvo: TRIPE.FCStd e STEP/TRIPE.step")

# ------------------------------------------------------------------ imagem de conferencia
if PREVIEW:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.colors import to_rgb
    from matplotlib.collections import PolyCollection
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    def cor(nm):
        if "INTERNA" in nm: return "#b8bcc2"
        if "EXTERNA" in nm: return "#2b2d31"
        if "PARAFUSO" in nm or "PINO" in nm: return "#c9a227"
        return "#1e1e1e"
    fig = plt.figure(figsize=(14, 8))
    ax = fig.add_subplot(1, 2, 1, projection="3d")
    ax2 = fig.add_subplot(1, 2, 2)
    luz = np.array([0.4, -0.5, 0.75]); luz /= np.linalg.norm(luz)
    T3, C3 = [], []
    for nm, s in parts.items():
        pts, tris = s.tessellate(0.5)
        P = np.array([(p.x, p.y, p.z) for p in pts]); tri = P[np.array(tris)]
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
        k = 0.35 + 0.65 * np.abs(n @ luz)
        T3.extend(tri); C3.extend(np.clip(np.array(to_rgb(cor(nm)))[None, :] * 1.6 * k[:, None], 0, 1))
        ax2.add_collection(PolyCollection(tri[:, :, [0, 2]], facecolor=cor(nm), edgecolor="none"))
    ax.add_collection3d(Poly3DCollection(T3, facecolors=C3, edgecolors="none"))
    H = bb.ZLength
    ax.set_xlim(-H / 2, H / 2); ax.set_ylim(-H / 2, H / 2); ax.set_zlim(bb.ZMin, bb.ZMax)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=12, azim=-60); ax.set_axis_off()
    ax2.set_xlim(bb.XMin - 20, bb.XMax + 20); ax2.set_ylim(bb.ZMin - 20, bb.ZMax + 20)
    ax2.set_aspect("equal"); ax2.grid(alpha=0.3); ax2.set_xlabel("X (mm)"); ax2.set_ylabel("Z (mm)")
    ax2.set_title("Vista lateral (Z = 0 no topo do prato)")
    fig.tight_layout(); fig.savefig(PREVIEW, dpi=110)
    print("Preview:", PREVIEW)
