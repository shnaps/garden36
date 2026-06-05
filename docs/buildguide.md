# Build Guide — garden36

> Build both halves in parallel — steps are identical for left and right.

## What you need

- Soldering iron (fine tip, ~320°C) + solder
- Tweezers
- Flux
- USB-C cable
- [Full BOM](bom.md)

---

## 1. Order the PCB

Download gerbers from the [latest release](https://github.com/shnaps/garden36/releases/latest).

JLCPCB settings:
- **Layers:** 2
- **Thickness:** 1.6mm
- **Surface finish:** HASL or ENIG
- **Color:** your choice
- All other settings: default

---

## 2. Solder diodes

1. Tin one pad of each diode footprint.
2. Place 1N4148W **SOD-123** diode with cathode (line) matching the PCB silkscreen mark.
3. Reflow the pre-tinned pad, then solder the other side.
4. Do all 18 diodes per half before moving on.

> Diodes are **surface-mount** on the bottom (B.Cu) side of the PCB.

---

## 3. Solder hotswap sockets

1. Place Kailh CPG135001S30 sockets in the hotswap footprints on the **bottom** side.
2. Press firmly while soldering both pads — sockets must sit flush.

---

## 4. Solder power switch

Solder **MSK12C02-HB** slide switch to the `SW` footprint. Orient per silkscreen.

---

## 5. Solder reset button

Solder **B3U-1000P** tactile switch to the `RST` footprint.

---

## 6. Solder battery connector

Solder **JST S2B-PH-SM4-TB** to the `J1` footprint on the bottom side. Pin 1 = positive (check silkscreen).

---

## 7. Socket the nice!nano

**Recommended: socket it** (Mill-Max 315 sockets) so it's swappable.

1. Insert Mill-Max 12-pin sockets into the PCB from the **top** side.
2. Tack with solder on bottom side.
3. Solder all 24 pins (12 per row).
4. nice!nano mounts **components-side down, USB toward the top edge** of the PCB — this is the "USB facing PCB" (AH) orientation.

To socket permanently without Mill-Max: solder nice!nano directly in the same orientation.

---

## 8. Socket the nice!view

1. Insert 5-pin Mill-Max socket into the `Display` footprint from the top side.
2. Solder from the bottom.
3. nice!view connects via the 5-pin header — plug it in after flashing.

---

## 9. Flash firmware

Before installing the battery:

1. Connect nice!nano via USB-C.
2. Double-tap the reset button — nice!nano enters bootloader (appears as USB drive).
3. Download the `.uf2` from the [ZMK config repo](https://github.com/shnaps/zmk-config).
4. Drag-and-drop `.uf2` onto the drive. Device reboots automatically.
5. Repeat for the other half (left and right have separate firmware files).

---

## 10. Install battery

1. Connect LiPo battery JST-PH plug to `J1`.
2. Verify polarity before connecting — reverse polarity damages the MCU.
3. Route battery cable under the MCU.

---

## 11. Assemble case

1. Attach top plate over switches.
2. Insert standoffs through PCB + plates.
3. Screw bottom plate in place.

STEPs for plates are in `case/`. FreeCAD source: `case/drawing.FCStd`.

---

## 12. Test

- Power on both halves (slide switch).
- Open a text editor — type some keys.
- nice!view should show layer/WPM info.
- Both halves connect wirelessly via ZMK Bluetooth split.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Key not registering | Check diode orientation, hotswap socket seating |
| Half not connecting | Re-pair: clear bonds in ZMK, re-flash if needed |
| Display blank | Check nice!view socket pins, reseat display |
| Battery drains fast | Check MSK12C02 is OFF when not in use |
