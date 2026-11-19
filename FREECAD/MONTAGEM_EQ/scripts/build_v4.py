# -*- coding: utf-8 -*-
# Gera MONTAGEM_EQ_V4.FCStd (montagem reforcada para o refletor 203 mm) e os STL das pecas impressas (STL_V4).
# Rodar pela interface para salvar as cores:  "C:\Program Files\FreeCAD 1.0\bin\freecad.exe" build_v4.py
# O script fecha o FreeCAD no fim e grava o relatorio em V4_LOG (padrao: %TEMP%\build_v4.log).
# Le o refletor do MONTAGEM_EQ_V3.FCStd sem alterar o arquivo.
import math
import os
import re
import shutil
import sys
import tempfile
import time
import traceback

try:
    AQUI = os.path.dirname(os.path.abspath(__file__))
except NameError:
    AQUI = r"C:\LUIZ\PROJECTS\GOTO_TELESCOPE\FREECAD\MONTAGEM_EQ\scripts"
PASTA = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
ARQ_V3 = os.path.join(PASTA, "MONTAGEM_EQ_V3.FCStd")
ARQ_V4 = os.environ.get("V4_ARQ", os.path.join(PASTA, "MONTAGEM_EQ_V4.FCStd"))
PASTA_STL = os.environ.get("V4_STL", os.path.join(PASTA, "STL_V4"))
LOG = os.environ.get("V4_LOG", os.path.join(tempfile.gettempdir(), "build_v4.log"))

import FreeCAD as App
import Part

import eq_massas as EM
import v4_modelo as M

try:
    import FreeCADGui as Gui
    GUI = App.GuiUp
except ImportError:
    GUI = False

V = App.Vector
G = 9.81
_log = open(LOG, "w", encoding="utf-8")


def pr(*a):
    _log.write(" ".join(str(x) for x in a) + "\n"); _log.flush()


def perp(v, ax):
    return v - ax * v.dot(ax)


def cg_forma(s):
    return EM._cm_forma(s)


# --------------------------------------------------------------- refletor (copiado da V3)
def le_refletor():
    doc3 = App.openDocument(ARQ_V3)
    try:
        R = doc3.getObjectsByLabel("REFLETOR_203MM")[0]
        gR = EM.gp(R).multiply(R.Placement)
        inv = gR.inverse()
        itens = []
        for o in EM.folhas(doc3):
            if EM.raiz(o) != R:
                continue
            if o.getParentGeoFeatureGroup() == R and o.Label.split()[-1] in ("004", "005", "006"):
                continue   # fixadores duplicados (os originais estao no grupo FIXADORES COLIMACAO)
            s = EM.forma(o)
            if s.isNull() or s.Volume < 1e-6:
                continue
            s.Placement = inv.multiply(s.Placement)
            ap = None
            if GUI and o.ViewObject is not None:
                try:
                    ap = o.ViewObject.ShapeAppearance
                except Exception:
                    ap = None
            itens.append(dict(nome=o.Label, forma=s, massa=s.Volume / 1000.0 * M.dens_refl(o.Label), ap=ap,
                              vis=bool(o.Visibility)))
        return itens, gR.Rotation
    finally:
        App.closeDocument(doc3.Name)


