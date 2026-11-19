# -*- coding: utf-8 -*-
# Montagem equatorial V4 (reforcada) para o refletor 203 mm f/1600 (~9,7 kg).
# Gera todas as pecas por script (Part::Feature). Usado por build_v4.py (gera e salva) e verifica_v4.py (confere).
#
# Convencoes globais: +x = sul, +y = leste, +z = zenite; topo da placa de base em z = 0.
# Cada modulo de eixo (RA e DEC) tem o seu quadro local: z ao longo do eixo (z = 0 na face externa da tampa da
# camara da coroa, +z para a cabeca), x para o lado do redutor.
import math
import os

import FreeCAD as App
import Part

V = App.Vector
P = App.Placement
R = App.Rotation
Z = V(0, 0, 1)

# ======================================================================= parametros
LAT = float(os.environ.get("LAT", "28.5"))

# redutor planetario (por eixo): NEMA23 + 4 estagios 12/12/36 -> 4^4 = 256:1
M_PL, ZS, ZP, ZR = 1.25, 12, 12, 36
B_PL = 10.0                       # largura das engrenagens planetarias
R_PL = M_PL * (ZS + ZP) / 2       # raio dos pinos = distancia sol-planeta (15 mm)
N_EST = 4
HA_SOL, HA_COROA, X_PLANETA, HF, RF = 0.95, 0.55, -0.08, 1.35, 0.2   # mesmos coeficientes testados na V2
D_PINO = 6.0                      # pinos de aco dos planetas
L_NEMA = 56.0                     # NEMA23 57x56 (1,26 N.m)
M_NEMA23 = 700.0                  # g

# ultimo estagio: pinhao 20T + coroa 200T helicoidais -> 10:1 (total 2560:1)
MN, BETA, Z1, Z2, B_H = 0.8, 15.0, 20, 200, 18.0
MT = MN / math.cos(math.radians(BETA))
ALFA_T = math.degrees(math.atan(math.tan(math.radians(20)) / math.cos(math.radians(BETA))))
A_H = MT * (Z1 + Z2) / 2 + 0.05   # distancia entre eixos pinhao-coroa (+0,05 de folga)
REDUCAO = (1 + ZR / ZS) ** N_EST * Z2 / Z1

# modulo de eixo
R_EIXO = 10.0                     # eixo de aco 20 mm
ROL_EXT, ROL_LARG = 21.0, 12.0    # 6004: 20 x 42 x 12
R_CAM_IN, R_CAM_OUT = 86.0, 96.0  # camara da coroa
R_LOBO_IN, R_LOBO_OUT = 14.0, 46.0
T_TAMPA = 14.0                    # tampa da camara (com o 6004 de baixo)
Z_DECK, T_DECK = 66.0, 10.0       # teto da camara
Z_TUBO_FIM = 206.0                # fim do tubo de rolamentos (6004 de cima em 194..206)
R_TUBO, R_FURO_TUBO = 35.0, 12.0
Z_ENG = 24.0                      # coroa e pinhao em Z_ENG .. Z_ENG + B_H
Z_CABECA = 232.0                  # face do flange da cabeca (onde a proxima peca aparafusa)
PCD_FLANGE = 46.0

# montagem
Z_PIV = 45.0                      # pivo de latitude no modulo RA (centro da camara)
Z_LAT = 120.0                     # apoio do parafuso de latitude no tubo do RA (abaixo do alcance do corpo DEC)
H_PIV = 125.0                     # altura do pivo acima da placa de base
H_BOSS = 80.0                     # bloco do DEC: distancia do eixo DEC a face no flange do RA (afasta tubo e barra do garfo)
Z_I = 150.0                       # cruzamento dos eixos, no quadro do DEC
L_BARRA_CW = 450.0
M_CONTRAPESO = 5000.0             # g, contrapeso comercial (furo 20 mm)
R_CP, H_CP = 56.0, 70.0
D_ANEIS = 360.0                   # distancia entre os aneis (simetricos no CG do tubo; o de tras nao pode passar sobre a camara do RA)
L_LOSMANDY = 380.0                # barra curta: acaba antes da camara do RA quando o tubo passa por cima dela
M_ANEL = 600.0                    # g, anel de aluminio CNC para tubo de 8" (par ~1,2 kg)
H_SELA = 36.0                     # base da sela (alta: afasta o tubo do lobulo do redutor RA quando ele passa por baixo)

# refletor: densidades das pecas modeladas no projeto TELESCOPE e massas que nao estao modeladas (Z local do tubo)
DENS_REFL = {"TUBO001": 1.40, "TAMPA INFERIOR": 0.70, "SUPORTE PRIMARIO": 0.70}
MASSAS_REFLETOR = [("espelho primario", 2000.0, (0, 0, 48)), ("espelho secundario", 60.0, (0, 0, 1444)),
                   ("ocular + buscadora", 600.0, (180, 0, 1440))]


