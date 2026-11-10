# -*- coding: utf-8 -*-
# Modelo de massa da montagem equatorial (usado por revisao3.py e verifica_v3.py).
# Massas ESTIMADAS: pese as pecas reais e ajuste aqui (ou ajuste o contrapeso na pratica).
import FreeCAD as App
import Part

V = App.Vector
PETG_EF = 1.27 * 0.70          # g/cm3: PETG com ~70% de material efetivo (5 paredes + 50% gyroid)
M_NEMA = 300.0                 # g por motor NEMA17
M_608 = 12.0                   # g por rolamento 608
OTA_DENS = {"TUBO": 2.7, "CELULA_TRASEIRA": 1.1, "CELULA_OBJETIVA": 1.1, "OBJETIVA": 2.5, "PARASOL": 1.05,
            "SAPATA": 2.7, "FOCALIZADOR": 1.5, "TUBO_FOCO": 2.7, "DIAGONAL": 1.35, "OCULAR": 1.2, "BUSCADOR": 1.8}
DENS_ESPECIAL = {"BARRA_M12_CW": 0.66 / (3.14159265 * 36) * 1000,   # barra roscada M12: 0,66 g/mm
                 "BARRA_VIXEN_200": 1.6,                            # aluminio com rebaixos (~190 g)
                 "PORCAS_M12_TAMPA": 7.85, "PORCAS_M12_CONTRAPESO": 7.85,
                 "CONTRAPESO_ENCHIMENTO": 4.6}                      # esferas de aco (densidade aparente)


def gp(o):
    pai = o.getParentGeoFeatureGroup()
    return App.Placement() if pai is None else gp(pai).multiply(pai.Placement)


def raiz(o):
    pai = o.getParentGeoFeatureGroup()
    return o if pai is None else raiz(pai)


def forma(o):
    s = Part.getShape(o) if o.TypeId != "Part::Feature" else o.Shape
    s = s.copy(); s.Placement = gp(o).multiply(s.Placement)
    return s


def folhas(doc):
    return [o for o in doc.Objects if o.TypeId in ("Part::Feature", "PartDesign::Body") and
            not any(p.TypeId == "PartDesign::Body" for p in o.InList)]


_vol_nema = {}


def massa(o, s):
    lb = o.Label; r = raiz(o).Label
    if lb in DENS_ESPECIAL:
        return s.Volume / 1000 * DENS_ESPECIAL[lb]
    if r == "OTA_GREIKA_70070":
        return s.Volume / 1000 * OTA_DENS.get(lb, 1.2)
    if r == "TRIPE_GREIKA_70070":
        return 0.0
    if lb.startswith("NEMA17"):
        if r not in _vol_nema:
            _vol_nema[r] = sum(forma(x).Volume for x in folhas(o.Document) if raiz(x).Label == r and x.Label.startswith("NEMA17"))
        return s.Volume / _vol_nema[r] * M_NEMA
    if lb.startswith("ROL_608"):
        return M_608
    if lb.startswith(("EIXO", "PARAFUSO", "ANEL")):
        return s.Volume / 1000 * 7.85
    if lb.startswith("POLIA"):
        return s.Volume / 1000 * 2.7
    if lb.startswith("CORREIA"):
        return s.Volume / 1000 * 1.2
    return s.Volume / 1000 * PETG_EF


def _cm_forma(s):
    if len(s.Solids) == 1:
        return s.Solids[0].CenterOfMass
    tv = 0.0; c = V()
    for so in s.Solids:
        c += so.CenterOfMass * so.Volume; tv += so.Volume
    return c * (1.0 / tv)


def cm(doc, objs):
    """massa total (g) e centro de massa (global) de uma lista de objetos"""
    M = 0.0; c = V()
    for o in objs:
        s = forma(o)
        if s.isNull() or s.Volume < 1e-6:
            continue
        m = massa(o, s)
        M += m; c += _cm_forma(s) * m
    return M, (c * (1.0 / M) if M else c)


def _saida(o, grupo):
    return raiz(o).Label == grupo and o.Label.startswith(("EIXO", "POLIA_GT2_40T", "PARAFUSO_M4_40T", "ANEL_DIN471"))


def conjunto_dec(doc):
    """o que gira no eixo DEC: tubo, sela, barra Vixen, ACOPLADOR2 e a saida do redutor DEC"""
    return [o for o in folhas(doc) if raiz(o).Label in ("OTA_GREIKA_70070", "ACOPLADOR2", "SELA_DEC", "BARRA_VIXEN_200")
            or _saida(o, "DEC")]


def conjunto_ra(doc):
    """o que gira no eixo RA: conjunto DEC + redutor DEC inteiro (com o contrapeso) + ACOPLADOR1 + saida do redutor RA"""
    return [o for o in folhas(doc) if raiz(o).Label in ("OTA_GREIKA_70070", "ACOPLADOR2", "SELA_DEC", "BARRA_VIXEN_200",
                                                         "ACOPLADOR1", "DEC") or _saida(o, "RA")]
