# Visibilidade ao salvar pelo freecadcmd (sem interface).
# O freecadcmd nao grava o GuiDocument.xml (cores, visibilidade da interface). Sem ele, o FreeCAD usa a propriedade
# Visibility de cada objeto. Aqui:
#   - normaliza(doc): em cada Body so o Tip fica visivel (origem e features anteriores ocultas); corpos, links, grupos e
#     pecas de referencia de primeiro nivel ficam visiveis (menos BaseFeatures e os nomes em 'ocultar')
#   - ler_gui(arquivo) / devolve_gui(doc, gui): guarda o GuiDocument.xml antes e devolve depois de salvar, com a
#     visibilidade de cada ViewProvider igual a do objeto
import re
import zipfile

TIPOS_TOPO = ("PartDesign::Body", "App::Link", "Part::Feature", "App::Part", "App::DocumentObjectGroup")


def normaliza(doc, ocultar=()):
    bases = set()
    for o in doc.Objects:
        if o.TypeId == "PartDesign::Body":
            bf = getattr(o, "BaseFeature", None)
            if bf is not None:
                bases.add(bf.Name)
    for o in doc.Objects:
        if o.TypeId == "PartDesign::Body":
            for f in o.Group:
                f.Visibility = (f == o.Tip)
            o.Origin.Visibility = False
            for f in o.Origin.OriginFeatures:
                f.Visibility = False
        elif o.TypeId == "App::Part":
            o.Origin.Visibility = False
            for f in o.Origin.OriginFeatures:
                f.Visibility = False
    for o in doc.Objects:
        if o.TypeId not in TIPOS_TOPO:
            continue
        pai = o.getParentGeoFeatureGroup()
        if pai is not None and pai.TypeId == "PartDesign::Body":
            continue                                   # feature dentro de corpo: ja tratada
        if o.Name in bases:
            o.Visibility = False
        else:
            o.Visibility = not (o.Name in ocultar or o.Label in ocultar)


def ler_gui(arquivo):
    try:
        with zipfile.ZipFile(arquivo) as z:
            if "GuiDocument.xml" in z.namelist():
                return z.read("GuiDocument.xml").decode("utf-8")
    except (OSError, zipfile.BadZipFile):
        pass
    return None


def devolve_gui(doc, gui):
    """chamar depois de doc.save(); se o arquivo salvo nao tem GuiDocument.xml, grava 'gui' ajustado"""
    if not gui:
        return False
    with zipfile.ZipFile(doc.FileName) as z:
        if "GuiDocument.xml" in z.namelist():
            return False
    vis = {o.Name: o.Visibility for o in doc.Objects}

    def troca(m):
        nome, corpo = m.group(1), m.group(2)
        if nome in vis:
            corpo = re.sub(r'(<Property name="Visibility"[^>]*>\s*<Bool value=")(?:true|false)(")',
                           lambda k: k.group(1) + ("true" if vis[nome] else "false") + k.group(2), corpo, count=1)
        return '<ViewProvider name="%s"%s</ViewProvider>' % (nome, corpo)

    txt = re.sub(r'<ViewProvider name="([^"]+)"((?:(?!</ViewProvider>).)*)</ViewProvider>', troca, gui, flags=re.S)
    with zipfile.ZipFile(doc.FileName, "a", zipfile.ZIP_DEFLATED) as z:
        z.writestr("GuiDocument.xml", txt)
    return True