def dens_refl(label):
    return DENS_REFL.get(label, 7.85 if label.startswith(("PARAFUSO", "ARRUELA", "PORCA", "MOLA")) else 1.0)

# densidades (g/cm3)
PETG = 0.90                       # PETG ~70% efetivo (6 paredes + 50% gyroid)
ACO, ALU = 7.85, 2.70
CORES = {"impresso": (0.95, 0.55, 0.15), "impresso2": (0.25, 0.45, 0.75), "engrenagem": (0.92, 0.92, 0.88),
         "aco": (0.72, 0.73, 0.75), "alu": (0.80, 0.82, 0.85), "motor": (0.15, 0.15, 0.17), "rolamento": (0.55, 0.57, 0.6),
         "contrapeso": (0.2, 0.2, 0.22), "losmandy": (0.75, 0.15, 0.15)}


# ======================================================================= utilitarios
def cil(r, h, z0=0.0, x=0.0, y=0.0):
    return Part.makeCylinder(r, h, V(x, y, z0), Z)


def anel(ro, ri, h, z0=0.0, x=0.0, y=0.0):
    return cil(ro, h, z0, x, y).cut(cil(ri, h + 2, z0 - 1, x, y))


def caixa(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def quadrado_chanfrado(meio, ch, h, z0, x=0.0, y=0.0):
    a = meio - ch
    pts = [(-a, -meio), (a, -meio), (meio, -a), (meio, a), (a, meio), (-a, meio), (-meio, a), (-meio, -a)]
    w = Part.makePolygon([V(x + px, y + py, z0) for px, py in pts] + [V(x + pts[0][0], y + pts[0][1], z0)])
    return Part.Face(w).extrude(V(0, 0, h))


def contorno(rc, rl, a, h, z0):
    s = cil(rc, h, z0).fuse(cil(rl, h, z0, x=a)).fuse(caixa(0, a, -rl, rl, z0, z0 + h))
    return s.removeSplitter()


def furos_pcd(r_furo, pcd, h, z0, n=4, ang0=45.0, x=0.0, y=0.0):
    s = None
    for k in range(n):
        a = math.radians(ang0 + 360.0 * k / n)
        c = cil(r_furo, h, z0, x + pcd / 2 * math.cos(a), y + pcd / 2 * math.sin(a))
        s = c if s is None else s.fuse(c)
    return s


def oblongo(r, comp, h, z0, x, y):
    """furo oblongo ao longo de x (ajuste do engrenamento)"""
    return cil(r, h, z0, x - comp / 2, y).fuse(cil(r, h, z0, x + comp / 2, y)).fuse(
        caixa(x - comp / 2, x + comp / 2, y - r, y + r, z0, z0 + h))


def quadro(origem, xdir, zdir):
    """Placement de um quadro local (x, y = z ^ x, z)"""
    x = V(xdir); x.normalize(); z = V(zdir); z.normalize(); y = z.cross(x)
    m = App.Matrix(x.x, y.x, z.x, origem.x, x.y, y.y, z.y, origem.y, x.z, y.z, z.z, origem.z, 0, 0, 0, 1)
    return P(m)


# ---------------------------------------------------------------- engrenagens (perfil evolvente do FreeCAD)
_doc_tmp = None


_cache_perfis = {}


def perfil(z, m, ext=True, x=0.0, ha=1.0, alfa=20.0):
    k = (z, m, ext, x, ha, alfa)
    if k not in _cache_perfis:
        _cache_perfis[k] = _perfil(*k)
    return _cache_perfis[k].copy()


def _perfil(z, m, ext=True, x=0.0, ha=1.0, alfa=20.0):
    import InvoluteGearFeature as IG
    global _doc_tmp
    if _doc_tmp is None:
        try:
            _doc_tmp = App.newDocument("perfis_tmp", hidden=True)
        except TypeError:
            _doc_tmp = App.newDocument("perfis_tmp")
    o = _doc_tmp.addObject("Part::Part2DObjectPython", "g")
    IG._InvoluteGear(o)
    o.NumberOfTeeth = z; o.Modules = m; o.PressureAngle = alfa; o.ExternalGear = ext; o.HighPrecision = False
    o.AddendumCoefficient = ha; o.DedendumCoefficient = HF; o.RootFilletCoefficient = RF; o.ProfileShiftCoefficient = x
    _doc_tmp.recompute()
    w = o.Shape.copy()
    _doc_tmp.removeObject(o.Name)
    return w


def fecha_tmp():
    global _doc_tmp
    if _doc_tmp is not None:
        App.closeDocument(_doc_tmp.Name)
        _doc_tmp = None


def reta(z, m, h, z0, ext=True, x=0.0, ha=1.0, rot=0.0, cx=0.0, cy=0.0):
    w = perfil(z, m, ext, x, ha)
    w.rotate(V(), Z, rot)
    s = Part.Face(w).extrude(V(0, 0, h))
    s.translate(V(cx, cy, z0))
    return s


def helicoidal(z, mao, h, z0, rot=0.0, cx=0.0, cy=0.0):
    """engrenagem helicoidal (mn = MN, beta = BETA); mao = +1 direita, -1 esquerda"""
    w = perfil(z, MT, True, 0.0, 1.0, ALFA_T)
    r = MT * z / 2
    tw = mao * math.degrees(h * math.tan(math.radians(BETA)) / r)
    secs = []
    for k in range(3):
        s = w.copy(); s.rotate(V(), Z, rot + tw * k / 2); s.translate(V(cx, cy, z0 + h * k / 2)); secs.append(s)
    return Part.makeLoft(secs, True, False)


def _melhor(func, passos):
    """func(r) -> volume de sobreposicao; devolve o meio da maior faixa sem sobreposicao (ou o minimo)"""
    vols = [func(r) for r in passos]
    zero = [v < 1e-3 for v in vols]
    melhor, ini = None, None
    for i, z in enumerate(zero + [False]):
        if z and ini is None:
            ini = i
        if not z and ini is not None:
            if melhor is None or i - ini > melhor[1] - melhor[0]:
                melhor = (ini, i)
            ini = None
    if melhor:
        return passos[(melhor[0] + melhor[1] - 1) // 2], 0.0
    i = min(range(len(vols)), key=lambda j: vols[j])
    return passos[i], vols[i]


# resultado de fases_engrenamento() (leva ~100 s; rode de novo se mudar modulo, numero de dentes ou coeficientes)
FASES = {"sol": 0.0, "planeta": 15.0, "coroa": 0.0, "pinhao": 9.0, "coroa_200": 0.0}


def fases_engrenamento():
    """rotacoes de cada perfil para os dentes encaixarem (testadas por sobreposicao de secoes de 1 mm)"""
    sol = reta(ZS, M_PL, 1, 0, ha=HA_SOL)
    rp, vp = _melhor(lambda r: sol.common(reta(ZP, M_PL, 1, 0, x=X_PLANETA, rot=r, cy=R_PL)).Volume,
                     [i * 0.75 for i in range(40)])
    pl = reta(ZP, M_PL, 1, 0, x=X_PLANETA, rot=rp, cy=R_PL)
    rc, vc = _melhor(lambda r: pl.cut(reta(ZR, M_PL, 1, 0, ext=False, ha=HA_COROA, rot=r)).Volume,
                     [i * 0.25 for i in range(40)])
    w = perfil(Z2, MT, True, 0.0, 1.0, ALFA_T)
    coroa = Part.Face(w).extrude(V(0, 0, 1))
    wp = perfil(Z1, MT, True, 0.0, 1.0, ALFA_T)

    def pinhao(r):
        s = wp.copy(); s.rotate(V(), Z, r); s.translate(V(A_H, 0, 0))
        return Part.Face(s).extrude(V(0, 0, 1))
    caixa_c = caixa(A_H - 15, A_H, -15, 15, -1, 2)
    coroa = coroa.common(caixa_c)
    rh, vh = _melhor(lambda r: coroa.common(pinhao(r)).Volume, [i * 0.5 for i in range(36)])
    return {"sol": 0.0, "planeta": rp, "coroa": rc, "pinhao": rh, "coroa_200": 0.0,
            "sobreposicao": (vp, vc, vh)}


def rolamento(de, di, b, z0, x=0.0, y=0.0):
    return anel(de / 2, di / 2, b, z0, x, y)


# ======================================================================= pecas
class Peca:
    def __init__(self, nome, forma, mat, cor, grupo, massa=None, impressa=False, conjunto="fixo"):
        self.nome, self.forma, self.mat, self.cor, self.grupo = nome, forma, mat, cor, grupo
        self.massa_fixa, self.impressa, self.conjunto = massa, impressa, conjunto

    def massa(self):
        if self.massa_fixa is not None:
            return self.massa_fixa
        return self.forma.Volume / 1000.0 * {"petg": PETG, "aco": ACO, "alu": ALU, "petg100": 1.27,
                                              "losmandy": 1.7}[self.mat]


def redutor(pecas, grupo, conj_corpo, conj_saida, rot_fase):
    """redutor V4 no quadro do modulo, com o eixo do pinhao em (A_H, 0); motor para -z"""
    a = A_H
    ca = rot_fase
    # TAMPA_V4: 60 x 80 x 18, com 2 x 608 e orelhas oblongas
    t = caixa(a - 30, a + 30, -40, 40, -18, 0)
    t = t.cut(cil(11.0, 16, -18, a)).cut(cil(6.0, 3, -2.5, a))
    for sx in (-1, 1):
        for sy in (-1, 1):
            t = t.cut(cil(3.2, 12, -18, a + sx * 23.57, sy * 23.57))                # insertos M5 das barras
            t = t.cut(oblongo(2.75, 3.0, 20, -19, a + sx * 15, sy * 34.5))           # M5 para a tampa da camara
    pecas.append(Peca("TAMPA_REDUTOR", t, "petg", "impresso2", grupo, impressa=True, conjunto=conj_corpo))
    # CAIXA_V4 com a coroa interna 36T
    z_cx0, z_cx1 = -87.0, -18.0
    c = quadrado_chanfrado(30, 6, z_cx1 - z_cx0, z_cx0, a)
    coroa = reta(ZR, M_PL, z_cx1 - z_cx0 + 2, z_cx0 - 1, ext=False, ha=HA_COROA, rot=ca["coroa"], cx=a)
    c = c.cut(coroa)
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = c.cut(cil(2.75, 80, -90, a + sx * 23.57, sy * 23.57))
    pecas.append(Peca("CAIXA_REDUTOR", c, "petg", "impresso2", grupo, impressa=True, conjunto=conj_corpo))
    # FLANGE do motor
    f = quadrado_chanfrado(30, 6, 10, -97, a).cut(cil(19.25, 2, -97, a)).cut(cil(9.0, 12, -98, a))
    for sx in (-1, 1):
        for sy in (-1, 1):
            f = f.cut(cil(2.75, 14, -99, a + sx * 23.57, sy * 23.57))
    pecas.append(Peca("FLANGE_MOTOR", f, "petg", "impresso2", grupo, impressa=True, conjunto=conj_corpo))
    # NEMA23 (referencia)
    mt = quadrado_chanfrado(28.5, 4, L_NEMA, -97 - L_NEMA, a).fuse(cil(19.05, 1.6, -97, a)).fuse(cil(4.0, 21, -97, a))
    for sx in (-1, 1):
        for sy in (-1, 1):
            mt = mt.cut(cil(2.55, L_NEMA + 4, -99 - L_NEMA, a + sx * 23.57, sy * 23.57))
    pecas.append(Peca("NEMA23", mt, None, "motor", grupo, massa=M_NEMA23, conjunto=conj_corpo))
    # barras roscadas M5 (4x)
    for sx in (-1, 1):
        for sy in (-1, 1):
            pecas.append(Peca("BARRA_M5", cil(2.5, 92, -104, a + sx * 23.57, sy * 23.57), "aco", "aco", grupo, conjunto=conj_corpo))
    # sol do motor
    s = reta(ZS, M_PL, B_PL, -86, ha=HA_SOL, rot=ca["sol"], cx=a).fuse(cil(7.0, 6, -92, a)).cut(cil(4.1, 20, -95, a))
    pecas.append(Peca("SOL_MOTOR", s, "petg100", "engrenagem", grupo, impressa=True, conjunto=conj_corpo))
    # estagios
    for k in range(1, N_EST + 1):
        zp = -86.0 + 16.0 * (k - 1)
        for j in range(3):
            ang = math.radians(90 + 120 * j)
            px, py = a + R_PL * math.cos(ang), R_PL * math.sin(ang)
            pl = reta(ZP, M_PL, B_PL, zp, x=X_PLANETA, rot=ca["planeta"] + 120 * j, cx=px, cy=py)
            pl = pl.cut(cil(D_PINO / 2 + 0.1, B_PL + 2, zp - 1, px, py))
            pecas.append(Peca("PLANETA_%d_%d" % (k, j + 1), pl, "petg100", "engrenagem", grupo, impressa=True, conjunto=conj_corpo))
            pecas.append(Peca("PINO_%d_%d" % (k, j + 1), cil(D_PINO / 2, 14.5, zp, px, py), "aco", "aco", grupo, conjunto=conj_corpo))
        if k < N_EST:
            zc = zp + 11.0
            sup = cil(20.0, 4, zc, a).fuse(reta(ZS, M_PL, 11.0, zc + 4 - 0.01, ha=HA_SOL, rot=ca["sol"], cx=a))
            for j in range(3):
                ang = math.radians(90 + 120 * j)
                sup = sup.cut(cil(D_PINO / 2 - 0.05, 3.5, zc - 0.01, a + R_PL * math.cos(ang), R_PL * math.sin(ang)))
            pecas.append(Peca("PORTA_PLANETAS_%d" % k, sup, "petg100", "engrenagem", grupo, impressa=True, conjunto=conj_corpo))
    # saida: porta-planetas do estagio 4 (8 mm) preso no eixo do pinhao
    zs = -27.0
    sa = cil(20.0, 8, zs, a).cut(cil(4.1, 10, zs - 1, a))
    for j in range(3):
        ang = math.radians(90 + 120 * j)
        sa = sa.cut(cil(D_PINO / 2 - 0.05, 4.5, zs - 0.01, a + R_PL * math.cos(ang), R_PL * math.sin(ang)))
    pecas.append(Peca("SAIDA_REDUTOR", sa, "petg100", "engrenagem", grupo, impressa=True, conjunto=conj_corpo))
    # eixo do pinhao (aco 8 mm) e rolamentos 608 (2 na tampa do redutor, 1 no teto da camara)
    pecas.append(Peca("EIXO_PINHAO", cil(4.0, 100, -27, a), "aco", "aco", grupo, conjunto=conj_corpo))
    for z0 in (-16.0, -9.0, Z_DECK):
        pecas.append(Peca("ROL_608", rolamento(22, 8, 7, z0, a), None, "rolamento", grupo, massa=12.0, conjunto=conj_corpo))
    # pinhao 20T helicoidal (mao esquerda)
    pin = helicoidal(Z1, -1, B_H, Z_ENG, rot=ca["pinhao"], cx=a).cut(cil(4.1, B_H + 2, Z_ENG - 1, a))
    pecas.append(Peca("PINHAO_20T", pin, "petg100", "engrenagem", grupo, impressa=True, conjunto=conj_corpo))


def modulo_eixo(pecas, papel, conj_corpo, conj_eixo, coroa_pronta, fases):
    """modulo RA ou DEC no seu quadro local"""
    g = papel
    a = A_H
    # ---- CORPO: camara da coroa + teto + tubo dos rolamentos + nervuras
    cam = contorno(R_CAM_OUT, R_LOBO_OUT, a, Z_DECK + T_DECK - T_TAMPA, T_TAMPA)
    cam = cam.cut(contorno(R_CAM_IN, R_LOBO_IN, a, Z_DECK - T_TAMPA, T_TAMPA - 0.01))
    tubo = cil(R_TUBO, Z_TUBO_FIM - Z_DECK - T_DECK + 0.01, Z_DECK + T_DECK - 0.01)
    corpo = cam.fuse(tubo)
    for ang in (45, 135, 225, 315):
        tri = Part.Face(Part.makePolygon([V(R_TUBO - 2, -4, 0), V(85, -4, 0), V(R_TUBO - 2, -4, 55), V(R_TUBO - 2, -4, 0)]))
        nerv = tri.extrude(V(0, 8, 0))
        nerv.translate(V(0, 0, Z_DECK + T_DECK - 0.01))
        nerv.rotate(V(), Z, ang)
        corpo = corpo.fuse(nerv)
    if papel == "RA":
        # bossas do pivo de latitude (eixo y local) e apoio do parafuso de latitude
        for sy in (-1, 1):
            b = Part.makeCylinder(22, 24, V(0, sy * 88, Z_PIV), V(0, sy, 0))
            corpo = corpo.fuse(b)
        corpo = corpo.fuse(caixa(-47, -30, -16, 16, Z_LAT - 16, Z_LAT + 16))
    else:
        # bloco que aparafusa no flange da cabeca do RA (face em x = -H_BOSS; o redutor fica do outro lado, em +x)
        corpo = corpo.fuse(caixa(-H_BOSS, 0, -35, 35, Z_I - 40, Z_I + 40))
    corpo = corpo.removeSplitter()
    # furos
    corpo = corpo.cut(cil(R_FURO_TUBO, Z_TUBO_FIM + 10, Z_DECK - 1))                    # passagem do eixo
    corpo = corpo.cut(cil(ROL_EXT, ROL_LARG + 1, Z_TUBO_FIM - ROL_LARG))                 # 6004 de cima
    corpo = corpo.cut(cil(11.0, 7.03, Z_DECK - 0.01, a)).cut(cil(6.0, 12, Z_DECK + 6, a))  # 608 do pinhao
    for k in range(8):
        ang = math.radians(22.5 + 45 * k)
        corpo = corpo.cut(cil(2.8, 12, T_TAMPA - 0.01, 91 * math.cos(ang), 91 * math.sin(ang)))   # insertos M4
    if papel == "RA":
        for sy in (-1, 1):
            corpo = corpo.cut(Part.makeCylinder(7.0, 20, V(0, sy * 113, Z_PIV), V(0, -sy, 0)))      # inserto M10
    else:
        for dy in (-16.26, 16.26):
            for dz in (-16.26, 16.26):
                corpo = corpo.cut(Part.makeCylinder(3.2, 14, V(-H_BOSS - 1, dy, Z_I + dz), V(1, 0, 0)))  # insertos M5 (furos do flange: 5,5)
    pecas.append(Peca("CORPO_" + papel, corpo, "petg", "impresso", g, impressa=True, conjunto=conj_corpo))
    # ---- TAMPA DA CAMARA (com o 6004 de baixo)
    tp = contorno(R_CAM_OUT, R_LOBO_OUT, a, T_TAMPA, 0)
    tp = tp.cut(cil(ROL_EXT, ROL_LARG + 0.01, 2)).cut(cil(16.0, 3, -1)).cut(cil(7.0, T_TAMPA + 2, -1, a))
    for k in range(8):
        ang = math.radians(22.5 + 45 * k)
        x, y = 91 * math.cos(ang), 91 * math.sin(ang)
        tp = tp.cut(cil(2.25, T_TAMPA + 2, -1, x, y)).cut(cil(4.25, 4, -1, x, y))
    for sx in (-1, 1):
        for sy in (-1, 1):
            tp = tp.cut(cil(3.2, 10, -0.01, a + sx * 15, sy * 34.5))           # insertos M5 do redutor
    if papel == "DEC":
        for k in range(6):
            ang = math.radians(30 + 60 * k)
            tp = tp.cut(cil(3.2, 10, -0.01, 37 * math.cos(ang), 37 * math.sin(ang)))   # insertos M5 da capa do contrapeso
    pecas.append(Peca("TAMPA_CAMARA_" + papel, tp, "petg", "impresso", g, impressa=True, conjunto=conj_corpo))
    # ---- eixo, rolamentos, espacadores, flanges, coroa
    pecas.append(Peca("EIXO_20_" + papel, cil(R_EIXO, Z_CABECA - 2, 2), "aco", "aco", g, conjunto=conj_eixo))
    pecas.append(Peca("ROL_6004", rolamento(42, 20, 12, 2), None, "rolamento", g, massa=69.0, conjunto=conj_eixo))
    pecas.append(Peca("ROL_6004", rolamento(42, 20, 12, Z_TUBO_FIM - 12), None, "rolamento", g, massa=69.0, conjunto=conj_eixo))
    pecas.append(Peca("ESPACADOR_20", anel(14, 10.1, 2, 14), "petg100", "impresso2", g, impressa=True, conjunto=conj_eixo))
    pecas.append(Peca("ESPACADOR_20", anel(14, 10.1, 2, Z_TUBO_FIM), "petg100", "impresso2", g, impressa=True, conjunto=conj_eixo))
    fl = anel(30, 10, 8, 16).fuse(anel(18, 10, 16, 24)).cut(furos_pcd(2.75, PCD_FLANGE, 10, 15))
    pecas.append(Peca("FLANGE_EIXO_20", fl, "alu", "alu", g, conjunto=conj_eixo))
    fl = anel(18, 10, 16, Z_TUBO_FIM + 2).fuse(anel(30, 10, 8, Z_CABECA - 8)).cut(furos_pcd(2.75, PCD_FLANGE, 10, Z_CABECA - 9))
    pecas.append(Peca("FLANGE_EIXO_20", fl, "alu", "alu", g, conjunto=conj_eixo))
    cr = coroa_pronta.copy()
    pecas.append(Peca("COROA_200T", cr, "petg100", "engrenagem", g, impressa=True, conjunto=conj_eixo))
    # ---- redutor
    redutor(pecas, g, conj_corpo, conj_eixo, fases)


def coroa_200(rot):
    c = helicoidal(Z2, +1, B_H, Z_ENG, rot=rot)
    c = c.cut(cil(18.3, B_H + 2, Z_ENG - 1)).cut(furos_pcd(2.75, PCD_FLANGE, B_H + 2, Z_ENG - 1))
    for k in range(6):
        ang = math.radians(30 + 60 * k)
        c = c.cut(cil(13.0, B_H + 2, Z_ENG - 1, 55 * math.cos(ang), 55 * math.sin(ang)))
    return c


# ======================================================================= geometria global
def eixos():
    c, s = math.cos(math.radians(LAT)), math.sin(math.radians(LAT))
    p = V(c, 0, s)                 # eixo RA (para o polo sul celeste)
    d = V(-s, 0, c)                # eixo DEC no estacionamento (para o lado do tubo)
    piv = V(0, 0, H_PIV)
    o_ra = piv - p * Z_PIV
    I = o_ra + p * (Z_CABECA + H_BOSS)
    pl_ra = quadro(o_ra, d, p)                       # x local do RA = d (redutor para cima/norte), y local = -y global
    o_dec = I - d * Z_I
    pl_dec = quadro(o_dec, p, d)                     # x local do DEC = p (redutor longe do RA), y local = leste
    pl_sela = pl_dec.multiply(P(V(), R(Z, 90)))      # sela: y local = -p (ao longo do tubo), x local = leste
    return dict(p=p, d=d, piv=piv, I=I, pl_ra=pl_ra, pl_dec=pl_dec, pl_sela=pl_sela, o_ra=o_ra, o_dec=o_dec)


def base(pecas, E, x_tripe=190.0):
    """placa de base (aluminio), garfo com o pivo de latitude e torre do parafuso de latitude (coordenadas globais).
    x_tripe: posicao do furo 3/8" do tripe (debaixo do CG do conjunto)"""
    p, d = E["p"], E["d"]
    g = "BASE"
    x0, x1 = min(-80.0, x_tripe - 70), max(200.0, x_tripe + 70)
    placa = caixa(x0, x1, -140, 140, -10, 0).cut(Part.makeCylinder(4.9, 12, V(x_tripe, 0, -11), Z))
    for sx in (-1, 1):
        for sy in (-1, 1):
            placa = placa.cut(Part.makeCylinder(3.2, 12, V(x_tripe + sx * 45, sy * 45, -11), Z))   # M6 para o adaptador do tripe
    pecas.append(Peca("PLACA_BASE", placa, "alu", "alu", g))
    for sy in (-1, 1):
        y0 = 113.0 if sy > 0 else -131.0
        ch = caixa(-55, 55, y0, y0 + 18, 0, H_PIV).fuse(Part.makeCylinder(55, 18, V(0, y0, H_PIV), V(0, 1, 0)))
        # pe virado para dentro (debaixo da camara do RA): a placa fica estreita e o tubo passa mais longe dela
        yi0, yi1 = (y0 - 30, y0 + 18) if sy > 0 else (y0, y0 + 48)
        ch = ch.fuse(caixa(-55, 55, yi0, yi1, 0, 14)).removeSplitter()
        ch = ch.cut(Part.makeCylinder(5.25, 30, V(0, y0 - 5, H_PIV), V(0, 1, 0)))
        for xx in (-45, 45):
            for yy in ((y0 - 15, y0 + 9) if sy > 0 else (y0 + 9, y0 + 33)):
                ch = ch.cut(cil(3.3, 16, -1, xx, yy))
        pecas.append(Peca("GARFO_" + ("L" if sy > 0 else "O"), ch, "petg", "impresso", g, impressa=True))
        pecas.append(Peca("PARAFUSO_PIVO_M10", Part.makeCylinder(5.0, 45, V(0, sy * 140, H_PIV), V(0, -sy, 0)), "aco", "aco", g))
    # torre do parafuso de latitude: empurra o apoio do RA (z local Z_LAT, face em x local -47) ao longo de d
    apoio = E["o_ra"] + p * Z_LAT - d * 47.0
    topo = apoio - d * 30.0
    tor = caixa(topo.x - 22, topo.x + 22, -20, 20, 0, topo.z + 40)
    corte = Part.makeBox(300, 300, 300, V(-150, -150, 0))
    corte.Placement = quadro(topo, V(0, 1, 0), d)
    tor = tor.cut(corte)
    furo = Part.makeCylinder(5.25, 200, topo - d * 150, d)
    tor = tor.cut(furo).cut(cil(3.3, 14, -1, topo.x, 0))
    pecas.append(Peca("TORRE_LATITUDE", tor.removeSplitter(), "petg", "impresso", g, impressa=True))
    pecas.append(Peca("PARAFUSO_LATITUDE_M10", Part.makeCylinder(5.0, 100, apoio - d * 100, d), "aco", "aco", g))
    return apoio


def sela_e_tubo(pecas, E, refl_rot, z_cg_tubo, desliza=0.0):
    """sela Losmandy, barra e aneis no quadro da sela (E['pl_sela']: x = leste, y = -p, z = d) e o Placement do refletor.
    desliza: deslocamento do tubo ao longo dele (mm)"""
    g = "SELA"
    z0 = Z_CABECA
    base_s = caixa(-55, 55, -70, 70, z0, z0 + H_SELA)
    for dx in (-16.26, 16.26):
        for dy in (-16.26, 16.26):
            base_s = base_s.cut(cil(3.3, H_SELA + 2, z0 - 1, dx, dy)).cut(cil(5.6, 7, z0 + H_SELA - 6, dx, dy))
    # mordente fixo (lado -x) com a face a 15 graus
    zb = z0 + H_SELA
    w_bar = 76.2; inc = math.tan(math.radians(15))
    mf = Part.Face(Part.makePolygon([V(-55, -70, zb), V(-w_bar / 2 - 0.3, -70, zb), V(-w_bar / 2 - 0.3 + 8 * inc, -70, zb + 8),
                                     V(-55, -70, zb + 8), V(-55, -70, zb)])).extrude(V(0, 140, 0))
    # batente (lado +x) com insertos M8: os manipulos atravessam e empurram o mordente movel contra a barra
    bat = caixa(55, 67, -70, 70, z0, zb + 14)
    sela = base_s.fuse(mf).fuse(bat).removeSplitter()
    for dy in (-35, 35):
        sela = sela.cut(Part.makeCylinder(5.6, 14, V(68, dy, zb + 5), V(-1, 0, 0)))
    pecas.append(Peca("SELA_LOSMANDY", sela, "petg", "impresso", g, impressa=True, conjunto="dec"))
    x_m = 52.0
    mm = Part.Face(Part.makePolygon([V(x_m, -60, zb), V(w_bar / 2 + 0.3, -60, zb), V(w_bar / 2 + 0.3 - 10 * inc, -60, zb + 10),
                                     V(x_m, -60, zb + 10), V(x_m, -60, zb)])).extrude(V(0, 120, 0))
    pecas.append(Peca("MORDENTE_LOSMANDY", mm, "petg", "impresso", g, impressa=True, conjunto="dec"))
    for dy in (-35, 35):
        pecas.append(Peca("MANIPULO_M8", Part.makeCylinder(4.0, 30, V(x_m + 30, dy, zb + 5), V(-1, 0, 0)).fuse(
            Part.makeCylinder(12, 12, V(x_m + 42, dy, zb + 5), V(-1, 0, 0))), "aco", "aco", g, conjunto="dec"))
    # barra Losmandy (trapezio) ao longo de y local (= ao longo do tubo)
    h_bar = 15.0
    w_top = w_bar - 2 * h_bar * inc
    sec = Part.Face(Part.makePolygon([V(-w_bar / 2, 0, zb), V(w_bar / 2, 0, zb), V(w_top / 2, 0, zb + h_bar),
                                      V(-w_top / 2, 0, zb + h_bar), V(-w_bar / 2, 0, zb)]))
    barra = sec.extrude(V(0, L_LOSMANDY, 0)); barra.translate(V(0, -L_LOSMANDY / 2 + desliza, 0))
    pecas.append(Peca("BARRA_LOSMANDY_%d" % L_LOSMANDY, barra, "losmandy", "losmandy", g, conjunto="dec"))
    # aneis do tubo
    r_tubo = 128.0
    z_eixo = zb + h_bar + 12 + 10 + r_tubo         # eixo do tubo no quadro do DEC
    for za in (z_cg_tubo - D_ANEIS / 2, z_cg_tubo + D_ANEIS / 2):
        yy = -(za - z_cg_tubo) + desliza          # y local = -p
        an = Part.makeCylinder(r_tubo + 10, 20, V(0, yy - 10, z_eixo), V(0, 1, 0)).cut(
            Part.makeCylinder(r_tubo, 22, V(0, yy - 11, z_eixo), V(0, 1, 0)))
        bloco = caixa(-25, 25, yy - 10, yy + 10, zb + h_bar, z_eixo - r_tubo - 5)
        an = an.fuse(bloco.cut(Part.makeCylinder(r_tubo + 2, 22, V(0, yy - 11, z_eixo), V(0, 1, 0))))
        pecas.append(Peca("ANEL_TUBO_256", an, None, "alu", g, massa=M_ANEL, conjunto="dec"))
    # refletor: eixo do tubo em (x=0, z=z_eixo) no quadro do DEC, CG (Z local z_cg_tubo) sobre o eixo DEC
    s_tubo = z_eixo - Z_I
    origem = E["I"] + E["d"] * s_tubo - E["p"] * (z_cg_tubo + desliza)
    pl_refl = P(origem, refl_rot)
    return s_tubo, pl_refl


def contrapeso(pecas, z_centros):
    g = "CONTRAPESO"
    cap = cil(45, 30, -30).cut(cil(10.0, 22, -31)).cut(cil(16.5, 1.2, -1.2))
    for k in range(6):
        ang = math.radians(30 + 60 * k)
        x, y = 37 * math.cos(ang), 37 * math.sin(ang)
        cap = cap.cut(cil(2.75, 32, -31, x, y)).cut(cil(5.0, 22, -31, x, y))
    pecas.append(Peca("CAPA_CONTRAPESO", cap, "petg100", "impresso", g, impressa=True, conjunto="ra"))
    pecas.append(Peca("PORCA_LUVA_M12", cil(9.5, 20, -30), "aco", "aco", g, conjunto="ra"))
    pecas.append(Peca("BARRA_CONTRAPESO_20", cil(10.0, L_BARRA_CW, -30 - L_BARRA_CW), "aco", "aco", g, conjunto="ra"))
    pecas.append(Peca("TRAVA_PONTA", anel(16, 10.1, 12, -30 - L_BARRA_CW), "aco", "aco", g, conjunto="ra"))
    for k, zc in enumerate(z_centros):
        pecas.append(Peca("CONTRAPESO_5KG", anel(R_CP, 10.25, H_CP, zc - H_CP / 2), None, "contrapeso", g,
                          massa=M_CONTRAPESO, conjunto="ra"))
