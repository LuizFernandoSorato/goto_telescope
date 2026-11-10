# -*- coding: utf-8 -*-
# Animacao do redutor V2 + saida por polias (MONTAGEM_V2) no FreeCAD.
#
# Como usar: abra MONTAGEM_V2.FCStd no FreeCAD; depois Arquivo > Abrir > este arquivo (abre no editor de macro)
# e Macro > Executar macro (Ctrl+F6). Aparece um painel a direita. Fechar o painel (botao "Fechar e restaurar")
# devolve todas as pecas a posicao original.
#
# Cinematica (coroa da CAIXA parada):
#   estagio k: sol = SOL_MOTOR (k=1) ou SOL_(k-1); suporte = SUPORTE_k (e SOL_k, que e preso nele)
#   suporte = sol / (1 + Zcoroa/Zsol); planeta: orbita com o suporte e gira (1 - Zcoroa/Zplaneta) x o suporte
#   SAIDA = SUPORTE_n; 20T gira com a SAIDA; 40T e EIXO = 20T x Z20/Z40 (mesmo sentido: correia aberta)
#   correia: os dentes andam r_primitivo(20T) x angulo da 20T ao longo do percurso
# As pecas sao giradas mexendo no Placement (as polias ficam num App::Part e o giro e convertido para o
# sistema local dele, qualquer que seja a orientacao).
import math
import re
import time

import FreeCAD as App
import Part

V = App.Vector
EIXO_Z = V(0, 0, 1)

# --- geometria GT2 (igual ao POLIAS_GT2/scripts/build_polias.py) ---
PASSO, PLD, H_DENTE_C, ESP_C = 2.0, 0.254, 0.75, 1.38
COSTA = ESP_C - H_DENTE_C - PLD
LARG, LARG_DENTES, T_FLANGE = 6.0, 7.0, 1.0
GT2 = [(0.747183, -0.5), (0.747183, 0), (0.647876, 0.037218), (0.598311, 0.130528), (0.578556, 0.238423),
       (0.547158, 0.343077), (0.504649, 0.443762), (0.451556, 0.53975), (0.358229, 0.636924), (0.2484, 0.707276),
       (0.127259, 0.750044), (0, 0.76447), (-0.127259, 0.750044), (-0.2484, 0.707276), (-0.358229, 0.636924),
       (-0.451556, 0.53975), (-0.504797, 0.443762), (-0.547291, 0.343077), (-0.578605, 0.238423),
       (-0.598311, 0.130528), (-0.648009, 0.037218), (-0.747183, 0), (-0.747183, -0.5)]
DENTE_C = [(x * 0.93, (y * H_DENTE_C / 0.76447 * 0.98) if y > 0 else (-0.3 if y < 0 else 0.0)) for x, y in GT2]


def _neg(v):
    return V(-v.x, -v.y, -v.z)


def global_pai(o):
    """Placement global do grupo geometrico (App::Part) que contem o objeto (identidade se estiver na raiz)"""
    pai = o.getParentGeoFeatureGroup()
    return global_pai(pai).multiply(pai.Placement) if pai is not None else App.Placement()


def gira_em_torno(c, ang):
    """Placement que gira 'ang' graus em torno do eixo z global que passa pelo ponto c"""
    return App.Placement(c, App.Rotation(EIXO_Z, ang)).multiply(App.Placement(_neg(c), App.Rotation()))


