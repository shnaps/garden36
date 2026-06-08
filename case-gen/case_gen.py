"""garden36 parametric case generator.

Reads pcb_data.json (from extract_pcb.py) and generates per-half case STEPs:
  out/{left,right}_bottom.step  — tray: floor, walls, standoffs, USB/power/reset access
  out/{left,right}_top.step     — cover: integrated Choc plate, display hump + window

Global z=0 at case bottom face. Both parts are modeled in the same global frame
(top cover in its assembled position) so cross-part cutouts (USB) stay aligned.

Stack-up:
  0 .. FLOOR_T                          case floor
  FLOOR_T .. +UNDER_PCB                 sockets + battery space, standoffs
  z_pcb_bot .. z_pcb_top                PCB
  z_pcb_top .. +ABOVE_PCB               choc switch body under plate
  z_plate .. +PLATE_T                   plate (top cover)
  hump rises to z_pcb_top + HUMP_H over the nano/nice!view zone
"""
import json
import math
from pathlib import Path

from build123d import (
    Align, Box, Cone, Cylinder, Kind, Location, Mode, Plane, Pos, Rot,
    BuildLine, BuildSketch, Polyline, make_face, offset,
    export_step, export_stl, extrude,
)

# ---------------- parameters (mm) ----------------
PCB_T = 1.6
# nothing big under the PCB: battery sits ABOVE the PCB under the controller.
# under-PCB = choc socket protrusion (~1.85) + seat for an M2x3 insert in the
# printed case-column standoffs (5/half).
UNDER_PCB = 4.0
# controller stack ABOVE PCB: nano on 5mm male headers; nice!view ~8.5 underside;
# a 7 or 10mm F-F standoff at each battery hole rises from the PCB to carry the
# flat cover (screwed from the PCB underside). 10mm clears nice!view, 7mm = nano-only.
CTRL_STANDOFF = 10.0  # display version; cover underside = PCB_top + this
DISPLAY_TOP = 9.5     # nice!view top above PCB top (verify w/ caliper)
ABOVE_PCB = 3.2       # plate underside above PCB = where choc switches hold it.
                      # MEASURED: 1.6mm plate sits ~1mm proud of the 2.2 clip notch
                      # -> wall must reach 3.2 or top/bottom won't be flush. Tune this
                      # to your exact gap (raise/lower until wall meets plate rim).
PLATE_T = 1.6         # NOTE: choc clips spec 1.2-1.4 -> clips won't latch; sockets hold
FLOOR_T = 1.6
WALL_T = 2.5
CLEAR = 0.3           # PCB edge to inner wall

SWITCH_CUT = 13.8     # choc plate cutout, square
USE_INSERTS = True    # heat-set M2x4xOD3.5 in standoff tops (False: M2 self-taps PETG)
STANDOFF_D = 4.5      # slim shaft; insert zone is a wider head (INSERT_HEAD_D)
INSERT_HEAD_D = 6.2   # top 4.5mm of case standoffs, wall ~1.5 around OD3.5 insert
TOP_BOSS_D = 4.5      # plate spacer bosses (just surround the 2.3 pass hole)
INSERT_D = 3.2        # pilot for OD3.5 heat-set in PETG
INSERT_DEPTH = 3.2    # M2x3 insert + 0.2 sink (fits UNDER_PCB=4)
SCREW_PILOT_D = 1.7   # self-tap pilot (no-insert mode)
SCREW_PASS_D = 2.3    # M2 clearance
CSK_D = 4.4           # countersink max dia for M2 flat head (head 3.8 + slack)
CSK_DEPTH = 1.2

# measured stack (user, 2026-06): nano soldered pins into 5mm sockets +0.4 gap;
# nice!view underside 8.5mm above PCB top
VIEW_GLASS_TOP = 9.3  # display glass top above PCB — print-fit verified (was est. 11.3)
LIP_CLEAR = 0.2       # window lip above glass (use 0.5 foam strip to preload)
HUMP_WALL = 1.8
HUMP_H = VIEW_GLASS_TOP + LIP_CLEAR + HUMP_WALL          # = 11.3 above PCB top
HUMP_W = 22.0
VIEW_S = 17.78        # nice!view module local extent toward user (after y-flip: -y)
WINDOW_W = 12.0       # window opening; ~1mm lip each side holds display down
WINDOW_N, WINDOW_S = 16.5, 12.5   # window extents from view center (+y away / -y toward user)
COVER_RECESS = 1.0    # ledge depth in roof for display cover plate
COVER_LEDGE = 1.6     # ledge width around window
COVER_CLEAR = 0.15    # cover-to-recess fit clearance per side
# viewing hole in cover over LCD active area (LS011B7DH03 ~11.5x25 portrait)
COVER_HOLE_W = 11.5
COVER_HOLE_N = 15.0   # extents from nice!view footprint center, +y away from user
COVER_HOLE_S = 10.5
COVER_SCREWS = False  # 2x M2x4 through cover ends into thickened roof pads


