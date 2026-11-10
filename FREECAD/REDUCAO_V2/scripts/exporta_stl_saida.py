# Exporta os STLs das pecas impressas da saida por polias (TAMPA, SAIDA, MANCAL, PLACA_SUPERIOR, pilares e espacadores)
# Rodar com: & "C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe" exporta_stl_saida.py
import FreeCAD as App, Part, MeshPart, os

V = App.Vector; P = App.Placement; R = App.Rotation
D = r"C:\LUIZ\PROJECTS\GOTO_TELESCOPE\FREECAD\REDUCAO_V2"
SD = os.path.join(D, "STL")
pd = App.openDocument(os.path.join(D, "REDUCAO_V2.FCStd"))
doc = App.openDocument(os.path.join(D, "MONTAGEM_V2.FCStd"))
pd.recompute(); doc.recompute()

# (documento, objeto, quantidade, virar de cabeca para baixo?)
pecas = [(pd, "TAMPA", "TAMPA", 1, False), (pd, "SAIDA", "SAIDA", 1, False),
         (doc, "Body", "MANCAL", 1, False), (doc, "PLACA_SUPERIOR", "PLACA_SUPERIOR", 1, True),
         (doc, "ESPACADOR_PLACA", "ESPACADOR_PLACA", 4, False),
         (doc, "ESPACADOR_608_2_6", "ESPACADOR_608_2_6", 1, False), (doc, "ESPACADOR_608_1_0", "ESPACADOR_608_1_0", 2, False)]
for d, nome, rotulo, qtd, virar in pecas:
    s = d.getObject(nome).Shape.copy()
    s.Placement = P()
    if virar:
        s.rotate(V(0, 0, 0), V(1, 0, 0), 180)          # rotacao: mantem as superficies exatas (bbox certo)
    bb = s.BoundBox
    s.translate(V(-bb.Center.x, -bb.Center.y, -bb.ZMin))
    msh = MeshPart.meshFromShape(Shape=s, LinearDeflection=0.01, AngularDeflection=0.0872665, Relative=False)
    fn = os.path.join(SD, "%s_x%d.stl" % (rotulo, qtd))
    msh.write(fn)
    print("STL %-28s %5.1f cm3  %5.1f x %5.1f x %5.1f mm  valido=%s" % (os.path.basename(fn), s.Volume / 1000, bb.XLength, bb.YLength, bb.ZLength, s.isValid()))

# conferencia do rebaixo da SAIDA (lado -x, z 77,5..85 na montagem = 18,5..26 na peca)
sa = pd.getObject("SAIDA").Shape
print("rebaixo SAIDA: ponto (-3.5,0,22) dentro=%s (esperado False); (-3.5,0,15) dentro=%s (esperado True)" % (
    sa.isInside(V(-3.5, 0, 22), 1e-6, True), sa.isInside(V(-3.5, 0, 15), 1e-6, True)))
