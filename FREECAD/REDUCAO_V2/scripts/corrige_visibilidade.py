# Deixa as pecas visiveis ao abrir REDUCAO_V2 / MONTAGEM_V2 e devolve o GuiDocument.xml (cores) se ele tiver sumido.
# Rodar com: & "C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe" corrige_visibilidade.py   (com os arquivos fechados no FreeCAD)
import FreeCAD as App, os, sys, glob

D = r"C:\LUIZ\PROJECTS\GOTO_TELESCOPE\FREECAD\REDUCAO_V2"
sys.path.insert(0, os.path.join(D, "scripts"))
import visivel

for fn in ("REDUCAO_V2.FCStd", "MONTAGEM_V2.FCStd"):
    caminho = os.path.join(D, fn)
    gui = visivel.ler_gui(caminho)
    origem = fn
    if gui is None:                                  # pega o GuiDocument.xml do backup mais novo que tiver um
        for bk in sorted(glob.glob(os.path.join(D, "_backup_*", fn)), key=os.path.getmtime, reverse=True):
            gui = visivel.ler_gui(bk)
            if gui:
                origem = bk
                break
    doc = App.openDocument(caminho)
    visivel.normaliza(doc, ocultar=("SOL_MOTOR_cubo_original",))
    doc.save()
    devolvido = visivel.devolve_gui(doc, gui)
    vis = [o.Label for o in doc.Objects if o.Visibility and o.getParentGeoFeatureGroup() is None]
    print("%s: GuiDocument %s (%s); visiveis no nivel de cima: %d" % (fn, "devolvido" if devolvido else "mantido",
          origem, len(vis)))
