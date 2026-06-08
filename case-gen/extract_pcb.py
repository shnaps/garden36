"""Extract case-relevant geometry from garden36.kicad_pcb.

Outputs pcb_data.json with:
- edge_cuts: list of segments/arcs on Edge.Cuts
- footprints: name, ref, position, rotation, side for case-relevant parts
"""
import json
import re
import sys
from pathlib import Path

PCB = Path(__file__).resolve().parent.parent / "garden36.kicad_pcb"


def tokenize(text):
    """S-expression tokenizer."""
    tokens = re.findall(r'"(?:[^"\\]|\\.)*"|\(|\)|[^\s()]+', text)
    return tokens


def parse(tokens):
    """Parse token stream into nested lists."""
    it = iter(tokens)

    def walk():
        items = []
        for tok in it:
            if tok == "(":
                items.append(walk())
            elif tok == ")":
                return items
            else:
                if tok.startswith('"') and tok.endswith('"') and len(tok) >= 2:
                    tok = tok[1:-1]
                items.append(tok)
        return items

    # top level
    out = []
    for tok in it:
        if tok == "(":
            out.append(walk())
    return out


def find_all(node, key):
    """Recursively find sub-lists whose first element == key."""
    found = []
    if isinstance(node, list):
        if node and node[0] == key:
            found.append(node)
        for child in node:
            found.extend(find_all(child, key))
    return found


def child(node, key):
    for item in node:
        if isinstance(item, list) and item and item[0] == key:
            return item
    return None


def main():
    text = PCB.read_text(encoding="utf-8")
    tree = parse(tokenize(text))[0]

    # --- Edge.Cuts ---
    edges = []
    for kind in ("gr_line", "gr_arc"):
        for el in find_all(tree, kind):
            layer = child(el, "layer")
            if not layer or layer[1] != "Edge.Cuts":
                continue
            entry = {"type": "line" if kind == "gr_line" else "arc"}
            for pt_key in ("start", "mid", "end"):
                pt = child(el, pt_key)
                if pt:
                    entry[pt_key] = [float(pt[1]), float(pt[2])]
            edges.append(entry)

    # --- Footprints ---
    wanted = {
        "SW_choc_v1_HS_CPG135001S30_1u": "switch",
        "MountingHole_2.2mm_M2": "hole_m2",
        "nice_view": "nice_view",
        "nice_nano_AH_USBdn": "nice_nano",
        "SW_MSK12C02-HB": "power_switch",
        "SW_SPST_B3U-1000P": "reset",
        "Battery": "battery",
        "mousebites_1mm": "mousebite",
    }
    fps = []
    for fp in find_all(tree, "footprint"):
        name = fp[1] if len(fp) > 1 and isinstance(fp[1], str) else ""
        short = name.split(":")[-1]
        if short == "LOGO":
            at = child(fp, "at")
            fx, fy = float(at[1]), float(at[2])
            xs, ys = [], []
            for p in find_all(fp, "fp_poly"):
                for xy in find_all(child(p, "pts"), "xy"):
                    xs.append(float(xy[1])); ys.append(float(xy[2]))
            # include visible silk text ("garden36" / "by shnaps") in the bbox
            for prop in find_all(fp, "property"):
                if len(prop) < 3 or not isinstance(prop[2], str) or not prop[2]:
                    continue
                lay = child(prop, "layer")
                hide = child(prop, "hide")
                flat = [x for x in prop if isinstance(x, str)]
                if (not lay or "Silk" not in lay[1]) or hide and hide[1] == "yes" or "hide" in flat:
                    continue
                if prop[2] == "LOGO":
                    continue
                pat = child(prop, "at")
                px, py = float(pat[1]), float(pat[2])
                font = child(child(child(prop, "effects") or [], "font") or [], "size")
                fh = float(font[1]) if font else 1.0
                tw = len(prop[2]) * fh * 0.95
                xs += [px - tw / 2, px + tw / 2]
                ys += [py - fh, py + fh]
            fps.append({
                "kind": "logo", "ref": "", "x": fx, "y": fy, "rot": 0.0,
                "layer": "F.SilkS",
                "bbox": [fx + min(xs), fy + min(ys), fx + max(xs), fy + max(ys)],
            })
            continue
        if short not in wanted:
            continue
        at = child(fp, "at")
        layer = child(fp, "layer")
        ref = ""
        for prop in find_all(fp, "property"):
            if len(prop) > 2 and prop[1] == "Reference":
                ref = prop[2]
                break
        x, y = float(at[1]), float(at[2])
        rot = float(at[3]) if len(at) > 3 else 0.0
        fps.append({
            "kind": wanted[short],
            "ref": ref,
            "x": x, "y": y, "rot": rot,
            "layer": layer[1] if layer else "F.Cu",
        })

    # standalone silk text (e.g. version string under logo)
    for t in find_all(tree, "gr_text"):
        layer = child(t, "layer")
        if not layer or "Silk" not in layer[1]:
            continue
        at = child(t, "at")
        x, y = float(at[1]), float(at[2])
        font = child(child(child(t, "effects") or [], "font") or [], "size")
        fh = float(font[1]) if font else 1.5
        tw = len(str(t[1])) * fh * 0.9
        fps.append({
            "kind": "silk_text", "ref": str(t[1]), "x": x, "y": y, "rot": 0.0,
            "layer": layer[1],
            "bbox": [x - tw / 2, y - fh, x + tw / 2, y + fh],
        })

    data = {"edge_cuts": edges, "footprints": fps}
    out = Path(__file__).resolve().parent / "pcb_data.json"
    out.write_text(json.dumps(data, indent=1), encoding="utf-8")

    # summary
    from collections import Counter
    counts = Counter(f["kind"] for f in fps)
    print(f"edges: {len(edges)} ({sum(1 for e in edges if e['type']=='arc')} arcs)")
    for k, v in sorted(counts.items()):
        print(f"{k}: {v}")
    xs = [f["x"] for f in fps if f["kind"] == "switch"]
    ys = [f["y"] for f in fps if f["kind"] == "switch"]
    print(f"switch bbox: x {min(xs):.1f}..{max(xs):.1f}  y {min(ys):.1f}..{max(ys):.1f}")


if __name__ == "__main__":
    main()
