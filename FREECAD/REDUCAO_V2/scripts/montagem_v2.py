# Gera MONTAGEM_V2.FCStd (links para REDUCAO_V2.FCStd) com planetas em fase, checa interferencias, exporta STL
import FreeCAD as App, Part, math, os, cmath
V = App.Vector; P = App.Placement; R = App.Rotation
OUT = os.environ.get("OUTDIR", r"C:\LUIZ\PROJECTS\GOTO_TELESCOPE\FREECAD\REDUCAO_V2")
OLD = r"C:\LUIZ\PROJECTS\GOTO_TELESCOPE\FREECAD\REDUCAO\MONTAGEM FINAL.FCStd"
EXPORT = os.environ.get("EXPORT", "1") == "1"

pd = App.openDocument(os.path.join(OUT, "REDUCAO_V2.FCStd"))
pd.recompute()
ss = pd.getObject("Parametros")
m = float(ss.get("modulo").Value) if hasattr(ss.get("modulo"), "Value") else float(ss.get("modulo"))
Zs = int(round(float(ss.get("dentes_sol")))); Zp = int(round(float(ss.get("dentes_planeta")))); Zr = int(round(float(ss.get("dentes_coroa"))))
Rc = m * (Zs + Zp) / 2.0
Rs, Rp, Rr = m * Zs / 2, m * Zp / 2, m * Zr / 2
ps, pp, pr = 360.0 / Zs, 360.0 / Zp, 360.0 / Zr
print("m=%.3f Zs=%d Zp=%d Zr=%d Rc=%.3f reducao=%.1f" % (m, Zs, Zp, Zr, Rc, (1 + Zr / Zs) ** 5))

def phase(gobj, internal=False):
    s = gobj.Shape.copy(); s.Placement = P()
    pts = [v for w in s.Wires for v in w.discretize(Number=6000)]
    rs = [math.hypot(v.x, v.y) for v in pts]
    if internal:
        lim = min(rs) + 0.005; sel = [v for v, r in zip(pts, rs) if r <= lim]
    else:
        lim = max(rs) - 0.005; sel = [v for v, r in zip(pts, rs) if r >= lim]
    z = len(rs)  # unused
    return sel

def tooth_phase(gobj, pitch, internal=False):
    sel = phase(gobj, internal)
    acc = sum(cmath.exp(1j * 2 * math.pi * math.degrees(math.atan2(v.y, v.x)) / pitch) for v in sel)
    return (math.degrees(cmath.phase(acc)) / 360.0 * pitch) % pitch

tau_s = tooth_phase(pd.getObject("Engrenagem_sol"), ps)
tau_sm = tooth_phase(pd.getObject("Engrenagem_sol_motor"), ps)
tau_p = tooth_phase(pd.getObject("Engrenagem_planeta"), pp)
tau_r = tooth_phase(pd.getObject("Coroa_interna"), pr, internal=True)
print("fases: sol=%.3f sol_motor=%.3f planeta=%.3f coroa=%.3f" % (tau_s, tau_sm, tau_p, tau_r))

def wrap(x, p):
    return (x + p / 2) % p - p / 2

def mesh(theta, sun_tooth):
    ds = wrap(sun_tooth - theta, ps)
    dr = wrap(tau_r - theta, pr)
    g1 = theta + 180 - (Rs / Rp) * ds
    g2 = theta + (Rr / Rp) * dr
    return wrap(g1 - g2, pp), g2

def solve_stage(sun_tooth):
    best = None
    t = 90 - 6.0
    while t <= 90 + 6.0:
        err, g2 = mesh(t, sun_tooth)
        if best is None or abs(err) < abs(best[1]) - 1e-12 or (abs(abs(err) - abs(best[1])) < 1e-9 and abs(t - 90) < abs(best[0] - 90)):
            best = (t, err)
        t += 0.0005
    return best[0]

doc = App.newDocument("MONTAGEM_V2")
doc.saveAs(os.path.join(OUT, "MONTAGEM_V2.FCStd"))
def link(name, obj, pl, group):
    l = doc.addObject("App::Link", name)
    l.LinkedObject = obj
    l.Placement = pl
    group.addObject(l)
    return l