def main():
    t0 = time.time()
    E = M.eixos()
    p, d, I = E["p"], E["d"], E["I"]
    pr("LAT %.1f | reducao %.0f:1 | entre eixos pinhao-coroa %.2f mm" % (M.LAT, M.REDUCAO, M.A_H))
    pr("cruzamento dos eixos I = (%.1f, %.1f, %.1f), pivo de latitude a %.0f mm da placa" % (I.x, I.y, I.z, M.H_PIV))

    # ---- refletor
    refl, rot_refl = le_refletor()
    m_r = sum(x["massa"] for x in refl) + sum(x[1] for x in M.MASSAS_REFLETOR)
    cg_r = (sum((cg_forma(x["forma"]) * x["massa"] for x in refl), V()) +
            sum((V(*x[2]) * x[1] for x in M.MASSAS_REFLETOR), V())) * (1.0 / m_r)
    pr("refletor: %d pecas + espelhos/ocular estimados = %.2f kg, CG local (%.1f, %.1f, %.1f)" % (
        len(refl), m_r / 1000, cg_r.x, cg_r.y, cg_r.z))

    # ---- pecas da montagem
    coroa = M.coroa_200(M.FASES["coroa_200"])
    pr("coroa 200T helicoidal: valida %s (%.0f s)" % (coroa.isValid(), time.time() - t0))
    pecas = []
    M.modulo_eixo(pecas, "RA", "fixo", "ra", coroa, M.FASES)
    M.modulo_eixo(pecas, "DEC", "ra", "dec", coroa, M.FASES)
    M.fecha_tmp()
    s_tubo, pl_refl = M.sela_e_tubo(pecas, E, rot_refl, cg_r.z)
    pr("eixo do tubo a %.0f mm do cruzamento dos eixos" % s_tubo)

    plc = {"RA": E["pl_ra"], "DEC": E["pl_dec"], "SELA": E["pl_sela"], "CONTRAPESO": E["pl_dec"], "BASE": App.Placement()}

    def massas_globais(lista):
        r = []
        for pc in lista:
            r.append((pc.massa(), plc[pc.grupo].multVec(cg_forma(pc.forma)), pc.conjunto))
        for x in refl:
            r.append((x["massa"], pl_refl.multVec(cg_forma(x["forma"])), "dec"))
        for nome, m, loc in M.MASSAS_REFLETOR:
            r.append((m, pl_refl.multVec(V(*loc)), "dec"))
        return r

    # ---- contrapeso: barra, capa e porca primeiro, depois os pesos de 5 kg onde equilibram
    tmp = []
    M.contrapeso(tmp, [])
    rot = [x for x in massas_globais(pecas + tmp) if x[2] in ("ra", "dec")]
    mom = sum((perp(c - I, p) * m for m, c, _ in rot), V())       # g.mm, perpendicular ao RA
    mom_d = mom.dot(d)
    z_topo, z_fundo = -40.0, -30.0 - M.L_BARRA_CW + 12.0
    centros = None
    for n in (1, 2, 3):
        dist = mom_d / (n * M.M_CONTRAPESO)              # distancia media dos centros ao cruzamento
        zc = M.Z_I - dist                                 # centro medio no quadro do DEC
        cs = [zc + (n - 1) * M.H_CP / 2 - k * M.H_CP for k in range(n)]
        if cs[0] + M.H_CP / 2 <= z_topo and cs[-1] - M.H_CP / 2 >= z_fundo:
            centros = cs
            break
    if centros is None:
        raise RuntimeError("contrapeso nao cabe na barra (momento %.0f kg.mm)" % (mom_d / 1000))
    M.contrapeso(pecas, centros)
    pr("contrapeso: %d x %.0f kg, centro(s) a %s mm do cruzamento dos eixos (momento do lado do tubo %.2f kg.m)" % (
        len(centros), M.M_CONTRAPESO / 1000, ", ".join("%.0f" % (M.Z_I - c) for c in centros), mom_d / 1e6))
    pr("  desbalanceamento lateral que o contrapeso nao corrige: %.3f kg.m" % (abs(mom.dot(V(0, 1, 0))) / 1e6))

    # ---- base: o furo do tripe vai debaixo do CG do conjunto (2 iteracoes, a placa entra no CG)
    x_tripe = 190.0
    for _ in range(3):
        pb = []
        M.base(pb, E, x_tripe)
        tudo = massas_globais(pecas + pb)
        mt = sum(x[0] for x in tudo)
        cgt = sum((x[1] * x[0] for x in tudo), V()) * (1.0 / mt)
        x_tripe = round(cgt.x / 5.0) * 5.0
    pecas += pb
    pr("massa total %.1f kg, CG em (%.0f, %.0f, %.0f) -> furo 3/8\" do tripe em x = %.0f mm (%.0f mm ao sul do pivo)" % (
        mt / 1000, cgt.x, cgt.y, cgt.z, x_tripe, x_tripe))
    for conj, txt in (("fixo", "fixo (base + corpo RA + redutor RA)"), ("ra", "gira no RA (sem o tubo)"),
                      ("dec", "gira no DEC (com o tubo)")):
        pr("  %-32s %.2f kg" % (txt, sum(x[0] for x in massas_globais(pecas) if x[2] == conj) / 1000))

    # ---- documento
    if os.path.exists(ARQ_V4):
        bk = os.path.join(os.path.dirname(ARQ_V4), "_backup_v4")
        os.makedirs(bk, exist_ok=True)
        shutil.copy2(ARQ_V4, os.path.join(bk, "MONTAGEM_EQ_V4_%s.FCStd" % time.strftime("%Y%m%d_%H%M%S")))
    doc = App.newDocument("MONTAGEM_EQ_V4")
    grupos = {}
    ordem = ["BASE", "RA", "RA_EIXO", "DEC", "DEC_EIXO", "CONTRAPESO", "SELA", "REFLETOR_203MM"]
    pl_grupo = {"BASE": plc["BASE"], "RA": plc["RA"], "RA_EIXO": plc["RA"], "DEC": plc["DEC"], "DEC_EIXO": plc["DEC"],
                "CONTRAPESO": plc["CONTRAPESO"], "SELA": plc["SELA"], "REFLETOR_203MM": pl_refl}
    for nome in ordem:
        g = doc.addObject("App::Part", nome)
        g.Placement = pl_grupo[nome]
        grupos[nome] = g

    def props(o, massa, conj, mat, impressa):
        o.addProperty("App::PropertyFloat", "Massa_g", "V4", "massa estimada (g)").Massa_g = massa
        o.addProperty("App::PropertyString", "Conjunto", "V4", "fixo / ra / dec: o que gira junto").Conjunto = conj
        o.addProperty("App::PropertyString", "Material", "V4").Material = mat or "comprado"
        o.addProperty("App::PropertyBool", "Impressa", "V4").Impressa = impressa

    for pc in pecas:
        gn = pc.grupo + ("_EIXO" if (pc.grupo, pc.conjunto) in (("RA", "ra"), ("DEC", "dec")) else "")
        o = doc.addObject("Part::Feature", re.sub(r"\W", "_", pc.nome))
        o.Label = pc.nome
        o.Shape = pc.forma
        props(o, pc.massa(), pc.conjunto, pc.mat, pc.impressa)
        grupos[gn].addObject(o)
        if GUI:
            o.ViewObject.ShapeColor = M.CORES[pc.cor]
    for x in refl:
        o = doc.addObject("Part::Feature", "REFL")
        o.Label = x["nome"]
        o.Shape = x["forma"]
        props(o, x["massa"], "dec", "refletor", False)
        grupos["REFLETOR_203MM"].addObject(o)
        if GUI:
            if x["ap"] is not None:
                try:
                    o.ViewObject.ShapeAppearance = x["ap"]
                except Exception:
                    pass
            o.Visibility = x["vis"]
    g = grupos["REFLETOR_203MM"]
    g.addProperty("App::PropertyString", "MassasNaoModeladas", "V4").MassasNaoModeladas = "; ".join(
        "%s %.0f g em %s" % x for x in M.MASSAS_REFLETOR)
    doc.recompute()
    doc.saveAs(ARQ_V4)
    pr("salvo: %s (%d pecas da montagem + %d do refletor)" % (ARQ_V4, len(pecas), len(refl)))

    # ---- STL das pecas impressas (uma de cada tipo, com a quantidade)
    import MeshPart
    if os.path.isdir(PASTA_STL):
        for f in os.listdir(PASTA_STL):
            if f.lower().endswith(".stl"):
                os.remove(os.path.join(PASTA_STL, f))
    else:
        os.makedirs(PASTA_STL)
    tipos = {}
    for pc in pecas:
        if pc.impressa:
            k = re.sub(r"(_\d+)+$", "", pc.nome) if pc.nome.startswith(("PLANETA", "PORTA_PLANETAS")) else pc.nome
            tipos.setdefault(k, []).append(pc)
    pr("\nSTL (pasta STL_V4) - quantidade / massa de cada / material:")
    massa_imp = 0.0
    for k in sorted(tipos):
        lst = tipos[k]
        s = lst[0].forma.copy()
        bb = s.BoundBox
        s.translate(V(-bb.Center.x, -bb.Center.y, -bb.ZMin))
        mesh = MeshPart.meshFromShape(Shape=s, LinearDeflection=0.05, AngularDeflection=0.2, Relative=False)
        mesh.write(os.path.join(PASTA_STL, "%s_x%d.stl" % (k, len(lst))))
        massa_imp += sum(x.massa() for x in lst)
        pr("  %-24s x%-2d %6.0f g  %s" % (k, len(lst), lst[0].massa(), "100% (engrenagem)" if lst[0].mat == "petg100" else "6 paredes + 50%"))
    pr("  filamento estimado: %.2f kg (PETG)" % (massa_imp / 1000))

    if GUI:
        Gui.activeDocument().activeView().viewIsometric()
        Gui.SendMsgToActiveView("ViewFit")
        doc.save()
    pr("\ntempo total %.0f s" % (time.time() - t0))


try:
    main()
except Exception:
    pr(traceback.format_exc())
finally:
    _log.close()
    if GUI:
        os._exit(0)
