# -*- coding: utf-8 -*-
# Animacao do movimento real da montagem equatorial V3 (MONTAGEM_EQ_V3.FCStd) no FreeCAD.
#
# Como usar: abra MONTAGEM_EQ_V3.FCStd; Macro > Macros... > (pasta scripts) anima_montagem.py > Executar.
# Painel a direita:
#   - escolha um alvo (estrelas e objetos do ceu do sul) e clique GoTo: os dois eixos giram na velocidade de GoTo
#     (rotacao do motor / 2048) ate apontar; depois o RA acompanha o ceu na velocidade sideral
#   - o tempo pode ser acelerado (x1 ... x3600); a hora sideral vem do relogio do PC e da longitude
#   - se o acompanhamento levar o RA alem de +-120 graus, a montagem faz o "meridian flip" (troca de lado)
#   - "ISS - passagem ...": volta o tempo para antes da passagem do TLE_ISS / PASSAGEM_ISS, espera no ponto onde a
#     ISS nasce e acompanha ate ela sumir (resumo no painel e no Report view)
#   - dentro dos redutores giram o sol do motor, os 5 estagios, as polias e a correia (2048:1)
#   - "Fechar e restaurar" devolve tudo a posicao original. NAO salve com a animacao aberta.
#
# Convencoes do modelo: +x = sul, +y = leste, +z = zenite. O eixo RA aponta para o polo sul celeste. Na posicao
# inicial (estacionamento) o tubo aponta para o polo e o contrapeso fica para baixo.
import importlib.util
import math
import re
import time

import FreeCAD as App
import Part

V = App.Vector
P = App.Placement
R = App.Rotation
Z = V(0, 0, 1)
ANIM_RED = r"C:\LUIZ\PROJECTS\GOTO_TELESCOPE\FREECAD\REDUCAO_V2\scripts\animacao_saida.py"
SIDEREO = 360.0 / 86164.0905      # graus por segundo
LIM_RA = 120.0                     # limite do eixo RA (colisao a +-150)
LON_PADRAO = -49.0                 # longitude (graus, leste positivo) -- ajuste no painel
RED_ESTAGIO, N_ESTAGIOS, F_PLANETA = 4.0, 5, 1.0 - 36.0 / 12.0

# ISS: TLE da Celestrak (celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=TLE), epoca 10/11/2026 04:12 UTC.
# Para outra passagem, cole um TLE novo (vale ~2 dias) e mude PASSAGEM_ISS (hora local do PC, qualquer minuto dentro
# da passagem).
TLE_ISS = ("1 25544U 98067A   26314.17503267  .00009346  00000+0  17575-3 0  9996",
           "2 25544  51.6322 297.6644 0007292   8.9462 351.1656 15.49289712594382")
PASSAGEM_ISS = (2026, 11, 10, 14, 55)
ANTECEDENCIA_ISS = 90.0            # s antes do nascimento: a montagem ja espera no ponto onde a ISS aparece

CATALOGO = [  # nome, AR (h, m, s), Dec (graus, ', ")  -- J2000
    ("Polo Sul celeste (estacionar)", None, None),
    ("Cruzeiro do Sul - Acrux", (12, 26, 35.9), (-63, 5, 57)),
    ("Alfa Centauri", (14, 39, 36.5), (-60, 50, 2)),
    ("Omega Centauri", (13, 26, 47.3), (-47, 28, 46)),
    ("Nebulosa de Eta Carinae", (10, 45, 3.6), (-59, 41, 4)),
    ("Canopus", (6, 23, 57.1), (-52, 41, 44)),
    ("Sirius", (6, 45, 8.9), (-16, 42, 58)),
    ("Nebulosa de Orion (M42)", (5, 35, 17.3), (-5, 23, 28)),
    ("Rigel", (5, 14, 32.3), (-8, 12, 6)),
    ("Betelgeuse", (5, 55, 10.3), (7, 24, 25)),
    ("Pleiades (M45)", (3, 47, 24.0), (24, 7, 0)),
    ("Aldebaran", (4, 35, 55.2), (16, 30, 33)),
    ("Achernar", (1, 37, 42.8), (-57, 14, 12)),
    ("Grande Nuvem de Magalhaes", (5, 23, 34.0), (-69, 45, 22)),
    ("Pequena Nuvem de Magalhaes", (0, 52, 44.8), (-72, 49, 43)),
    ("47 Tucanae", (0, 24, 5.4), (-72, 4, 53)),
    ("Fomalhaut", (22, 57, 39.0), (-29, 37, 20)),
    ("Antares", (16, 29, 24.5), (-26, 25, 55)),
    ("Spica", (13, 25, 11.6), (-11, 9, 41)),
    ("Arcturus", (14, 15, 39.7), (19, 10, 57)),
    ("Altair", (19, 50, 47.0), (8, 52, 6)),
    ("Vega", (18, 36, 56.3), (38, 47, 1)),
]


def _ar(hms):
    return 15.0 * (hms[0] + hms[1] / 60.0 + hms[2] / 3600.0)


def _dec(dms):
    s = -1.0 if dms[0] < 0 else 1.0
    return s * (abs(dms[0]) + dms[1] / 60.0 + dms[2] / 3600.0)


def _modulo_reducao():
    spec = importlib.util.spec_from_file_location("animacao_saida_mod", ANIM_RED)
    m = importlib.util.module_from_spec(spec)
    m.ANIM_TESTE = True                     # so a biblioteca, sem abrir o painel do redutor
    spec.loader.exec_module(m)
    return m


AS = _modulo_reducao()


def gp(o):
    pai = o.getParentGeoFeatureGroup()
    return P() if pai is None else gp(pai).multiply(pai.Placement)


def glob(o):
    return gp(o).multiply(o.Placement)