# ------------------------------------------------------------------ correia
class CorreiaAnimada:
    """faixa lisa fixa + dentes que correm pelo percurso (no sistema local do App::Part das polias)"""

    def __init__(self, C, z1, z2, z_base):
        self.r1, self.r2 = z1 * PASSO / (2 * math.pi), z2 * PASSO / (2 * math.pi)
        self.circs = [(V(0, 0, 0), self.r1), (V(C, 0, 0), self.r2)]
        self.segs, self.L = self._percurso(0.0)
        self.n = int(round(self.L / PASSO))
        self.passo = self.L / self.n                  # correia esticada: espalha os dentes no percurso todo
        self.s0 = self.r1 * ((math.pi - self.segs[0][3]) % (2 * math.pi))
        self.z_base = z_base
        face = self._contorno(COSTA).cut(self._contorno(-PLD))
        self.faixa = face.extrude(V(0, 0, LARG))
        self.faixa.translate(V(0, 0, z_base))
        f = Part.Face(Part.makePolygon([V(x, y, z_base) for x, y in DENTE_C] + [V(DENTE_C[0][0], DENTE_C[0][1], z_base)]))
        self.dente = f.extrude(V(0, 0, LARG))

    @staticmethod
    def _tangente(ca, ra, cb, rb):
        d = cb - ca; D = d.Length
        dh = d * (1.0 / D); dp = V(-dh.y, dh.x, 0)
        k = (ra - rb) / D
        for s in (1, -1):
            n = dh * k + dp * (s * math.sqrt(max(0.0, 1 - k * k)))
            pa = ca + n * ra; pb = cb + n * rb
            t = pb - pa
            if t.x * n.y - t.y * n.x < 0:
                return n, pa, pb
        raise RuntimeError("tangente nao encontrada")

    def _percurso(self, dr):
        cs = [(c, r + dr) for c, r in self.circs]
        m = len(cs)
        tans = [self._tangente(cs[i][0], cs[i][1], cs[(i + 1) % m][0], cs[(i + 1) % m][1]) for i in range(m)]
        segs = []
        for i in range(m):
            c, r = cs[i]
            u_in, u_out = tans[i - 1][0], tans[i][0]
            a_in, a_out = math.atan2(u_in.y, u_in.x), math.atan2(u_out.y, u_out.x)
            segs.append(("arco", c, abs(r), a_in, (a_out - a_in) % (2 * math.pi)))
            n, pa, pb = tans[i]
            segs.append(("reta", pa, pb, n))
        comp = sum((s[2] * abs(s[4])) if s[0] == "arco" else (s[2] - s[1]).Length for s in segs)
        return segs, comp

    def _contorno(self, dr):
        segs, _ = self._percurso(dr)
        e = []
        for sg in segs:
            if sg[0] == "arco":
                _, c, r, a0, sw = sg
                e.append(Part.ArcOfCircle(Part.Circle(c, EIXO_Z, r), a0, a0 + sw).toShape())
            elif (sg[2] - sg[1]).Length > 1e-6:
                e.append(Part.LineSegment(sg[1], sg[2]).toShape())
        return Part.Face(Part.Wire(Part.__sortEdges__(e)))

    def ponto(self, s):
        s %= self.L
        for sg in self.segs:
            if sg[0] == "arco":
                _, c, r, a0, sw = sg
                l = r * sw
                if s <= l:
                    a = a0 + s / r
                    u = V(math.cos(a), math.sin(a), 0)
                    return c + u * r, u
            else:
                _, pa, pb, n = sg
                l = (pb - pa).Length
                if s <= l:
                    return pa + (pb - pa) * (s / l), n
            s -= l
        return self.ponto(0)

    def forma(self, ds):
        """ds: quanto a correia andou (mm) no sentido do percurso (anti-horario no sistema local)"""
        pecas = [self.faixa]
        for i in range(self.n):
            p, n = self.ponto(self.s0 + self.passo * i + ds)
            t = V(-n.y, n.x, 0)
            d = self.dente.copy()
            d.Placement = App.Placement(p - n * PLD, App.Rotation(EIXO_Z, math.degrees(math.atan2(t.y, t.x))))
            pecas.append(d)
        return Part.makeCompound(pecas)