USB_W = 14.0          # usb plug notch width
USB_Z_BOT = 1.0       # notch bottom above PCB top

# controller cover: flat plate floating on the 2 battery standoffs, no walls
OPEN_W = 18.6         # plate opening width: nano 17.78 + margin
COVER_T = 1.6         # flat cover plate
COVER_OVERHANG = 2.0  # cover overhang past the opening (rests/presses, no walls)

PWR_SLOT = (10.0, 6.0)   # floor opening under MSK12C02
BAT_COL_D = 4.5          # slim battery/box columns (self-tap, no insert)

# reset flexure (KOMETA-style printed button in floor)
FLEX_PAD_D = 7.0      # round pad at free end of spring arm
FLEX_ARM_W = 5.0      # arm width
FLEX_ARM_L = 11.0     # pad center to root
FLEX_SLOT = 1.1       # U-slot width around tongue
FLEX_PAD_SHIFT = 1.5  # pad center offset away from power switch
NUB_D = 2.5
NUB_GAP = 0.25        # rest gap below B3U-1000P plunger
B3U_H = 1.95          # button body+plunger below PCB bottom

LOGO_MARGIN = 1.0     # logo window margin around silk bbox

SPLIT_X = 138.0       # panel halves split line (kicad x)
OUT = Path(__file__).resolve().parent / "out"

# derived
Z_PCB_BOT = FLOOR_T + UNDER_PCB
Z_PCB_TOP = Z_PCB_BOT + PCB_T
Z_PLATE = Z_PCB_TOP + ABOVE_PCB          # plate underside / wall top
Z_HUMP_TOP = Z_PCB_TOP + HUMP_H
BAY_RIM = Z_PCB_TOP + CTRL_STANDOFF          # bay wall top = cover underside = standoff top


# ---------------- pcb data ----------------
def load():
    return json.loads((Path(__file__).resolve().parent / "pcb_data.json").read_text())


def arc_points(start, mid, end, n=24):
    """Sample a 3-point arc."""
    ax, ay = start; bx, by = mid; cx, cy = end
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-9:
        return [tuple(start), tuple(end)]
    ux = ((ax**2 + ay**2) * (by - cy) + (bx**2 + by**2) * (cy - ay) + (cx**2 + cy**2) * (ay - by)) / d
    uy = ((ax**2 + ay**2) * (cx - bx) + (bx**2 + by**2) * (ax - cx) + (cx**2 + cy**2) * (bx - ax)) / d
    r = math.hypot(ax - ux, ay - uy)
    a0 = math.atan2(ay - uy, ax - ux)
    a1 = math.atan2(by - uy, bx - ux)
    a2 = math.atan2(cy - uy, cx - ux)

    def sweep(f, t):
        s = t - f
        while s <= -math.pi: s += 2 * math.pi
        while s > math.pi: s -= 2 * math.pi
        return s
    total = sweep(a0, a1) + sweep(a1, a2)
    return [(ux + r * math.cos(a0 + total * i / n), uy + r * math.sin(a0 + total * i / n))
            for i in range(n + 1)]


def half_outline(edges, left=True):
    """Chain one half's Edge.Cuts into a closed loop (bridges mousebite tab gaps)."""
    sel = []
    for e in edges:
        xs = [e["start"][0], e["end"][0]] + ([e["mid"][0]] if "mid" in e else [])
        if (max(xs) < SPLIT_X) == left and (min(xs) < SPLIT_X) == left:
            sel.append(e)

    def pts_of(e, rev=False):
        if e["type"] == "arc":
            p = arc_points(e["start"], e["mid"], e["end"])
        else:
            p = [tuple(e["start"]), tuple(e["end"])]
        return p[::-1] if rev else p

    unused = sel[:]
    pts = pts_of(unused.pop(0))
    while unused:
        cur = pts[-1]
        best, bd, brev = None, 1e9, False
        for e in unused:
            ds = math.dist(cur, e["start"]); de = math.dist(cur, e["end"])
            if ds < bd: best, bd, brev = e, ds, False
            if de < bd: best, bd, brev = e, de, True
        unused.remove(best)
        pts.extend(pts_of(best, brev))      # gap >0 becomes a straight bridge
    if math.dist(pts[-1], pts[0]) > 0.05:
        pts.append(pts[0])
    return [(x, -y) for x, y in pts]        # flip y for CAD orientation