# Com interface, as pecas giram so na tela: muda-se o SoTransform (Coin) de cada uma, sem mexer no Placement do
# documento. Trocar o Placement de um Part::Feature custa ~40 ms (o FreeCAD reprocessa a forma); o no Coin custa ~0.
VISUAL = {"ligado": False, "nos": {}}


def _no_transf(o):
    try:
        from pivy import coin
        raiz = o.ViewObject.RootNode
        for i in range(raiz.getNumChildren()):
            c = raiz.getChild(i)
            if c.isOfType(coin.SoTransform.getClassTypeId()):
                return c
    except Exception:
        pass
    return None


def poe(o, plc):
    """coloca o objeto em plc (Placement local, relativo ao pai)"""
    if VISUAL["ligado"]:
        nos = VISUAL["nos"]
        if o.Name not in nos:
            nos[o.Name] = _no_transf(o)
        t = nos[o.Name]
        if t is not None:
            t.translation.setValue(plc.Base.x, plc.Base.y, plc.Base.z)
            t.rotation.setValue(*plc.Rotation.Q)
            t.center.setValue(0, 0, 0)
            t.scaleFactor.setValue(1, 1, 1)
            return
    o.Placement = plc


def gira(c, d, ang):
    return P(c, R(d, ang)).multiply(P(c * -1, R()))


def dif_ang(a, b):
    """a - b em (-180, 180]"""
    d = (a - b) % 360.0
    return d - 360.0 if d > 180.0 else d


def eixo_cil(s, raio=4.0):
    melhor = None
    for f in s.Faces:
        if isinstance(f.Surface, Part.Cylinder) and abs(f.Surface.Radius - raio) < 0.05 and (melhor is None or f.Area > melhor.Area):
            melhor = f
    d = V(melhor.Surface.Axis); d.normalize()
    return V(melhor.Surface.Center), d


def descendentes(raiz):
    r = []
    for o in raiz.Group:
        r.append(o)
        if o.TypeId == "App::Part":
            r += descendentes(o)
    return r


# ------------------------------------------------------------------ um redutor (dentro do seu App::Part)
class Redutor:
    def __init__(self, raiz):
        self.raiz = raiz
        g0 = glob(raiz)
        self.inv0 = g0.inverse()
        todos = descendentes(raiz)
        pecas = [o for o in todos if o.TypeId == "Part::Feature"]
        lb = lambda o, *p: o.Label.startswith(p)
        estag = [o for o in todos if o.TypeId == "App::Part" and o.Label.startswith("Estagio")]
        sup_z = lambda e: min(self.rel(o).Base.z for o in e.Group if o.Label.startswith("SUPORTE"))
        estag.sort(key=sup_z)
        assert len(estag) == N_ESTAGIOS, "%s: %d estagios" % (raiz.Label, len(estag))
        self.motor = [o for o in pecas if lb(o, "SOL_MOTOR")]
        self.suporte = [[o for o in e.Group if lb(o, "SUPORTE", "SOL", "SAIDA") and not lb(o, "SOL_MOTOR")] for e in estag]
        self.planetas = [[o for o in e.Group if lb(o, "PLANETA")] for e in estag]
        self.g20 = [o for o in pecas if lb(o, "POLIA_GT2_20T", "PARAFUSO_M3_20T")]
        self.g40 = [o for o in pecas if lb(o, "POLIA_GT2_40T", "PARAFUSO_M4_40T", "ANEL_DIN471") or re.fullmatch(r"EIXO\d*", o.Label)]
        c = self.rel([o for o in self.g40 if o.Label.startswith("POLIA_GT2_40T")][0]).Base
        self.c40 = V(c.x, c.y, 0)
        self.c20 = V(0, 0, 0)
        self.orig = {}
        for o in self.motor + sum(self.suporte, []) + sum(self.planetas, []) + self.g20 + self.g40:
            self.orig[o.Name] = (o, App.Placement(o.Placement), self.rel(o), self.relpai(o))
        cor = [o for o in pecas if lb(o, "CORREIA_GT2")]
        self.correia_orig = cor[0] if cor else None
        self.correia = None
        if self.correia_orig is not None:
            pol = self.correia_orig.getParentGeoFeatureGroup()
            self.pai_correia = pol
            self.sinal_correia = self.relpai(self.correia_orig).Rotation.multVec(Z).z
            p40 = [o for o in self.g40 if o.Label.startswith("POLIA_GT2_40T")][0]
            z1 = int(re.match(r"POLIA_GT2_(\d+)T", self.g20[0].Label).group(1)) if self.g20 else 20
            z2 = int(re.match(r"POLIA_GT2_(\d+)T", p40.Label).group(1))
            self.z1, self.z2 = z1, z2
            self.correia = AS.CorreiaAnimada(p40.Placement.Base.x, z1, z2, self.correia_orig.Shape.BoundBox.ZMin)
        else:
            self.z1, self.z2 = 20, 40
        self.reducao = RED_ESTAGIO ** N_ESTAGIOS * self.z2 / self.z1

    def rel(self, o):
        return self.inv0.multiply(glob(o))

    def relpai(self, o):
        pai = o.getParentGeoFeatureGroup()
        return self.inv0.multiply(glob(pai) if pai is not None else P())

    def _poe(self, o, rel_novo):
        _, _, _, rp = self.orig[o.Name]
        poe(o, rp.inverse().multiply(rel_novo))

    def _gira(self, objs, c, ang):
        g = gira(c, Z, ang)
        for o in objs:
            self._poe(o, g.multiply(self.orig[o.Name][2]))

    def aplica(self, a40):
        """a40: angulo (graus) do EIXO/polia 40T no quadro local do redutor"""
        a20 = a40 * self.z2 / self.z1
        sup = [a20 * RED_ESTAGIO ** (N_ESTAGIOS - 1 - k) for k in range(N_ESTAGIOS)]
        motor = a20 * RED_ESTAGIO ** N_ESTAGIOS
        self._gira(self.motor, self.c20, motor)
        for k in range(N_ESTAGIOS):
            self._gira(self.suporte[k], self.c20, sup[k])
            orb = gira(self.c20, Z, sup[k])
            for p in self.planetas[k]:
                r0 = self.orig[p.Name][2]
                c0 = V(r0.Base.x, r0.Base.y, 0)
                self._poe(p, orb.multiply(gira(c0, Z, sup[k] * F_PLANETA - sup[k])).multiply(r0))
        self._gira(self.g20, self.c20, a20)
        self._gira(self.g40, self.c40, a40)
        return dict(motor=motor, a20=a20)

    def ds_correia(self, a20):
        return self.correia.r1 * math.radians(self.sinal_correia * a20)

    def restaura(self):
        for o, plc, _, _ in self.orig.values():
            poe(o, plc)