bodies = {n: pd.getObject(n) for n in ("PLANETA", "SOL_MOTOR", "SOL", "SUPORTE", "SAIDA", "TAMPA", "CAIXA")}
gfix = doc.addObject("App::DocumentObjectGroup", "Fixos")
link("CAIXA", bodies["CAIXA"], P(V(0, 0, -3.4), R()), gfix)
link("TAMPA", bodies["TAMPA"], P(V(0, 0, 59.4), R()), gfix)

# motor de referencia (copia estatica do arquivo antigo)
try:
    od = App.openDocument(OLD, True)
    shs = []
    for o in od.Objects:
        if o.TypeId == "Part::Feature" and (o.Label.startswith("Motor") or o.Label == "Shaft"):
            s = o.Shape.copy(); s.Placement = o.getGlobalPlacement(); shs.append(s)
    mot = doc.addObject("Part::Feature", "NEMA17_referencia")
    mot.Shape = Part.makeCompound(shs)
    gfix.addObject(mot)
    App.closeDocument(od.Name)
except Exception as e:
    print("motor nao copiado:", e)

g0 = doc.addObject("App::DocumentObjectGroup", "Entrada")
link("SOL_MOTOR", bodies["SOL_MOTOR"], P(V(0, 0, 10.2), R()), g0)

sun_tooth = tau_sm  # sol do motor com rotacao 0
report = []
for k in range(1, 6):
    zk = 12.3 + 9.8 * (k - 1)
    theta = solve_stage(sun_tooth)
    phi = theta - 90.0
    grp = doc.addObject("App::DocumentObjectGroup", "Estagio_%d" % k)
    link("SUPORTE_%d" % k, bodies["SUPORTE"], P(V(0, 0, zk), R(V(0, 0, 1), phi)), grp)
    errs = []
    for j in range(3):
        th = theta + 120 * j
        err, g2 = mesh(th, sun_tooth)
        errs.append(err)
        psi = g2 - tau_p - pp / 2
        pos = V(Rc * math.cos(math.radians(th)), Rc * math.sin(math.radians(th)), zk + 0.2)
        link("PLANETA_%d_%d" % (k, j + 1), bodies["PLANETA"], P(pos, R(V(0, 0, 1), psi)), grp)
    report.append("estagio %d: carrier=%.3f deg, erro de fase planetas=%s" % (k, phi, ["%.4f" % e for e in errs]))
    if k < 5:
        link("SOL_%d" % k, bodies["SOL"], P(V(0, 0, zk + 7.5), R(V(0, 0, 1), phi)), grp)
        sun_tooth = tau_s + phi
    else:
        link("SAIDA", bodies["SAIDA"], P(V(0, 0, zk + 7.5), R(V(0, 0, 1), phi)), grp)
print("\n".join(report))
doc.recompute()
doc.saveAs(os.path.join(OUT, "MONTAGEM_V2.FCStd"))

# ---------------- interferencias
items = [o for o in doc.Objects if o.TypeId in ("App::Link", "Part::Feature")]
shapes = {o.Name: Part.getShape(o) for o in items}
names = list(shapes)
print("\nINTERFERENCIAS (vol > 0.001 mm3):")
n_int = 0
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        a, b = shapes[names[i]], shapes[names[j]]
        if not a.BoundBox.intersect(b.BoundBox):
            continue
        try:
            v = a.common(b).Volume
        except Exception:
            v = -1
        if v > 0.001 or v < 0:
            n_int += 1
            print("  %-14s x %-14s %.4f mm3" % (names[i], names[j], v))
print("total de pares com interferencia:", n_int)

# ---------------- STL
if EXPORT:
    import MeshPart, Mesh
    sd = os.path.join(OUT, "STL")
    os.makedirs(sd, exist_ok=True)
    qtd = {"PLANETA": 15, "SOL_MOTOR": 1, "SOL": 4, "SUPORTE": 5, "SAIDA": 1, "TAMPA": 1, "CAIXA": 1}
    for n, b in bodies.items():
        msh = MeshPart.meshFromShape(Shape=b.Shape, LinearDeflection=0.01, AngularDeflection=0.0872665, Relative=False)
        fn = os.path.join(sd, "%s_x%d.stl" % (n, qtd[n]))
        msh.write(fn)
        print("STL", fn, msh.CountFacets, "facetas")
