# -*- coding: utf-8 -*-
# Verificacao da MONTAGEM_EQ_V3: interferencias, folgas, balanceamento, cargas e varredura de colisoes.
#   & "C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe" scripts\verifica_v3.py      (leva alguns minutos)
import math
import os
import sys
import time

import FreeCAD as App
import Part

V = App.Vector
D = r"C:\LUIZ\PROJECTS\GOTO_TELESCOPE\FREECAD\MONTAGEM_EQ"
sys.path.insert(0, os.path.join(D, "scripts"))
import eq_massas as MM  # noqa: E402

doc = App.openDocument(os.path.join(D, os.environ.get("V3_NOME", "MONTAGEM_EQ_V3.FCStd")))
doc.recompute()
L = lambda n: doc.getObjectsByLabel(n)[0]
forma, raiz = MM.forma, MM.raiz
folhas = MM.folhas(doc)
sh = {o.Name: forma(o) for o in folhas}
G = 9.81


def eixo_cil(o):
    s = sh[o.Name]; melhor = None
    for f in s.Faces:
        if isinstance(f.Surface, Part.Cylinder) and abs(f.Surface.Radius - 4.0) < 0.05 and (melhor is None or f.Area > melhor.Area):
            melhor = f
    d = V(melhor.Surface.Axis); d.normalize()
    return V(melhor.Surface.Center), d if d.z > 0 else d * -1


pra, dra = eixo_cil(L("EIXO")); pde, dde = eixo_cil(L("EIXO001"))
w = pra - pde; b_ = dra.dot(dde); d_, e_ = dra.dot(w), dde.dot(w)
I = pra + dra * ((b_ * e_ - d_) / (1 - b_ * b_))
n = dra.cross(dde); n.normalize()
print("== eixos: latitude %.2f graus, RA x DEC %.2f graus, distancia entre eixos %.3f mm" % (
    math.degrees(math.asin(dra.z)), math.degrees(math.acos(abs(dra.dot(dde)))), abs((pde - pra).dot(n))))

# ------------------------------------------------------------------ interferencias
ESPERADAS = {frozenset(p) for p in [("BASE", "PARAFUSO_1-4")]}   # rosca 1/4" aberta no furo Ø5,2
print("\n== interferencias entre conjuntos (> 0,05 mm3)")
grupos = {}
for o in folhas:
    grupos.setdefault(raiz(o).Label, []).append(o)
nomes = list(grupos)
achou = 0
for i in range(len(nomes)):
    for j in range(i + 1, len(nomes)):
        for a in grupos[nomes[i]]:
            for b in grupos[nomes[j]]:
                sa, sb = sh[a.Name], sh[b.Name]
                if not sa.BoundBox.intersect(sb.BoundBox):
                    continue
                v = sa.common(sb).Volume
                if v > 0.05:
                    esp = frozenset((a.Label, b.Label)) in ESPERADAS
                    achou += 0 if esp else 1
                    print("   %s/%s x %s/%s: %.2f mm3%s" % (nomes[i], a.Label, nomes[j], b.Label, v, "  (esperado)" if esp else ""))
# dentro do App::Part DEC: as pecas novas do contrapeso
novos = [o for o in grupos["DEC"] if o.Label.startswith(("TAMPA_CW", "BARRA_M12", "PORCAS_M12", "CONTRAPESO"))]
for a in novos:
    for b in grupos["DEC"]:
        if b in novos or a is b:
            continue
        if sh[a.Name].BoundBox.intersect(sh[b.Name].BoundBox):
            v = sh[a.Name].common(sh[b.Name]).Volume
            if v > 0.05:
                achou += 1
                print("   DEC/%s x DEC/%s: %.2f mm3" % (a.Label, b.Label, v))
print("   interferencias inesperadas:", achou)

print("\n== folgas (mm)")
for a, b in [("ACOPLADOR1", "MANCAL"), ("ACOPLADOR1", "ROL_608_MANCAL"), ("ACOPLADOR2", "MANCAL002"), ("ACOPLADOR2", "ROL_608_MANCAL002"),
             ("ACOPLADOR1", "EIXO"), ("ACOPLADOR2", "EIXO001"), ("ACOPLADOR1", "MANCAL002"), ("ACOPLADOR3", "MANCAL"),
             ("ACOPLADOR3", "BASE"), ("SELA_DEC", "ACOPLADOR2"), ("BARRA_VIXEN_200", "SELA_DEC"), ("SAPATA", "BARRA_VIXEN_200"),
             ("SELA_DEC", "MANCAL002"), ("BARRA_VIXEN_200", "MANCAL002"), ("TAMPA_CW", "PLACA_SUPERIOR002"),
             ("TAMPA_CW", "EIXO001"), ("TAMPA_CW", "SAIDA002")]:
    print("   %-16s x %-20s %.2f" % (a, b, sh[L(a).Name].distToShape(sh[L(b).Name])[0]))
s3 = sh[L("ACOPLADOR3").Name]
ys = [v.Point.y for v in s3.Vertexes if v.Point.z < -30]
print("   haste do ACOPLADOR3: y %.2f..%.2f (bochechas em +-5,25)" % (min(ys), max(ys)))