# ------------------------------------------------------------------ montagem
class Montagem:
    def __init__(self, doc):
        self.doc = doc
        L = lambda n: doc.getObjectsByLabel(n)[0]
        self.RA, self.DEC = L("RA"), L("DEC")
        self.red_ra, self.red_dec = Redutor(self.RA), Redutor(self.DEC)
        s_ra = L("EIXO").Shape.copy(); s_ra.Placement = gp(L("EIXO")).multiply(s_ra.Placement)
        s_de = L("EIXO001").Shape.copy(); s_de.Placement = gp(L("EIXO001")).multiply(s_de.Placement)
        self.pR, self.p = eixo_cil(s_ra)
        self.pD, self.d = eixo_cil(s_de)
        if self.p.z < 0:
            self.p = self.p * -1                     # para cima = para o polo sul celeste
        # cruzamento dos eixos
        w = self.pR - self.pD; b_ = self.p.dot(self.d); d_, e_ = self.p.dot(w), self.d.dot(w)
        self.I = self.pR + self.p * ((b_ * e_ - d_) / (1 - b_ * b_))
        self.lat = -math.degrees(math.asin(self.p.z))  # hemisferio sul
        # sinal: giro local do redutor x giro do eixo da montagem
        self.s_ra = glob(self.RA).Rotation.multVec(Z).dot(self.p)
        self.s_dec = glob(self.DEC).Rotation.multVec(Z).dot(self.d)
        self.ra_mov = [self.DEC, L("ACOPLADOR1")]
        self.dec_mov = [o for o in (L("ACOPLADOR2"), L("SELA_DEC"), L("BARRA_VIXEN_200"), L("OTA_GREIKA_70070"))]
        self.orig = {o.Name: (o, App.Placement(o.Placement)) for o in self.ra_mov + self.dec_mov}
        # direcao do tubo (ocular -> objetiva) no estacionamento
        tubo = L("TUBO"); st = tubo.Shape.copy(); st.Placement = gp(tubo).multiply(st.Placement)
        cil = max((f for f in st.Faces if isinstance(f.Surface, Part.Cylinder)), key=lambda f: f.Area)
        t0 = V(cil.Surface.Axis); t0.normalize()
        ob = L("OBJETIVA"); so = ob.Shape.copy(); so.Placement = gp(ob).multiply(so.Placement)
        if (so.CenterOfMass - st.CenterOfMass).dot(t0) < 0:
            t0 = t0 * -1
        self.t0 = t0
        self.tubo = tubo
        c = V(cil.Surface.Center)                 # ponto no eixo optico; a "boca" e a frente da objetiva
        self.boca = c + t0 * max((v.Point - c).dot(t0) for v in so.Vertexes)
        # horizonte local: sul = projecao horizontal do eixo polar
        sh = V(self.p.x, self.p.y, 0); sh.normalize()
        self.sul, self.leste, self.zen = sh, Z.cross(sh), Z
        self.alfa, self.teta = 0.0, 0.0

    # ---- pose
    def aplica(self, alfa, teta):
        self.alfa, self.teta = alfa, teta
        T_ra = gira(self.pR, self.p, alfa)
        T_de = gira(self.pD, self.d, teta)
        for o in self.ra_mov:
            poe(o, T_ra.multiply(self.orig[o.Name][1]))
        for o in self.dec_mov:
            poe(o, T_ra.multiply(T_de).multiply(self.orig[o.Name][1]))
        a = self.red_ra.aplica(self.s_ra * alfa)
        b = self.red_dec.aplica(self.s_dec * teta)
        return a, b

    def apontamento(self, alfa=None, teta=None):
        alfa = self.alfa if alfa is None else alfa
        teta = self.teta if teta is None else teta
        return R(self.p, alfa).multVec(R(self.d, teta).multVec(self.t0))

    def ponto_boca(self):
        return gira(self.pR, self.p, self.alfa).multiply(gira(self.pD, self.d, self.teta)).multVec(self.boca)

    def restaura(self):
        for o, plc in self.orig.values():
            poe(o, plc)
        self.red_ra.restaura(); self.red_dec.restaura()

    # ---- ceu
    def vetor(self, H, dec):
        """direcao (global) de um astro com angulo horario H e declinacao dec (graus)"""
        H, dec, lat = math.radians(H), math.radians(dec), math.radians(self.lat)
        n = math.cos(lat) * math.sin(dec) - math.sin(lat) * math.cos(dec) * math.cos(H)
        e = -math.cos(dec) * math.sin(H)
        u = math.sin(lat) * math.sin(dec) + math.cos(lat) * math.cos(dec) * math.cos(H)
        return self.sul * -n + self.leste * e + self.zen * u

    def altaz(self, t):
        alt = math.degrees(math.asin(max(-1, min(1, t.dot(self.zen)))))
        az = math.degrees(math.atan2(t.dot(self.leste), -t.dot(self.sul))) % 360.0
        return alt, az

    def solucoes(self, t):
        """os 2 pares (alfa, teta) que apontam o tubo para t (um de cada lado do pilar)"""
        psi = math.degrees(math.acos(max(-1, min(1, self.p.dot(t)))))
        r = []
        for s in (1, -1):
            teta = s * psi
            t1 = R(self.d, teta).multVec(self.t0)
            u1 = t1 - self.p * self.p.dot(t1)
            u = t - self.p * self.p.dot(t)
            if u.Length < 1e-9 or u1.Length < 1e-9:
                alfa = 0.0
            else:
                alfa = math.degrees(math.atan2(self.p.dot(u1.cross(u)), u1.dot(u)))
            r.append((alfa, teta))
        return r

    def escolhe(self, t, lado_atual=None):
        """lado do pilar: mantem o atual enquanto o RA estiver dentro do limite; senao troca (meridian flip)"""
        sol = self.solucoes(t)
        if lado_atual is not None:
            for a, b in sol:
                if (b >= 0) == lado_atual and abs(a) <= LIM_RA:
                    return a, b
        return min(sol, key=lambda ab: abs(ab[0]))

    def vetor_enu(self, e, n, u):
        v = self.sul * -n + self.leste * e + self.zen * u
        v.normalize()
        return v

    def plano_satelite(self, sat, ps, lon, passo=1.0):
        """trajetoria de uma passagem nos eixos. Escolhe o lado do pilar em que o flip (se houver) cai com o satelite
        o mais baixo possivel, e devolve as velocidades maximas pedidas a cada eixo."""
        ts = [ps["aos"] + passo * k for k in range(int((ps["los"] - ps["aos"]) / passo) + 1)]
        vs = [self.vetor_enu(*sat.topo(t, self.lat, lon)) for t in ts]
        planos = []
        for lado in (True, False):
            cam, flips, ld = [], [], lado
            for t, v in zip(ts, vs):
                a, b = self.escolhe(v, ld)
                if (b >= 0) != ld:
                    flips.append((t, self.altaz(v)[0]))
                    ld = b >= 0
                cam.append((t, a, b))
            vra = vde = 0.0
            for (t0, a0, b0), (t1, a1, b1) in zip(cam, cam[1:]):
                if (b0 >= 0) == (b1 >= 0):
                    vra = max(vra, abs(a1 - a0) / (t1 - t0))
                    vde = max(vde, abs(dif_ang(b1, b0)) / (t1 - t0))
            custo = max([alt for _, alt in flips] + [-90.0])
            planos.append(dict(lado=lado, caminho=cam, flips=flips, v_ra=vra, v_dec=vde, custo=custo))
        return min(planos, key=lambda p: (p["custo"], len(p["flips"])))


