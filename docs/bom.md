# Bill of Materials — garden36

Per side × 2 = full build. Quantities below are **per keyboard** (both halves).

## Electronics

| Component | Qty | Notes | Source |
|-----------|-----|-------|--------|
| nice!nano v2 | 2 | nRF52840 wireless MCU, one per half | [typeractive](https://typeractive.xyz/products/nice-nano) |
| nice!view | 2 | MIP display, one per half | [typeractive](https://typeractive.xyz/products/nice-view) |
| Kailh Choc v1 switch | 36 | Any Choc v1 linear/tactile/clicky | [typeractive](https://typeractive.xyz/collections/switches) |
| Kailh Choc hotswap socket CPG135001S30 | 36 | | [typeractive](https://typeractive.xyz/products/kailh-hotswap-sockets) |
| 1N4148W diode SOD-123 | 36 | One per switch | [LCSC C2290336](https://www.lcsc.com/product-detail/C2290336.html) / AliExpress |
| MSK12C02-HB slide switch | 2 | Power on/off per half | [LCSC C431540](https://www.lcsc.com/product-detail/C431540.html) |
| B3U-1000P tactile reset switch | 2 | One per half | [LCSC C841584](https://www.lcsc.com/product-detail/C841584.html) |
| JST S2B-PH-SM4-TB battery connector | 2 | | [LCSC C295747](https://www.lcsc.com/product-detail/C295747.html) |
| LiPo battery 301230 or similar | 2 | ~100–300 mAh, fits under MCU | AliExpress |
| Mill-Max 315-43-112-41-003000 socket (12-pin) | 4 | For socketing nice!nano (optional but recommended) | [Digikey](https://www.digikey.com) |
| Mill-Max 315-43-105-41-003000 socket (5-pin) | 4 | For socketing nice!view (optional but recommended) | [Digikey](https://www.digikey.com) |

## PCB & Case

| Item | Qty | Notes |
|------|-----|-------|
| garden36 PCB | 2 halves | Order via JLCPCB/PCBWay from gerbers in release |
| Top plate | 2 | `case/Only top.step` (FR4 or acrylic, 1.5mm) |
| Bottom plate | 2 | `case/Bottom left.step`, `case/Bottom right.step` |
| M2 × 6mm standoff | ~14 | Exact qty depends on case variant |
| M2 × 4mm screw | ~28 | |
| Choc keycaps | 36 | Low-profile Choc spacing | [typeractive](https://typeractive.xyz/collections/keycaps) |

## Optional

| Item | Notes |
|------|-------|
| TRRS cable | If using wired split connection (ZMK supports wireless only, no TRRS needed) |
| USB-C cable | For flashing firmware |