# ------------------------------------------------------------------ cinematica
class Cinematica:
    def __init__(self, doc):
        self.doc = doc
        rot = {o.Label: o for o in doc.Objects}

        def acha(padrao):
            return sorted((o for lb, o in rot.items() if re.fullmatch(padrao, lb)), key=lambda o: o.Label)

        self.sol_motor = acha(r"SOL_MOTOR")
        self.n_estagios = max(int(m.group(1)) for m in (re.fullmatch(r"SUPORTE_(\d+)", lb) for lb in rot) if m)
        self.suporte = {k: acha(r"SUPORTE_%d" % k) + acha(r"SOL_%d" % k) for k in range(1, self.n_estagios + 1)}
        self.planetas = {k: acha(r"PLANETA_%d_\d+" % k) for k in range(1, self.n_estagios + 1)}
        self.saida = acha(r"SAIDA")
        p20 = acha(r"POLIA_GT2_\d+T.*")
        if len(p20) != 2 or not self.saida or not self.sol_motor:
            raise RuntimeError("nao achei SOL_MOTOR / SAIDA / as 2 polias POLIA_GT2_*T na montagem")
        zs = sorted(p20, key=lambda o: int(re.match(r"POLIA_GT2_(\d+)T", o.Label).group(1)))
        self.z1 = int(re.match(r"POLIA_GT2_(\d+)T", zs[0].Label).group(1))
        self.z2 = int(re.match(r"POLIA_GT2_(\d+)T", zs[1].Label).group(1))
        self.grupo_20 = [zs[0]] + acha(r"PARAFUSO_M\d+_%dT_\d+" % self.z1)
        self.grupo_40 = [zs[1]] + acha(r"PARAFUSO_M\d+_%dT_\d+" % self.z2) + acha(r"EIXO") + acha(r"ANEL_DIN471_.*")
        self.correia_orig = (acha(r"CORREIA_GT2_.*") or [None])[0]

        # dentes das engrenagens (planilha do REDUCAO_V2)
        ss = None
        alvo = getattr(self.sol_motor[0], "LinkedObject", None)
        if alvo is not None and alvo.Document.getObject("Parametros") is not None:
            ss = alvo.Document.getObject("Parametros")
        zs_, zp_, zr_ = (12, 12, 36) if ss is None else (float(ss.get("dentes_sol")), float(ss.get("dentes_planeta")),
                                                           float(ss.get("dentes_coroa")))
        self.red_estagio = 1.0 + zr_ / zs_
        self.f_planeta = 1.0 - zr_ / zp_
        self.dentes = (zs_, zp_, zr_)

        # estado original
        self.orig = {}
        for o in self.todos():
            pai = o.getParentGeoFeatureGroup()
            pg = global_pai(o)
            self.orig[o.Name] = (o, App.Placement(o.Placement), pg.multiply(o.Placement), pg)
        g20 = self.orig[self.grupo_20[0].Name][2]
        g40 = self.orig[self.grupo_40[0].Name][2]
        self.c20 = V(g20.Base.x, g20.Base.y, 0)
        self.c40 = V(g40.Base.x, g40.Base.y, 0)
        g1 = self.orig[self.suporte[1][0].Name][2]
        self.c_red = V(g1.Base.x, g1.Base.y, 0)

        # correia animada (no sistema local do App::Part das polias)
        self.correia = None
        if self.correia_orig is not None:
            pai = self.correia_orig.getParentGeoFeatureGroup()
            self.pai_polias = pai
            p40 = zs[1].Placement.Base
            self.sinal_local = global_pai(self.correia_orig).Rotation.multVec(EIXO_Z).z
            z_base = self.correia_orig.Placement.Base.z + self.correia_orig.Shape.BoundBox.ZMin - self.correia_orig.Placement.Base.z
            self.correia = CorreiaAnimada(p40.x, self.z1, self.z2, z_base)

    def todos(self):
        objs = list(self.sol_motor) + list(self.saida) + self.grupo_20 + self.grupo_40
        for k in self.suporte:
            objs += self.suporte[k] + self.planetas[k]
        return objs

    def _poe(self, o, g_nova):
        _, _, _, pg = self.orig[o.Name]
        o.Placement = pg.inverse().multiply(g_nova)

    def _gira(self, objs, c, ang):
        r = gira_em_torno(c, ang)
        for o in objs:
            self._poe(o, r.multiply(self.orig[o.Name][2]))

    def angulos(self, motor):
        """angulos (graus) de cada peca para o motor em 'motor' graus"""
        sup = {k: motor / self.red_estagio ** k for k in range(1, self.n_estagios + 1)}
        a20 = sup[self.n_estagios]
        return dict(motor=motor, suporte=sup, a20=a20, a40=a20 * self.z1 / self.z2)

    def aplica(self, motor):
        a = self.angulos(motor)
        self._gira(self.sol_motor, self.c_red, motor)
        for k, ang in a["suporte"].items():
            self._gira(self.suporte[k], self.c_red, ang)
            orbita = gira_em_torno(self.c_red, ang)
            for p in self.planetas[k]:
                g0 = self.orig[p.Name][2]
                c0 = V(g0.Base.x, g0.Base.y, 0)
                self._poe(p, orbita.multiply(gira_em_torno(c0, ang * self.f_planeta - ang)).multiply(g0))
        self._gira(self.saida, self.c_red, a["a20"])
        self._gira(self.grupo_20, self.c20, a["a20"])
        self._gira(self.grupo_40, self.c40, a["a40"])
        return a

    def ds_correia(self, a20):
        """quanto a correia andou (mm, sistema local das polias) para a 20T em a20 graus (global)"""
        return self.correia.r1 * math.radians(self.sinal_local * a20)

    def forma_correia(self, a20):
        return self.correia.forma(self.ds_correia(a20))

    def fase_correia(self, a20, n_fases):
        """a correia se repete a cada dente: indice da fase (0..n_fases-1) mais proxima"""
        f = (self.ds_correia(a20) % self.correia.passo) / self.correia.passo
        return int(round(f * n_fases)) % n_fases

    def restaura(self):
        for o, plc, _, _ in self.orig.values():
            try:
                o.Placement = plc
            except Exception:
                pass