def hora_sideral(unix, lon):
    jd = unix / 86400.0 + 2440587.5
    return (280.46061837 + 360.98564736629 * (jd - 2451545.0) + lon) % 360.0


# ------------------------------------------------------------------ satelite (ISS)
MU, RT, J2, ACH = 398600.4418, 6378.137, 1.08262668e-3, 1.0 / 298.257223563


class Satelite:
    """Propagacao simplificada de um TLE: Kepler + efeitos seculares do J2 (no de ascensao e perigeu) + arrasto (ndot).
    Para a ISS, a menos de 1 dia da epoca, o erro fica em alguns km (~1 grau numa passagem alta). Para apontar o
    telescopio de verdade use SGP4 completo."""

    def __init__(self, l1, l2):
        ano = int(l1[18:20]); ano += 2000 if ano < 57 else 1900
        self.epoca = _utc(ano, 1, 1) + (float(l1[20:32]) - 1) * 86400
        self.ndot2 = float(l1[33:43])                              # rev/dia^2 (o TLE guarda ndot/2)
        self.i = math.radians(float(l2[8:16]))
        self.raan0 = math.radians(float(l2[17:25]))
        self.e = float("0." + l2[26:33].strip())
        self.w0 = math.radians(float(l2[34:42]))
        self.M0 = math.radians(float(l2[43:51]))
        self.n = float(l2[52:63])                                  # rev/dia
        n = self.n * 2 * math.pi / 86400.0
        self.a = (MU / n ** 2) ** (1.0 / 3.0)
        p = self.a * (1 - self.e ** 2)
        k = 1.5 * J2 * (RT / p) ** 2 * n
        self.draan = -k * math.cos(self.i)
        self.dw = 0.5 * k * (5 * math.cos(self.i) ** 2 - 1)

    def eci(self, unix):
        dt = unix - self.epoca; td = dt / 86400.0
        M = self.M0 + 2 * math.pi * (self.n * td + self.ndot2 * td * td)
        a = self.a * (self.n / (self.n + 2 * self.ndot2 * td)) ** (2.0 / 3.0)
        E = M
        for _ in range(10):
            E -= (E - self.e * math.sin(E) - M) / (1 - self.e * math.cos(E))
        nu = 2 * math.atan2(math.sqrt(1 + self.e) * math.sin(E / 2), math.sqrt(1 - self.e) * math.cos(E / 2))
        r = a * (1 - self.e * math.cos(E))
        u = self.w0 + self.dw * dt + nu
        O = self.raan0 + self.draan * dt
        ci, si = math.cos(self.i), math.sin(self.i)
        return (r * (math.cos(O) * math.cos(u) - math.sin(O) * math.sin(u) * ci),
                r * (math.sin(O) * math.cos(u) + math.cos(O) * math.sin(u) * ci),
                r * math.sin(u) * si)

    def topo(self, unix, lat, lon, h=0.0):
        """(leste, norte, cima) em km, do observador ate o satelite"""
        x, y, z = self.eci(unix)
        g = math.radians(hora_sideral(unix, 0.0))
        xe, ye = x * math.cos(g) + y * math.sin(g), -x * math.sin(g) + y * math.cos(g)
        f, l = math.radians(lat), math.radians(lon)
        e2 = ACH * (2 - ACH)
        N = RT / math.sqrt(1 - e2 * math.sin(f) ** 2)
        ox, oy, oz = (N + h) * math.cos(f) * math.cos(l), (N + h) * math.cos(f) * math.sin(l), (N * (1 - e2) + h) * math.sin(f)
        dx, dy, dz = xe - ox, ye - oy, z - oz
        return (-math.sin(l) * dx + math.cos(l) * dy,
                -math.sin(f) * math.cos(l) * dx - math.sin(f) * math.sin(l) * dy + math.cos(f) * dz,
                math.cos(f) * math.cos(l) * dx + math.cos(f) * math.sin(l) * dy + math.sin(f) * dz)

    def altaz(self, unix, lat, lon):
        e, n, u = self.topo(unix, lat, lon)
        d = math.sqrt(e * e + n * n + u * u)
        return math.degrees(math.asin(u / d)), math.degrees(math.atan2(e, n)) % 360.0, d

    def passagem(self, perto, lat, lon, janela=3600.0):
        """passagem (alt > 0) mais proxima do instante 'perto' (unix): dict com aos/tca/los e alturas"""
        alt = lambda t: self.altaz(t, lat, lon)[0]
        ts = [perto - janela + 10 * k for k in range(int(2 * janela / 10) + 1)]
        vis = [t for t in ts if alt(t) > 0]
        if not vis:
            return None
        grupos, g = [], [vis[0]]
        for t in vis[1:]:
            if t - g[-1] > 15:
                grupos.append(g); g = [t]
            else:
                g.append(t)
        grupos.append(g)
        g = min(grupos, key=lambda g: 0 if g[0] <= perto <= g[-1] else min(abs(g[0] - perto), abs(g[-1] - perto)))

        def borda(t_fora, t_dentro):
            for _ in range(30):
                m = 0.5 * (t_fora + t_dentro)
                if alt(m) > 0:
                    t_dentro = m
                else:
                    t_fora = m
            return t_dentro
        aos, los = borda(g[0] - 10, g[0]), borda(g[-1] + 10, g[-1])
        a, b = aos, los
        for _ in range(60):                                       # maximo por secao aurea
            c, d = b - 0.618 * (b - a), a + 0.618 * (b - a)
            if alt(c) > alt(d):
                b = d
            else:
                a = c
        tca = 0.5 * (a + b)
        r = dict(aos=aos, tca=tca, los=los)
        for k in ("aos", "tca", "los"):
            r["alt_" + k], r["az_" + k], r["dist_" + k] = self.altaz(r[k], lat, lon)
        return r