def big_loop_edges(edges):
    """Drop the small 3mm interior cutout loops."""
    keep = []
    for e in edges:
        xs = [e["start"][0], e["end"][0]]
        ys = [e["start"][1], e["end"][1]]
        if max(xs) - min(xs) < 4 and 84 < min(ys) and max(ys) < 89:
            continue
        keep.append(e)
    return keep


def fp_filter(fps, kind, left=True):
    return [f for f in fps if f["kind"] == kind and (f["x"] < SPLIT_X) == left]


def flip(f):
    return (f["x"], -f["y"])


def face_from(pts):
    clean = [pts[0]]
    for p in pts[1:]:
        if math.dist(p, clean[-1]) > 1e-4:
            clean.append(p)
    if math.dist(clean[0], clean[-1]) > 1e-4:
        clean.append(clean[0])
    with BuildSketch() as sk:
        with BuildLine():
            Polyline(*clean)
        make_face()
    return sk.sketch


def at_z(face, z):
    return Location((0, 0, z)) * face


def rect_face_g(cx, cy, w, l):
    h_w, h_l = w / 2, l / 2
    return face_from([(cx - h_w, cy - h_l), (cx + h_w, cy - h_l),
                      (cx + h_w, cy + h_l), (cx - h_w, cy + h_l), (cx - h_w, cy - h_l)])


def face_circle(cx, cy, r, n=48):
    return face_from([(cx + r * math.cos(2 * math.pi * i / n),
                       cy + r * math.sin(2 * math.pi * i / n)) for i in range(n + 1)])




A_BOT = (Align.CENTER, Align.CENTER, Align.MIN)