# ------------------------------------------------------------------ interface (so com o FreeCAD grafico)
def _painel():
    import FreeCADGui as Gui
    try:
        from PySide import QtCore, QtWidgets
    except ImportError:
        from PySide import QtCore, QtGui as QtWidgets

    PRESETS = [("Sideral", 2048 * 1440 / 1436.0682 / 1440.0),   # EIXO: 1 volta por dia sideral -> motor ~1,426 rpm
               ("60 rpm", 60.0), ("GoTo 600 rpm", 600.0), ("EIXO a 1 rpm (motor 2048)", 2048.0)]
    CARCACA = r"CAIXA|TAMPA|PLACA_SUPERIOR|NEMA17_referencia|MANCAL"
    N_FASES = 12                                        # posicoes da correia dentro de 1 dente (2 mm / 12)

    class Painel(QtWidgets.QDockWidget):
        def __init__(self, doc):
            super().__init__("Animacao do redutor")
            self.setObjectName("AnimacaoRedutorV2")
            self.doc = doc
            self.cin = Cinematica(doc)
            self.undo = doc.UndoMode
            doc.UndoMode = 0                           # sem historico de desfazer para cada quadro
            self.motor = 0.0                           # graus acumulados do motor
            self.rpm = 60.0
            self.sentido = 1.0
            self.rodando = False
            self.t_ant = None
            self.fase = None
            self.vis_orig = {}
            # correia: o desenho se repete a cada dente, entao N_FASES copias prontas (deslocadas de passo/N_FASES)
            # e so a da fase atual fica visivel -- trocar visibilidade e muito mais leve que refazer a forma
            self.fases_correia = []
            if self.cin.correia is not None:
                App.Console.PrintMessage("Animacao: preparando a correia (%d fases)...\n" % N_FASES)
                pai = self.cin.correia_orig.getParentGeoFeatureGroup()
                try:
                    cor = self.cin.correia_orig.ViewObject.ShapeColor
                except Exception:
                    cor = None
                for i in range(N_FASES):
                    o = doc.addObject("Part::Feature", "ANIM_CORREIA_%02d" % i)
                    o.Label = "ANIM_CORREIA_%02d (temporaria)" % i
                    o.Shape = self.cin.correia.forma(self.cin.correia.passo * i / N_FASES)
                    if pai is not None:
                        pai.addObject(o)
                    if cor is not None:
                        try:
                            o.ViewObject.ShapeColor = cor
                        except Exception:
                            pass
                    o.Visibility = False
                    self.fases_correia.append(o)
                self.vis_orig[self.cin.correia_orig.Name] = self.cin.correia_orig.Visibility
                self.cin.correia_orig.Visibility = False
            self.obj_correia = self.fases_correia[0] if self.fases_correia else None
            self._monta_ui()
            self.timer = QtCore.QTimer(self)
            self.timer.timeout.connect(self._quadro)
            self.timer.start(30)
            self._desenha()

        # ---- interface
        def _monta_ui(self):
            w = QtWidgets.QWidget(); lay = QtWidgets.QVBoxLayout(w)
            zs, zp, zr = self.cin.dentes
            info = QtWidgets.QLabel("%d estagios de %.0f:1 (sol %d, planeta %d, coroa %d) + polias %dT/%dT\nreducao total %.0f:1" % (
                self.cin.n_estagios, self.cin.red_estagio, zs, zp, zr, self.cin.z1, self.cin.z2,
                self.cin.red_estagio ** self.cin.n_estagios * self.cin.z2 / self.cin.z1))
            lay.addWidget(info)
            self.lb_rpm = QtWidgets.QLabel(); lay.addWidget(self.lb_rpm)
            self.sl = QtWidgets.QSlider(QtCore.Qt.Horizontal); self.sl.setRange(-100, 500)   # log10(rpm) x 100
            self.sl.valueChanged.connect(self._muda_sl); lay.addWidget(self.sl)
            grade = QtWidgets.QGridLayout()
            for i, (nome, rpm) in enumerate(PRESETS):
                b = QtWidgets.QPushButton(nome)
                b.clicked.connect(lambda _=False, r=rpm: self._poe_rpm(r))
                grade.addWidget(b, i // 2, i % 2)
            lay.addLayout(grade)
            linha = QtWidgets.QHBoxLayout()
            self.bt_play = QtWidgets.QPushButton("Iniciar"); self.bt_play.clicked.connect(self._play)
            bt_inv = QtWidgets.QPushButton("Inverter sentido"); bt_inv.clicked.connect(self._inverte)
            bt_zero = QtWidgets.QPushButton("Zerar"); bt_zero.clicked.connect(self._zera)
            for b in (self.bt_play, bt_inv, bt_zero):
                linha.addWidget(b)
            lay.addLayout(linha)
            self.cb_carc = QtWidgets.QCheckBox("Esconder carcaca (CAIXA, TAMPA, PLACA, MANCAL, motor)")
            self.cb_carc.toggled.connect(self._carcaca); lay.addWidget(self.cb_carc)
            self.cb_cor = QtWidgets.QCheckBox("Correia andando")
            self.cb_cor.setChecked(self.obj_correia is not None); self.cb_cor.setEnabled(self.obj_correia is not None)
            self.cb_cor.toggled.connect(lambda _=False: self._desenha())
            lay.addWidget(self.cb_cor)
            self.lb_est = QtWidgets.QLabel(); self.lb_est.setStyleSheet("font-family: monospace")
            lay.addWidget(self.lb_est)
            aviso = QtWidgets.QLabel("Em rotacao alta o sol do motor pode parecer parado ou girando ao contrario: "
                                     "e o efeito estroboscopico da taxa de quadros, nao um erro.\n"
                                     "Nao salve com a animacao aberta: feche abaixo para restaurar as posicoes.")
            aviso.setWordWrap(True); lay.addWidget(aviso)
            bt_fim = QtWidgets.QPushButton("Fechar e restaurar"); bt_fim.clicked.connect(self.close)
            lay.addWidget(bt_fim)
            lay.addStretch(1)
            self.setWidget(w)
            self._poe_rpm(self.rpm)
            self.cb_carc.setChecked(True)

        def _poe_rpm(self, rpm):
            self.rpm = rpm
            self.sl.blockSignals(True); self.sl.setValue(int(round(100 * math.log10(rpm)))); self.sl.blockSignals(False)
            self._texto_rpm()

        def _muda_sl(self, v):
            self.rpm = 10 ** (v / 100.0)
            self._texto_rpm()

        def _texto_rpm(self):
            eixo = self.rpm / (self.cin.red_estagio ** self.cin.n_estagios) * self.cin.z1 / self.cin.z2
            self.lb_rpm.setText("Motor: %.4g rpm   ->   EIXO: %.4g rpm (%.4g graus/s)" % (self.rpm, eixo, eixo * 6.0))

        def _play(self):
            self.rodando = not self.rodando
            self.t_ant = None
            self.bt_play.setText("Pausar" if self.rodando else "Iniciar")

        def _inverte(self):
            self.sentido = -self.sentido

        def _zera(self):
            self.motor = 0.0
            self._desenha()

        def _carcaca(self, esconder):
            for o in self.doc.Objects:
                if re.fullmatch(CARCACA, o.Label) and o.getParentGeoFeatureGroup() is None:
                    if esconder:
                        self.vis_orig.setdefault(o.Name, o.Visibility)
                        o.Visibility = False
                    elif o.Name in self.vis_orig:
                        o.Visibility = self.vis_orig[o.Name]

        # ---- animacao
        def _quadro(self):
            try:
                agora = time.monotonic()
                if self.rodando:
                    if self.t_ant is not None:
                        self.motor += self.sentido * self.rpm * 6.0 * (agora - self.t_ant)   # rpm -> graus/s
                    self.t_ant = agora
                    self._desenha()
            except Exception as e:                    # documento fechado, objeto apagado...
                App.Console.PrintWarning("Animacao parada: %s\n" % e)
                self.timer.stop()

        def _desenha(self):
            a = self.cin.aplica(self.motor)
            if self.fases_correia:
                andando = self.cb_cor.isChecked()
                fase = self.cin.fase_correia(a["a20"], N_FASES) if andando else None
                if fase != self.fase or self.cin.correia_orig.Visibility == andando:
                    for i, o in enumerate(self.fases_correia):
                        o.Visibility = (i == fase)
                    self.cin.correia_orig.Visibility = not andando
                    self.fase = fase
            linhas = ["%-10s %12.2f voltas" % ("motor", a["motor"] / 360.0)]
            for k, ang in a["suporte"].items():
                linhas.append("%-10s %12.4f voltas" % ("suporte %d" % k, ang / 360.0))
            linhas.append("%-10s %12.4f graus" % ("20T/SAIDA", a["a20"]))
            linhas.append("%-10s %12.4f graus" % ("EIXO", a["a40"]))
            linhas.append("%-10s %12.1f arcmin" % ("", a["a40"] * 60.0))
            self.lb_est.setText("\n".join(linhas))

        def closeEvent(self, ev):
            try:
                self.timer.stop()
                self.cin.restaura()
                for o in self.fases_correia:
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
                Gui.ANIMACAO_REDUTOR = None
                super().closeEvent(ev)
                self.deleteLater()

    # uma animacao por vez
    antigo = getattr(Gui, "ANIMACAO_REDUTOR", None)
    if antigo is not None:
        try:
            antigo.close()
        except Exception:
            pass
    doc = App.getDocument("MONTAGEM_V2") if "MONTAGEM_V2" in App.listDocuments() else App.ActiveDocument
    if doc is None:
        raise RuntimeError("Abra MONTAGEM_V2.FCStd antes de rodar a animacao")
    p = Painel(doc)
    Gui.getMainWindow().addDockWidget(QtCore.Qt.RightDockWidgetArea, p)
    Gui.ANIMACAO_REDUTOR = p
    return p


if App.GuiUp and globals().get("ANIM_TESTE") is not True:
    _painel()