def _utc(ano, mes, dia, h=0, m=0, s=0.0):
    """instante unix de uma data/hora UTC"""
    import calendar
    return calendar.timegm((ano, mes, dia, h, m, 0, 0, 0, 0)) + s


def _local(ano, mes, dia, h=0, m=0, s=0.0):
    """instante unix de uma data/hora no fuso do PC"""
    return time.mktime((ano, mes, dia, h, m, 0, 0, 0, -1)) + s


def _rumo(az):
    return ("N", "NE", "L", "SE", "S", "SO", "O", "NO")[int(((az + 22.5) % 360) // 45)]


# ------------------------------------------------------------------ painel (FreeCAD com interface)
def _painel():
    import FreeCADGui as Gui
    try:
        from PySide import QtCore, QtWidgets
    except ImportError:
        from PySide import QtCore, QtGui as QtWidgets
    N_FASES = 12
    CARCACA = r"(CAIXA|TAMPA|MANCAL|PLACA_SUPERIOR|NEMA17_referencia)\d*"

    class Painel(QtWidgets.QDockWidget):
        def __init__(self, doc):
            super().__init__("Movimento da montagem")
            self.setObjectName("AnimacaoMontagemEQ")
            self.doc = doc
            self.m = Montagem(doc)
            VISUAL["ligado"] = True
            VISUAL["nos"] = {}
            self.undo = doc.UndoMode
            doc.UndoMode = 0
            self.t_sim = time.time()
            self.t_ant = None
            self.alvo = None                 # (nome, ar, dec) ou None; ("ISS", None, None) para o satelite
            self.iss = None
            self.ant_eixos = None
            self.rastreio = False
            self.manual = (0, 0)
            self.lado = None
            self.desejado = (0.0, 0.0)
            self.vis_orig = {}
            self.criados = []
            # correias animadas (fases prontas)
            self.fases = []
            for red in (self.m.red_ra, self.m.red_dec):
                lista = []
                if red.correia is not None:
                    try:
                        cor = red.correia_orig.ViewObject.ShapeColor
                    except Exception:
                        cor = None
                    for i in range(N_FASES):
                        o = doc.addObject("Part::Feature", "ANIM_CORREIA_%s_%02d" % (red.raiz.Name, i))
                        o.Label = "ANIM_CORREIA_%s_%02d (temporaria)" % (red.raiz.Label, i)
                        o.Shape = red.correia.forma(red.correia.passo * i / N_FASES)
                        red.pai_correia.addObject(o)
                        if cor is not None:
                            try:
                                o.ViewObject.ShapeColor = cor
                            except Exception:
                                pass
                        o.Visibility = False
                        lista.append(o); self.criados.append(o)
                    self.vis_orig[red.correia_orig.Name] = red.correia_orig.Visibility
                    red.correia_orig.Visibility = False
                self.fases.append(lista)
            self.fase = [None, None]
            self.linha = doc.addObject("Part::Feature", "ANIM_ALVO")
            self.linha.Label = "ANIM_ALVO (temporario)"
            self.criados.append(self.linha)
            try:
                self.linha.ViewObject.ShapeColor = (1.0, 0.85, 0.1)
                self.linha.ViewObject.LineWidth = 2
            except Exception:
                pass
            self.linha.Visibility = False
            self._monta_ui()
            self.timer = QtCore.QTimer(self)
            self.timer.timeout.connect(self._quadro)
            self.timer.start(40)
            self._desenha(0.0)

        # ---- interface
        def _monta_ui(self):
            w = QtWidgets.QWidget(); lay = QtWidgets.QVBoxLayout(w)
            lay.addWidget(QtWidgets.QLabel("Latitude do modelo: %.2f graus (eixo RA para o polo sul)" % self.m.lat))
            f = QtWidgets.QFormLayout()
            self.cb_alvo = QtWidgets.QComboBox()
            for nome, _, _ in CATALOGO:
                self.cb_alvo.addItem(nome)
            self.cb_alvo.insertItem(1, "ISS - passagem de %02d/%02d %02d:%02d" % (PASSAGEM_ISS[2:0:-1] + PASSAGEM_ISS[3:5]))
            f.addRow("Alvo:", self.cb_alvo)
            self.sp_lon = QtWidgets.QDoubleSpinBox(); self.sp_lon.setRange(-180, 180); self.sp_lon.setDecimals(2)
            self.sp_lon.setValue(LON_PADRAO); self.sp_lon.setSuffix(" graus (leste +)")
            f.addRow("Longitude:", self.sp_lon)
            self.cb_acel = QtWidgets.QComboBox()
            for a in (1, 10, 60, 300, 1200, 3600):
                self.cb_acel.addItem("x%d" % a, a)
            self.cb_acel.setCurrentIndex(0)
            f.addRow("Tempo:", self.cb_acel)
            self.sp_rpm = QtWidgets.QDoubleSpinBox(); self.sp_rpm.setRange(10, 3000); self.sp_rpm.setValue(600)
            self.sp_rpm.setSuffix(" rpm no motor")
            f.addRow("Velocidade de GoTo:", self.sp_rpm)
            lay.addLayout(f)
            linha = QtWidgets.QHBoxLayout()
            b = QtWidgets.QPushButton("GoTo"); b.clicked.connect(self._goto); linha.addWidget(b)
            self.bt_rastreio = QtWidgets.QPushButton("Parar acompanhamento"); self.bt_rastreio.clicked.connect(self._rastreio)
            linha.addWidget(self.bt_rastreio)
            b = QtWidgets.QPushButton("Estacionar"); b.clicked.connect(self._estaciona); linha.addWidget(b)
            lay.addLayout(linha)
            grade = QtWidgets.QGridLayout()
            for txt, d, pos in (("RA -", (-1, 0), (1, 0)), ("RA +", (1, 0), (1, 2)), ("DEC +", (0, 1), (0, 1)), ("DEC -", (0, -1), (2, 1))):
                bb = QtWidgets.QPushButton(txt)
                bb.pressed.connect(lambda d=d: self._manual(d))
                bb.released.connect(lambda: self._manual((0, 0)))
                grade.addWidget(bb, *pos)
            grade.addWidget(QtWidgets.QLabel("manual\n(segure)"), 1, 1)
            lay.addLayout(grade)
            self.cb_carc = QtWidgets.QCheckBox("Ver engrenagens (esconde as carcacas dos redutores)")
            self.cb_carc.toggled.connect(self._carcaca); lay.addWidget(self.cb_carc)
            self.cb_cor = QtWidgets.QCheckBox("Correias andando")
            self.cb_cor.setChecked(bool(self.fases[0] or self.fases[1])); lay.addWidget(self.cb_cor)
            self.lb = QtWidgets.QLabel(); self.lb.setStyleSheet("font-family: monospace"); lay.addWidget(self.lb)
            aviso = QtWidgets.QLabel("Velocidade real de GoTo: %.2f graus/s no eixo com 600 rpm no motor. Acelere o tempo para "
                                     "ver o acompanhamento sideral (x1200: 1 hora em 3 s).\nNao salve com a animacao aberta."
                                     % (600 * 6.0 / self.m.red_ra.reducao))
            aviso.setWordWrap(True); lay.addWidget(aviso)
            b = QtWidgets.QPushButton("Fechar e restaurar"); b.clicked.connect(self.close); lay.addWidget(b)
            lay.addStretch(1)
            self.setWidget(w)

        def _goto(self):
            i = self.cb_alvo.currentIndex()
            if i == 1:
                self._goto_iss(); return
            nome, ar, dec = CATALOGO[i - 1 if i > 1 else i]
            if self.iss is not None:
                self.t_sim = time.time()          # saindo da passagem da ISS: volta para a hora atual
            self.iss = None
            if ar is None:
                self._estaciona(); return
            self.alvo = (nome, _ar(ar), _dec(dec))
            self.rastreio = True
            # lado do pilar escolhido na partida (o de menor giro no RA); so troca no meridian flip
            t = self.m.vetor(dif_ang(hora_sideral(self.t_sim, self.sp_lon.value()), self.alvo[1]), self.alvo[2])
            self.lado = self.m.escolhe(t)[1] >= 0
            self.bt_rastreio.setText("Parar acompanhamento")

        def _goto_iss(self):
            m, lon = self.m, self.sp_lon.value()
            sat = Satelite(*TLE_ISS)
            ps = sat.passagem(_local(*PASSAGEM_ISS), m.lat, lon)
            if ps is None:
                App.Console.PrintWarning("ISS: nenhuma passagem perto de %s nesta longitude\n" % (PASSAGEM_ISS,))
                return
            plano = m.plano_satelite(sat, ps, lon)
            self.iss = dict(sat=sat, ps=ps, plano=plano)
            self.alvo = ("ISS", None, None)
            self.rastreio = True
            self.lado = plano["lado"]
            self.t_sim = ps["aos"] - ANTECEDENCIA_ISS
            self.cb_acel.setCurrentIndex(0)
            self.bt_rastreio.setText("Parar acompanhamento")
            h = lambda t: time.strftime("%H:%M:%S", time.localtime(t))
            rpm = lambda v: v * m.red_ra.reducao / 6.0
            txt = ["ISS, passagem de %s (lat %.2f, lon %.2f):" % (time.strftime("%d/%m/%Y", time.localtime(ps["aos"])), m.lat, lon)]
            for k, nome in (("aos", "nasce"), ("tca", "maximo"), ("los", "some")):
                txt.append("  %-7s %s  alt %4.1f  az %5.1f (%s)  %5.0f km" % (nome, h(ps[k]), ps["alt_" + k], ps["az_" + k],
                                                                         _rumo(ps["az_" + k]), ps["dist_" + k]))
            txt.append("  velocidade maxima: RA %.2f graus/s (motor %.0f rpm), DEC %.2f graus/s (motor %.0f rpm); GoTo: %.2f graus/s"
                       % (plano["v_ra"], rpm(plano["v_ra"]), plano["v_dec"], rpm(plano["v_dec"]), self.sp_rpm.value() * 6.0 / m.red_ra.reducao))
            if plano["flips"]:
                for t, alt in plano["flips"]:
                    txt.append("  meridian flip as %s com a ISS a %.0f graus de altura (perde a ISS por ~1-2 min)" % (h(t), alt))
            else:
                txt.append("  sem meridian flip: a passagem inteira cabe num lado do pilar")
            self.iss["resumo"] = txt
            App.Console.PrintMessage("\n".join(txt) + "\n")

        def _rastreio(self):
            if self.alvo is None:
                return
            self.rastreio = not self.rastreio
            self.bt_rastreio.setText("Parar acompanhamento" if self.rastreio else "Retomar acompanhamento")
            if not self.rastreio:
                self.desejado = (self.m.alfa, self.m.teta)

        def _estaciona(self):
            self.alvo = None; self.rastreio = False; self.lado = None; self.iss = None
            self.desejado = (0.0, 0.0)

        def _manual(self, d):
            self.manual = d
            if d != (0, 0):
                self.rastreio = False
                self.bt_rastreio.setText("Retomar acompanhamento")

        def _carcaca(self, ver):
            for o in self.doc.Objects:
                if re.fullmatch(CARCACA, o.Label) and o.getParentGeoFeatureGroup() is not None and \
                        self._raiz(o) in (self.m.RA, self.m.DEC):
                    if ver:
                        self.vis_orig.setdefault(o.Name, o.Visibility); o.Visibility = False
                    elif o.Name in self.vis_orig:
                        o.Visibility = self.vis_orig[o.Name]

        @staticmethod
        def _raiz(o):
            pai = o.getParentGeoFeatureGroup()
            while pai is not None and pai.getParentGeoFeatureGroup() is not None:
                pai = pai.getParentGeoFeatureGroup()
            return pai

        # ---- animacao
        def _quadro(self):
            try:
                agora = time.monotonic()
                dt = 0.0 if self.t_ant is None else min(agora - self.t_ant, 0.2)
                self.t_ant = agora
                self._desenha(dt * self.cb_acel.currentData())
            except Exception as e:
                App.Console.PrintWarning("Animacao parada: %s\n" % e)
                self.timer.stop()

        def _desenha(self, dt):
            m = self.m
            self.t_sim += dt
            lst = hora_sideral(self.t_sim, self.sp_lon.value())
            vel = self.sp_rpm.value() * 6.0 / m.red_ra.reducao          # graus/s no eixo
            estado = "parado"
            t = None
            fase_iss = None
            if self.alvo is not None:
                nome, ar, dec = self.alvo
                if self.iss is not None:
                    ps, sat = self.iss["ps"], self.iss["sat"]
                    e_, n_, u_ = sat.topo(self.t_sim, m.lat, self.sp_lon.value())
                    t = m.vetor_enu(e_, n_, u_)
                    self.iss["dist"] = math.sqrt(e_ * e_ + n_ * n_ + u_ * u_)
                    fase_iss = "antes" if self.t_sim < ps["aos"] else ("depois" if self.t_sim > ps["los"] else "durante")
                else:
                    t = m.vetor(dif_ang(lst, ar), dec)
                alt, az = m.altaz(t)
                if self.rastreio and fase_iss == "antes":
                    # espera no ponto onde a ISS vai nascer
                    v0 = m.vetor_enu(*sat.topo(ps["aos"], m.lat, self.sp_lon.value()))
                    self.desejado = m.escolhe(v0, self.lado)
                    estado = "esperando a ISS nascer a %s (faltam %.0f s)" % (_rumo(ps["az_aos"]), ps["aos"] - self.t_sim)
                elif self.rastreio and fase_iss == "depois":
                    estado = "a ISS se pos a %s" % _rumo(ps["az_los"])
                    self.desejado = (m.alfa, m.teta)
                elif self.rastreio:
                    if alt < 0:
                        estado = "%s abaixo do horizonte" % nome
                        self.desejado = (m.alfa, m.teta)
                    else:
                        a, b = m.escolhe(t, self.lado)
                        if self.lado is not None and (b >= 0) != self.lado:
                            estado = "meridian flip"
                        self.desejado = (a, b)
            if self.manual != (0, 0):
                self.desejado = (max(-LIM_RA, min(LIM_RA, m.alfa + self.manual[0] * vel * dt)), m.teta + self.manual[1] * vel * dt)
                estado = "manual"
            # move os eixos com velocidade limitada
            da = self.desejado[0] - m.alfa
            db = dif_ang(self.desejado[1], m.teta)
            passo = vel * dt
            alfa = m.alfa + max(-passo, min(passo, da))
            teta = m.teta + max(-passo, min(passo, db))
            alfa = max(-LIM_RA, min(LIM_RA, alfa))
            mov = abs(da) > passo + 1e-9 or abs(db) > passo + 1e-9
            if self.alvo is not None and self.rastreio and estado not in ("manual",) and "abaixo" not in estado \
                    and fase_iss in (None, "durante"):
                if mov:
                    estado = estado if estado == "meridian flip" else "GoTo: %s" % self.alvo[0]
                else:
                    estado = "acompanhando %s" % self.alvo[0]
                    self.lado = self.desejado[1] >= 0
            if self.alvo is None and not mov and self.manual == (0, 0):
                estado = "estacionado" if abs(alfa) < 1e-6 and abs(teta) < 1e-6 else "parado"
            elif self.alvo is None and mov:
                estado = "indo para o estacionamento"
            ra, de = m.aplica(alfa, teta)
            # correias
            for k, red in enumerate((m.red_ra, m.red_dec)):
                lista = self.fases[k]
                if not lista:
                    continue
                andando = self.cb_cor.isChecked()
                a20 = (ra if k == 0 else de)["a20"]
                f = int(round((red.ds_correia(a20) % red.correia.passo) / red.correia.passo * N_FASES)) % N_FASES if andando else None
                if f != self.fase[k] or red.correia_orig.Visibility == andando:
                    for i, o in enumerate(lista):
                        o.Visibility = (i == f)
                    red.correia_orig.Visibility = not andando
                    self.fase[k] = f
            # linha do alvo
            if t is not None:
                ini = m.ponto_boca() + t * 20
                self.linha.Shape = Part.makeCylinder(1.0, 1500, ini, t).fuse(Part.makeSphere(15, ini + t * 1500))
                self.linha.Visibility = True
            else:
                self.linha.Visibility = False
            # texto
            ap = m.apontamento()
            alt_t, az_t = m.altaz(ap)
            hs = lst / 15.0
            linhas = ["%-10s %s" % ("estado", estado),
                      "%-10s %s  (hora sideral %02d:%02d)" % ("hora", time.strftime("%d/%m %H:%M:%S", time.localtime(self.t_sim)),
                                                              int(hs), int((hs % 1) * 60)),
                      "%-10s alt %6.1f  az %6.1f" % ("tubo", alt_t, az_t)]
            if t is not None:
                erro = math.degrees(math.acos(max(-1, min(1, ap.dot(t)))))
                alt, az = m.altaz(t)
                extra = "dist %5.0f km" % self.iss["dist"] if self.iss is not None else "H %+7.2f h" % (dif_ang(lst, self.alvo[1]) / 15.0)
                linhas.append("%-10s alt %6.1f  az %6.1f  %s  erro %.3f graus" % ("alvo", alt, az, extra, erro))
            # velocidade dos eixos (graus/s de tempo simulado) e rotacao dos motores
            if self.ant_eixos is not None and dt > 0:
                w_ra, w_de = (alfa - self.ant_eixos[0]) / dt, dif_ang(teta, self.ant_eixos[1]) / dt
            else:
                w_ra = w_de = 0.0
            self.ant_eixos = (alfa, teta)
            rpm = lambda w: w * m.red_ra.reducao / 6.0
            linhas.append("%-10s %+8.2f graus  %+6.3f graus/s  motor %+10.1f voltas %+6.0f rpm" % (
                "eixo RA", alfa, w_ra, ra["motor"] / 360.0, rpm(w_ra)))
            linhas.append("%-10s %+8.2f graus  %+6.3f graus/s  motor %+10.1f voltas %+6.0f rpm" % (
                "eixo DEC", teta, w_de, de["motor"] / 360.0, rpm(w_de)))
            if self.iss is not None:
                linhas += [""] + self.iss["resumo"]
            self.lb.setText("\n".join(linhas))

        def closeEvent(self, ev):
            try:
                self.timer.stop()
                self.m.restaura()
                VISUAL["ligado"] = False
                VISUAL["nos"] = {}
                for o in self.criados:
                    try:
                        self.doc.removeObject(o.Name)
                    except Exception:
                        pass
                for nome, vis in self.vis_orig.items():
                    o = self.doc.getObject(nome)
                    if o is not None:
                        o.Visibility = vis
                self.doc.UndoMode = self.undo
                self.doc.recompute()
            finally:
                Gui.ANIMACAO_MONTAGEM = None
                super().closeEvent(ev)
                self.deleteLater()

    antigo = getattr(Gui, "ANIMACAO_MONTAGEM", None)
    if antigo is not None:
        try:
            antigo.close()
        except Exception:
            pass
    doc = App.ActiveDocument
    for nome in App.listDocuments():
        if nome.startswith("MONTAGEM_EQ_V3"):
            doc = App.getDocument(nome)
    if doc is None or not doc.getObjectsByLabel("SELA_DEC"):
        raise RuntimeError("Abra MONTAGEM_EQ_V3.FCStd antes de rodar a animacao")
    App.Console.PrintMessage("Animacao da montagem: preparando as correias (~20 s)...\n")
    try:
        from PySide import QtGui
        QtGui.QGuiApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
    except Exception:
        QtGui = None
    try:
        p = Painel(doc)
    finally:
        if QtGui is not None:
            QtGui.QGuiApplication.restoreOverrideCursor()
    Gui.getMainWindow().addDockWidget(QtCore.Qt.RightDockWidgetArea, p)
    Gui.ANIMACAO_MONTAGEM = p
    return p


if App.GuiUp and globals().get("ANIM_TESTE") is not True:
    _painel()
