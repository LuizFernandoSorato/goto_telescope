# -*- coding: utf-8 -*-
# Confere a MONTAGEM_EQ_V4.FCStd: interferencias, equilibrio, esforcos nos eixos, dentes, inercia e colisoes
# no giro (RA +-135 graus x DEC volta inteira). So le o arquivo.
# Rodar:  "C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe" verifica_v4.py   (relatorio em V4_LOG, padrao %TEMP%\verifica_v4.log)
import math
import os
import sys
import tempfile
import time
import traceback

try:
    AQUI = os.path.dirname(os.path.abspath(__file__))
except NameError:
    AQUI = r"C:\LUIZ\PROJECTS\GOTO_TELESCOPE\FREECAD\MONTAGEM_EQ\scripts"
sys.path.insert(0, AQUI)
ARQ_V4 = os.environ.get("V4_ARQ", os.path.join(os.path.dirname(AQUI), "MONTAGEM_EQ_V4.FCStd"))
LOG = os.environ.get("V4_LOG", os.path.join(tempfile.gettempdir(), "verifica_v4.log"))
PASSO = float(os.environ.get("V4_PASSO", "15"))
ANGS_RA = sorted(set([-135.0 + PASSO * k for k in range(int(270 // PASSO) + 1)] + [-100.0, -95.0, 95.0, 100.0]))

import FreeCAD as App
import Part

import eq_massas as EM
import v4_modelo as M

V = App.Vector
G = 9.81
_log = open(LOG, "w", encoding="utf-8")


def pr(*a):
    _log.write(" ".join(str(x) for x in a) + "\n"); _log.flush()


def perp(v, ax):
    return v - ax * v.dot(ax)


def gira(centro, eixo, ang):
    return App.Placement(V(), App.Rotation(eixo, ang), centro)


def main():
    t0 = time.time()
    doc = App.openDocument(ARQ_V4)
    E = M.eixos()
    p, d, I = E["p"], E["d"], E["I"]
    itens = []
    for o in doc.Objects:
        if o.TypeId != "Part::Feature":
            continue
        s = EM.forma(o)
        itens.append(dict(o=o, nome=o.Label, grupo=EM.raiz(o).Label, s=s, m=o.Massa_g, conj=o.Conjunto,
                          cg=EM._cm_forma(s)))
    extras = []
    R = doc.getObject("REFLETOR_203MM")
    for nome, m, loc in M.MASSAS_REFLETOR:
        extras.append(dict(nome=nome, m=m, conj="dec", cg=R.Placement.multVec(V(*loc)), s=None))
    todos = itens + extras
    pr("%d pecas lidas de %s" % (len(itens), ARQ_V4))

    # ================================================================ 1. interferencias na posicao de estacionamento
    pr("\n== 1. Interferencias (sobreposicao > 1 mm3) na posicao de estacionamento")
    n = 0
    for i, a in enumerate(itens):
        for b in itens[i + 1:]:
            if a["grupo"] == "REFLETOR_203MM" and b["grupo"] == "REFLETOR_203MM":
                continue    # o tubo vem pronto do projeto TELESCOPE
            if not a["s"].BoundBox.intersect(b["s"].BoundBox):
                continue
            v = a["s"].common(b["s"]).Volume
            if v > 1.0:
                par = sorted((a["nome"], b["nome"]))
                ajuste = par[0].startswith("PINO") or par[1].startswith("PINO")
                pr("  %-8s %s x %s: %.1f mm3" % ("(pino)" if ajuste else "!!", par[0], par[1], v))
                n += 0 if ajuste else 1
    pr("  -> %d interferencia(s) a corrigir (os pinos de aco entram com 0,05 mm de interferencia de proposito)" % n)

    # ================================================================ 2. equilibrio
    def soma(lst):
        m = sum(x["m"] for x in lst)
        return m, sum((x["cg"] * x["m"] for x in lst), V()) * (1.0 / m)

    dec = [x for x in todos if x["conj"] == "dec"]
    ra = [x for x in todos if x["conj"] in ("ra", "dec")]
    m_dec, c_dec = soma(dec)
    m_ra, c_ra = soma(ra)
    m_tot, c_tot = soma(todos)
    off_dec = perp(c_dec - I, d)
    off_ra = perp(c_ra - I, p)
    pr("\n== 2. Equilibrio")
    pr("  DEC: %.2f kg girando; CG a %.1f mm do eixo DEC (ao longo do tubo %.1f, lateral %.1f) -> %.2f N.m" % (
        m_dec / 1000, off_dec.Length, off_dec.dot(p), off_dec.dot(V(0, 1, 0)), m_dec / 1000 * G * off_dec.Length / 1000))
    pr("  RA:  %.2f kg girando; CG a %.1f mm do eixo RA (lado do tubo %.1f, lateral %.1f) -> %.2f N.m" % (
        m_ra / 1000, off_ra.Length, off_ra.dot(d), off_ra.dot(V(0, 1, 0)), m_ra / 1000 * G * off_ra.Length / 1000))
    placa = [x for x in itens if x["nome"] == "PLACA_BASE"][0]["s"]
    furo = [f for f in placa.Faces if isinstance(f.Surface, Part.Cylinder) and abs(f.Surface.Radius - 4.9) < 0.01][0]
    pr("  total %.1f kg, CG em x = %.0f, y = %.0f (furo do tripe em x = %.0f)" % (
        m_tot / 1000, c_tot.x, c_tot.y, furo.Surface.Center.x))

    # ================================================================ 3. eixos de 20 mm e rolamentos 6004
    pr("\n== 3. Eixos de aco 20 mm (6004 com centros em z 8 e z %.0f; carga no flange da cabeca)" % (M.Z_TUBO_FIM - 6))
    L = M.Z_TUBO_FIM - 6 - 8.0
    for nome, mm, cg, ax, o_ax, fat in (("DEC (tubo na horizontal)", m_dec, c_dec, d, E["o_dec"], 1.0),
                                        ("RA", m_ra, c_ra, p, E["o_ra"], math.cos(math.radians(M.LAT)))):
        W = mm / 1000 * G * fat
        a = (cg - o_ax).dot(ax) - (M.Z_TUBO_FIM - 6)
        Mf = W * a / 1000
        sig = 32 * Mf / (math.pi * 0.020 ** 3) / 1e6
        pr("  %-25s carga %.0f N a %.0f mm do 6004 de cima -> flexao %.1f N.m, %.0f MPa | 6004: %.0f N e %.0f N (C0 = 5000 N)" % (
            nome, W, a, Mf, sig, W * (1 + a / L), W * a / L))
    W_ax = m_ra / 1000 * G * math.sin(math.radians(M.LAT))
    pr("  carga axial no RA: %.0f N (6004 aguenta ~2500 N axial)" % W_ax)
    pr("  aco 1045/prata: escoamento ~350-500 MPa, fadiga ~200 MPa")
    m_cw_lado = sum(x["m"] for x in itens if x["grupo"] == "CONTRAPESO")
    c_cw = soma([x for x in itens if x["grupo"] == "CONTRAPESO"])[1]
    Mcw = m_cw_lado / 1000 * G * ((c_cw - E["o_dec"]).dot(d) * -1) / 1000
    pr("  capa do contrapeso (presa na tampa da camara DEC por 6 M5): momento ate %.1f N.m (barra na horizontal)" % Mcw)

    # ================================================================ 4. ultimo estagio e motor
    pr("\n== 4. Transmissao (NEMA23 + 4 x 4:1 planetario + 20T/200T helicoidal = %.0f:1)" % M.REDUCAO)
    Y20, sig_adm = 0.32, 20.0     # fator de Lewis 20T; tensao admissivel de fadiga do PETG (conservador)
    F = sig_adm * M.B_H * M.MN * Y20
    T_eixo = F * M.MT * M.Z2 / 2 / 1000
    pr("  pinhao 20T PETG 100%%: forca admissivel %.0f N -> torque no eixo %.1f N.m (no pinhao %.2f N.m)" % (F, T_eixo, T_eixo / 10))
    eta = 0.9 ** 4 * 0.9
    pr("  torque de motor para %.1f N.m no eixo: %.4f N.m (rendimento %.0f%%) -> o NEMA23 (1,26 N.m) sobra MUITO:" % (
        T_eixo, T_eixo / M.REDUCAO / eta, eta * 100))
    pr("    limitar a corrente do driver: travado, o motor tem forca para quebrar os dentes")
    for rpm in (300, 600, 900):
        pr("  motor a %d rpm -> %.2f graus/s no eixo (180 graus em %.0f s)" % (rpm, rpm * 6.0 / M.REDUCAO, 180 / (rpm * 6.0 / M.REDUCAO)))
    pr("  rastreio sideral: %.2f rpm no motor; passo inteiro (1,8 graus) = %.2f segundos de arco no ceu" % (
        M.REDUCAO / 1436.07, 1.8 * 3600 / M.REDUCAO))

    # ================================================================ 5. inercia
    def inercia(lst, ax):
        t = 0.0
        for x in lst:
            t += x["m"] / 1000 * (perp(x["cg"] - I, ax).Length / 1000) ** 2
            if x["s"] is not None and x["s"].Volume > 0:
                rho = x["m"] / x["s"].Volume   # g/mm3
                for so in x["s"].Solids:
                    J = so.MatrixOfInertia
                    n = ax
                    Jn = V(J.A11 * n.x + J.A12 * n.y + J.A13 * n.z, J.A21 * n.x + J.A22 * n.y + J.A23 * n.z,
                           J.A31 * n.x + J.A32 * n.y + J.A33 * n.z)
                    t += n.dot(Jn) * rho * 1e-9
        return t
    I_dec, I_ra = inercia(dec, d), inercia(ra, p)
    pr("\n== 5. Inercia: DEC %.2f kg.m2, RA %.2f kg.m2 -> acelerar ate 1,4 graus/s em 1 s: DEC %.3f N.m, RA %.3f N.m" % (
        I_dec, I_ra, I_dec * math.radians(1.4), I_ra * math.radians(1.4)))

    # ================================================================ 6. colisoes no giro
    pr("\n== 6. Colisoes: RA de -135 a +135 graus x DEC volta inteira (passo %.0f graus)" % PASSO)
    # so o envelope externo: engrenagens, pinos, rolamentos e eixos ficam dentro das carcacas
    internas = ("PLANETA", "PINO", "PORTA_PLANETAS", "SOL_", "SAIDA_", "EIXO", "ROL_", "COROA", "PINHAO", "ESPACADOR",
                "BARRA_M5", "PORCA_LUVA", "FLANGE_EIXO")
    ext = [x for x in itens if not x["nome"].startswith(internas)]
    fixos = [x for x in ext if x["conj"] == "fixo"]
    mov_ra = [x for x in ext if x["conj"] == "ra"]
    mov_dec = [x for x in ext if x["conj"] == "dec"]
    pr("  pecas externas testadas: %d fixas, %d no RA, %d no DEC" % (len(fixos), len(mov_ra), len(mov_dec)))
    boca_l = V(0, 0, 1582)
    pl_refl = R.Placement
    boca0 = pl_refl.multVec(boca_l) - pl_refl.multVec(V())
    boca0.normalize()

    def colide(movs, plc, alvos):
        """sobreposicao de volume (> 1 mm3) entre as pecas que giram e os alvos"""
        res = []
        for x in movs:
            s = x["s"].copy(); s.Placement = plc.multiply(s.Placement)
            bb = s.BoundBox
            for y in alvos:
                if not bb.intersect(y["s"].BoundBox):
                    continue
                v = s.common(y["s"]).Volume
                if v > 1.0:
                    res.append((x["nome"], y["nome"], v))
        return res

    t = time.time()
    # (a) o que gira no RA (corpo DEC, redutor DEC, contrapeso) contra a parte fixa
    ruins_ra = []
    for H in ANGS_RA:
        r = colide(mov_ra, gira(I, p, H), fixos)
        if r:
            ruins_ra.append((H, r))
    pr("  (a) corpo DEC + contrapeso x base/RA: %s" % ("livre" if not ruins_ra else ""))
    for H, r in ruins_ra:
        pr("      RA %+5.0f: %s" % (H, "; ".join("%s x %s (%.0f mm3)" % c for c in r[:4])))
    # (b) tubo + sela contra corpo DEC/contrapeso (so depende do DEC)
    ruins_dec = []
    D = 0.0
    while D < 359.99:
        r = colide(mov_dec, gira(I, d, D), mov_ra)
        if r:
            ruins_dec.append((D, r))
        D += PASSO
    pr("  (b) tubo + sela x corpo DEC/contrapeso: %s" % ("livre" if not ruins_dec else ""))
    for D, r in ruins_dec:
        pr("      DEC %5.0f: %s" % (D, "; ".join("%s x %s (%.0f mm3)" % c for c in r[:4])))
    # (c) tubo + sela contra a parte fixa, em todas as combinacoes
    ruins = []
    abaixo = []
    for H in ANGS_RA:
        D = 0.0
        while D < 359.99:
            plc = gira(I, p, H).multiply(gira(I, d, D))
            alt = math.degrees(math.asin(max(-1, min(1, plc.Rotation.multVec(boca0).z))))
            r = colide(mov_dec, plc, fixos)
            if r:
                ruins.append((H, D, alt, r))
            D += PASSO
    pr("  (c) tubo + sela x base/RA: %d posicoes com contato (de %d)" % (len(ruins), len(ANGS_RA) * int(360 // PASSO)))
    ruim_h = set(abs(x[0]) for x in ruins)
    livre = max([h for h in ANGS_RA if h >= 0 and all(abs(k) not in ruim_h for k in ANGS_RA if abs(k) <= h)] or [0])
    pr("      -> RA livre (qualquer DEC) ate +-%.0f graus; o meridiano fica em +-90 (contrapeso na horizontal)" % livre)
    for H, D, alt, r in ruins:
        pr("      RA %+5.0f DEC %5.0f (tubo a %+3.0f graus de altura): %s" % (
            H, D, alt, "; ".join("%s x %s (%.0f mm3)" % c for c in r[:3])))
    acima = [x for x in ruins if x[2] > 0]
    pr("      -> com o tubo acima do horizonte: %d" % len(acima))
    pr("  tempo das colisoes %.0f s" % (time.time() - t))

    # (d) o tubo desce abaixo da placa de base? (o tripe fica embaixo dela)
    tubo = [x for x in itens if x["grupo"] == "REFLETOR_203MM" and x["nome"] == "TUBO001"][0]
    pior = (1e9, 0, 0)
    for H in ANGS_RA:
        D = 0.0
        while D < 359.99:
            plc = gira(I, p, H).multiply(gira(I, d, D))
            if plc.Rotation.multVec(boca0).z > 0:
                s = tubo["s"].copy(); s.Placement = plc.multiply(s.Placement)
                if s.BoundBox.ZMin < pior[0]:
                    pior = (s.BoundBox.ZMin, H, D)
            D += PASSO
    pr("  (d) ponto mais baixo do tubo apontando acima do horizonte: z = %.0f mm (RA %+.0f, DEC %.0f);"
       " a placa de base esta em z = 0, o cruzamento dos eixos em z = %.0f" % (pior[0], pior[1], pior[2], I.z))
    pr("\ntempo total %.0f s" % (time.time() - t0))
    App.closeDocument(doc.Name)


try:
    main()
except Exception:
    pr(traceback.format_exc())
finally:
    _log.close()