# ---------------- solid building ----------------
def build_half(d, left):
    name = "left" if left else "right"
    outline = half_outline(big_loop_edges(d["edge_cuts"]), left)
    pcb_face = face_from(outline)
    inner = offset(pcb_face, CLEAR, kind=Kind.INTERSECTION)
    outer = offset(pcb_face, CLEAR + WALL_T, kind=Kind.INTERSECTION)

    fps = d["footprints"]
    switches = fp_filter(fps, "switch", left)
    holes = fp_filter(fps, "hole_m2", left)
    nano = fp_filter(fps, "nice_nano", left)[0]
    view = fp_filter(fps, "nice_view", left)[0]
    pwr = fp_filter(fps, "power_switch", left)[0]
    rst = fp_filter(fps, "reset", left)[0]
    bat = fp_filter(fps, "battery", left)[0]
    logos = fp_filter(fps, "logo", left)
    texts = fp_filter(fps, "silk_text", left)
    # 5 of 7 PCB holes hold the case; the 2 flanking the battery connector mount the box
    bat_holes = [h for h in holes if math.dist((h["x"], h["y"]), (bat["x"], bat["y"])) <= 10]
    holes = [h for h in holes if math.dist((h["x"], h["y"]), (bat["x"], bat["y"])) > 10]

    nx, ny = flip(nano)
    vx, vy = flip(view)
    px, py = flip(pwr)
    rx, ry = flip(rst)
    bx, by = flip(bat)

    # hump zone: nano + nice!view envelope (nano USB end is +19.3 from center, away)
    hz_n = ny + 19.3 + 2.0
    hz_s = vy - VIEW_S - 2.5
    hz_cx, hz_cy = nx, (hz_n + hz_s) / 2
    hz_len = hz_n - hz_s

    hump_face = rect_face_g(hz_cx, hz_cy, HUMP_W, hz_len) & outer
    hump_hole = rect_face_g(hz_cx, hz_cy, HUMP_W - 2 * HUMP_WALL, hz_len - 2 * HUMP_WALL) & inner
    win_n, win_s = vy + WINDOW_N, vy - WINDOW_S
    window = rect_face_g(vx, (win_n + win_s) / 2, WINDOW_W, win_n - win_s)

    # USB notch: one global cutter through case wall (bottom) + bay wall (top)
    usb_cut = Pos(nx, hz_n, Z_PCB_TOP + USB_Z_BOT) * Box(USB_W, 14, 40, align=A_BOT)
    usb_cut_bay = Pos(nx, hz_n, Z_PCB_TOP + USB_Z_BOT) * Box(USB_W, 14, BAY_RIM, align=A_BOT)

    # ---------- bottom tray ----------
    bottom = extrude(at_z(outer, 0), FLOOR_T)                      # floor
    bottom += extrude(at_z(outer - inner, FLOOR_T), Z_PLATE - FLOOR_T)  # wall ring
    # one column per PCB hole: M2x7 F-F metal standoff between floor and PCB.
    # M2x4 csk from below through the floor, M2x8 csk from above through
    # plate+boss+PCB — both thread into the standoff. No printed columns.
    # 5 case columns: printed standoff floor->PCB with an M2x3 heat-set insert at
    # the top. M2x8 csk from the plate threads down into the insert. (Battery holes
    # get NOTHING in the bottom — any cover-standoff holes live in the top plate.)
    for h in holes:
        x, y = flip(h)
        bottom += Pos(x, y, FLOOR_T) * Cylinder(STANDOFF_D / 2, UNDER_PCB, align=A_BOT)
        bottom += Pos(x, y, Z_PCB_BOT - INSERT_DEPTH) * Cylinder(INSERT_HEAD_D / 2, INSERT_DEPTH, align=A_BOT)
        bottom -= Pos(x, y, Z_PCB_BOT - INSERT_DEPTH) * Cylinder(INSERT_D / 2, INSERT_DEPTH + 0.1, align=A_BOT)
    bottom -= Pos(px, py, -1) * Box(PWR_SLOT[0], PWR_SLOT[1], FLOOR_T + 2, align=A_BOT)
    # reset flexure: U-slot tongue in floor, nub presses B3U-1000P from below
    shift = FLEX_PAD_SHIFT * (1 if rx > px else -1)      # pad away from power switch
    pcx = rx + shift
    arm_end_y = ry - FLEX_ARM_L
    tongue = face_circle(pcx, ry, FLEX_PAD_D / 2) + rect_face_g(pcx, (ry + arm_end_y) / 2, FLEX_ARM_W, FLEX_ARM_L)
    slot_ring = offset(tongue, FLEX_SLOT, kind=Kind.INTERSECTION) - tongue
    root = rect_face_g(pcx, arm_end_y - FLEX_SLOT / 2, FLEX_ARM_W + 2 * FLEX_SLOT + 2, FLEX_SLOT + 2)
    slot = slot_ring - root
    bottom -= extrude(at_z(slot, -1), FLOOR_T + 2)
    nub_h = (Z_PCB_BOT - B3U_H - NUB_GAP) - FLOOR_T
    bottom += Pos(rx, ry, FLOOR_T) * Cylinder(NUB_D / 2, nub_h, align=A_BOT)
    bottom -= usb_cut

    # ---------- top cover (flat plate; controller box is a separate snap-on part) ----------
    # opening is a pure rectangle clamped at the split-side edge (straight there)
    mnx = min(p[0] for p in outline)
    mxx = max(p[0] for p in outline)
    ox0 = max(nx - OPEN_W / 2, mnx - CLEAR)
    ox1 = min(nx + OPEN_W / 2, mxx + CLEAR)

    # opening shrunk to the controller envelope: nano width + margin, USB end to
    # display S end; plate covers the battery zone (solder bumps < 2.2 gap)
    o_s = vy - VIEW_S - 1.0
    oc_y, o_len = (hz_n + o_s) / 2, hz_n - o_s

    def open_rect(inset):
        return rect_face_g((ox0 + ox1) / 2, oc_y, (ox1 - ox0) - 2 * inset, o_len - 2 * inset)

    opening = open_rect(0)
    flat_x = ox0 - 0.1 if left else ox1 + 0.1     # opening edge on the nano side
    plate_face = outer - opening
    top = extrude(at_z(plate_face, Z_PLATE), PLATE_T)
    # switch cutouts (splayed keys -> rotated squares). KiCad rotation is visually
    # CCW; after the y-flip that stays +CCW in CAD coords (sign must NOT flip)
    for s in switches:
        x, y = flip(s)
        top -= Pos(x, y, Z_PLATE - 1) * Rot(0, 0, s["rot"]) * Box(
            SWITCH_CUT, SWITCH_CUT, PLATE_T + 2, align=A_BOT)
    # battery wires soldered directly (no JST connector) — no pocket needed;
    # solder bumps sit inside the box opening with 2.2mm clearance
    # logo windows: see PCB silk logo (+ version text beneath) through the plate
    for lg in logos:
        x0, y0, x1, y1 = lg["bbox"]
        # union nearby silk text (e.g. "v1.1") into the window
        for t in texts:
            tx0, ty0, tx1, ty1 = t["bbox"]
            if abs(t["x"] - lg["x"]) < 15 and 0 < ty0 - y1 < 8:
                x0, y0 = min(x0, tx0), min(y0, ty0)
                x1, y1 = max(x1, tx1), max(y1, ty1)
        x0 -= LOGO_MARGIN; y0 -= LOGO_MARGIN; x1 += LOGO_MARGIN; y1 += LOGO_MARGIN
        cx, cy = (x0 + x1) / 2, -(y0 + y1) / 2   # flip y
        win = rect_face_g(cx, cy, x1 - x0, y1 - y0) & inner
        top -= extrude(at_z(win, Z_PLATE - 1), PLATE_T + 2)
    # ---------- snap-on controller boxes (tall: nice!view; plain: nano only) ----------
    # ---------- controller: NO walls, NO rim, NO box ----------------------------
    # Top plate just has the opening (controller pokes through, sides exposed).
    # A flat cover floats above the opening on the 2 battery standoffs and presses
    # the nice!view / nano down. Nothing else.
    bat_y = -bat_holes[0]["y"]
    cover_screws = [flip(h) for h in bat_holes]

    def build_cover(tall):
        # flat lid spanning the opening + small overhang, sitting at the standoff top
        cov_face = rect_face_g((ox0 + ox1) / 2, (bat_y + hz_n) / 2,
                               (ox1 - ox0) + 2 * COVER_OVERHANG,
                               (hz_n - bat_y) + 2 * COVER_OVERHANG)
        cov = extrude(at_z(cov_face, BAY_RIM), COVER_T)
        if tall:                                             # LCD viewing window
            vh_s = vy - COVER_HOLE_S; vh_n = vy + COVER_HOLE_N
            cov -= extrude(at_z(rect_face_g(vx, (vh_s + vh_n) / 2,
                                            COVER_HOLE_W, vh_n - vh_s), BAY_RIM - 1),
                           COVER_T + 2)
        # 2 csk screws into the battery standoffs
        for sx, sy in cover_screws:
            cov -= Pos(sx, sy, BAY_RIM - 1) * Cylinder(SCREW_PASS_D / 2, COVER_T + 2, align=A_BOT)
            cov -= Pos(sx, sy, BAY_RIM + COVER_T - CSK_DEPTH) * Cone(0, CSK_D / 2, CSK_DEPTH, align=A_BOT)
        return cov

    cover_view = build_cover(tall=True)
    cover_plain = build_cover(tall=False)

    # spacer bosses + countersunk screw at the 5 case PCB holes (plate -> standoff)
    for h in holes:
        x, y = flip(h)
        top += Pos(x, y, Z_PCB_TOP) * Cylinder(TOP_BOSS_D / 2, ABOVE_PCB, align=A_BOT)
        top -= Pos(x, y, Z_PCB_TOP - 1) * Cylinder(SCREW_PASS_D / 2, ABOVE_PCB + PLATE_T + 2, align=A_BOT)
        top -= Pos(x, y, Z_PLATE + PLATE_T - CSK_DEPTH) * Cone(0, CSK_D / 2, CSK_DEPTH, align=A_BOT)
    # battery columns belong to the TOP plate: clear pass-holes so the cover-standoff
    # screw path runs through the plate (the bottom stays solid there)
    for x, y in cover_screws:
        top -= Pos(x, y, Z_PCB_TOP - 1) * Cylinder(SCREW_PASS_D / 2, ABOVE_PCB + PLATE_T + 2, align=A_BOT)

    return name, bottom, top, cover_view, cover_plain


def main():
    (OUT / "step").mkdir(parents=True, exist_ok=True)
    (OUT / "stl").mkdir(parents=True, exist_ok=True)
    d = load()
    for left in (True, False):
        name, bot, top, cover_view, cover_plain = build_half(d, left)
        parts = {"bottom": bot, "top": top,
                 "cover_view": cover_view, "cover_plain": cover_plain}
        for pname, part in parts.items():
            export_step(part, OUT / "step" / f"{name}_{pname}.step")
            export_stl(part, OUT / "stl" / f"{name}_{pname}.stl")
        print(f"{name}: " + ", ".join(f"{p} {s.volume/1000:.1f}cm3" for p, s in parts.items()))


if __name__ == "__main__":
    main()