# ------------------------------------------------------------------ balanceamento e cargas
print("\n== balanceamento (massas estimadas em eq_massas.py)")
Md, cd = MM.cm(doc, MM.conjunto_dec(doc))
pd_ = (cd - I) - dde * (cd - I).dot(dde)
print("   DEC: %.0f g, CM a %.2f mm do eixo -> torque max %.3f N.m" % (Md, pd_.Length, Md / 1000 * G * pd_.Length / 1000))
Mr, cr = MM.cm(doc, MM.conjunto_ra(doc))
pr_ = (cr - I) - dra * (cr - I).dot(dra)
lat = math.asin(dra.z)
print("   RA:  %.0f g, CM a %.2f mm do eixo -> torque max %.3f N.m" % (Mr, pr_.Length, Mr / 1000 * G * math.cos(lat) * pr_.Length / 1000))
cw = [L(x) for x in ("CONTRAPESO_COPO", "CONTRAPESO_TAMPA", "CONTRAPESO_ENCHIMENTO", "PORCAS_M12_CONTRAPESO")]
mcw, ccw = MM.cm(doc, cw)
me, _ = MM.cm(doc, [L("CONTRAPESO_ENCHIMENTO")])
r_cw = -(ccw - I).dot(dde)
print("   contrapeso: %.0f g (enchimento %.0f g) a %.0f mm do cruzamento" % (mcw, me, r_cw))
print("   sensibilidade: 1 cm de deslocamento do copo na barra = %.3f N.m no RA; +100 g no tubo pedem +%.0f g no copo" % (
    mcw / 1000 * G * math.cos(lat) * 0.01, 100 * ((MM.cm(doc, [L("TUBO")])[1] - I).dot(dde)) / r_cw))


def mancais(g):
    ps = {}
    for o in grupos[g]:
        if o.Label.startswith(("ROL_608_MANCAL", "ROL_608_EIXO_PLACA")):
            ps["M" if "MANCAL" in o.Label else "P"] = MM._cm_forma(sh[o.Name])
    return ps["M"], ps["P"]


for nome, objs, d, g in (("RA", MM.conjunto_ra(doc), dra, "RA"), ("DEC", MM.conjunto_dec(doc), dde, "DEC")):
    M, c = MM.cm(doc, objs)
    pm, pp = mancais(g)
    a = (c - pm).dot(d) * (1 if (pm - pp).dot(d) > 0 else -1)      # + = fora do vao, alem do 608 do MANCAL
    Lv = (pm - pp).Length
    F = M / 1000 * G * (math.cos(lat) if nome == "RA" else 1.0)
    Rm = F * (1 + a / Lv); Rp = F * a / Lv
    print("   %s: carga %.0f g, CM %.1f mm alem do 608 do MANCAL (vao %.1f): 608 MANCAL %.1f N, 608 PLACA %.1f N; "
          "flexao no eixo %.2f N.m (%.0f MPa)" % (nome, M, a, Lv, Rm, Rp, F * a / 1000, F * a / 50.3))

# ------------------------------------------------------------------ varredura de colisoes
CASCA = ("CAIXA", "TAMPA", "MANCAL", "PLACA_SUPERIOR", "NEMA17", "POLIA_GT2_20T", "CORREIA", "ESPACADOR_PLACA", "PARAFUSO_M3",
         "TAMPA_CW", "BARRA_M12", "PORCAS_M12", "CONTRAPESO")


def sel(g, casca=True):
    return [o.Name for o in grupos.get(g, []) if not casca or o.Label.startswith(CASCA)]


tubo = sel("OTA_GREIKA_70070", False) + sel("ACOPLADOR2", False) + sel("SELA_DEC", False) + sel("BARRA_VIXEN_200", False)
dec_c = sel("DEC") + sel("ACOPLADOR1", False)
ra_c = sel("RA") + sel("ACOPLADOR3", False) + sel("BASE", False)
tripe = sel("TRIPE_GREIKA_70070", False)


def girado(nomes_, c, d, ang, base=None):
    r = App.Placement(c, App.Rotation(d, ang)).multiply(App.Placement(c * -1, App.Rotation()))
    out = {}
    for k in nomes_:
        s = (base or sh)[k].copy(); s.Placement = r.multiply(s.Placement); out[k] = s
    return out


def colide(mov, fix):
    r = []
    for a, sa in mov.items():
        for b, sb in fix.items():
            if sa.BoundBox.intersect(sb.BoundBox):
                v = sa.common(sb).Volume
                if v > 1.0:
                    r.append("%s x %s %.0f mm3" % (doc.getObject(a).Label, doc.getObject(b).Label, v))
    return r


t0 = time.time()
print("\n== DEC 360 graus (RA = 0)")
fix = {k: sh[k] for k in dec_c + ra_c + tripe}
livre = True
for ang in range(0, 360, 20):
    c = colide(girado(tubo, pde, dde, ang), fix)
    if c:
        livre = False
        print("   DEC %+4d: %s" % (ang, "; ".join(c[:4])))
print("   %s (%.0f s)" % ("livre em toda a volta" if livre else "", time.time() - t0))

print("\n== RA (redutor DEC + contrapeso + tubo) contra (redutor RA + base + tripe)")
fix = {k: sh[k] for k in ra_c + tripe}
limite = {}
for dang in (0, 90, 180, 270):
    tubo_d = girado(tubo, pde, dde, dang)
    base = dict(sh); base.update(tubo_d)
    for rang in list(range(-165, 166, 15)):
        c = colide(girado(dec_c + tubo, pra, dra, rang, base), fix)
        if c:
            limite.setdefault(dang, []).append(rang)
            if abs(rang) <= 120:
                print("   DEC %3d RA %+4d: %s" % (dang, rang, "; ".join(c[:4])))
    ok = [r for r in range(-165, 166, 15) if r not in limite.get(dang, [])]
    neg = max([r for r in limite.get(dang, []) if r < 0], default=None)
    pos = min([r for r in limite.get(dang, []) if r > 0], default=None)
    print("   DEC %3d: primeira colisao em RA %s / %s (%.0f s)" % (dang, neg, pos, time.time() - t0))
