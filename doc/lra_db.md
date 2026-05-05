# LRA Database — File Format Reference

Authoritative reference for the Loads Reference Axis (LRA) input files consumed
by `lra.py`.  One file per lifting surface; placed in `data/lra/`.

---

## File naming convention

```
lra_<surface>.json
```

| Surface tag | Example filename |
|---|---|
| `wing` | `lra_wing.json` |
| `htail` | `lra_htail.json` |
| `vtail` | `lra_vtail.json` |
| `fuselage` | `lra_fuselage.json` |

---

## Coordinate frame

All positions are expressed in the **global aircraft frame**:

- **Origin:** fuselage station zero, waterline zero, buttline zero
- **x-axis:** positive forward (nose direction)
- **y-axis:** positive starboard
- **z-axis:** defined by the coordinate system decision (see `decision.md` §4)

Units: metres (SI).

---

## JSON schema

```json
{
  "surface": "<surface_tag>",
  "stations": [
    {
      "station_id": "<string>",
      "position_m": [<x_m>, <y_m>, <z_m>],
      "normal_nd": [<nx>, <ny>, <nz>]
    }
  ]
}
```

### Top-level fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `surface` | string | yes | Must match the surface tag in the filename |
| `stations` | array | yes | Ordered list of LRA station objects; minimum 2 entries |

### Station object fields

| Field | Type | Unit | Required | Notes |
|---|---|---|---|---|
| `station_id` | string | — | yes | Unique within the file; e.g. `"WS0.000"`, `"WS3.500"` |
| `position_m` | float[3] | m | yes | Global-frame `[x_m, y_m, z_m]` of the LRA reference point |
| `normal_nd` | float[3] | — | yes | Unit vector in the direction of positive Cn (positive section normal force); magnitude must be 1.0 ± 1 × 10⁻⁴ |

---

## Conventions

- **Station ordering:** stations must be listed in the order the user intends
  along the LRA spine — from the inboard/forward end to the outboard/aft end.
  For a straight wing the natural order is increasing `y_m`.  For a winglet the
  last stations increase in `z_m` while `y_m` changes little.  For the fuselage
  LRA the natural order is increasing `x_m` (nose to tail).  `lra.py` does not
  enforce monotonicity on any single axis; it only checks that consecutive
  station spacing is non-zero (see validation rule 5).
- **Normal vector orientation:**
  - Wing: `normal_nd` points dorsally, approximately `[0, 0, 1]` for an
    undihedraled wing.
  - Horizontal tail: same convention as wing.
  - Vertical tail: `normal_nd` points in the positive-y (starboard) direction,
    approximately `[0, 1, 0]`.
  - Winglet: `normal_nd` rotates continuously from dorsal (`[0, 0, 1]`) at the
    winglet root to starboard (`[0, 1, 0]`) toward the winglet tip as the
    surface turns from horizontal to vertical.
  - Fuselage: `normal_nd` is typically `[0, 0, 1]` (upward) for vertical load
    reporting.
- **Chord direction:** not stored in this file.  Chordwise direction at each
  strip station is inferred from the aero database geometry (`c_m` and
  adjacent `y_m` values in the baseline CSV per `doc/loads_aero_db.md`).
- **Moment transfer:** full 3-D position offset between the strip c/4 point
  (from the aero database) and `position_m` is used to transfer strip moments
  to the LRA reference point.

---

## Validation performed by `lra.py`

1. `surface` field matches filename stem.
2. `stations` array contains at least 2 entries.
3. `position_m` arrays are length 3; all elements are finite floats.
4. `normal_nd` arrays are length 3; magnitude is 1.0 ± 1 × 10⁻⁴ (provide values to at least 4 significant decimal places).
5. Arc-length spacing between every pair of consecutive stations is > 0 (no coincident stations).
6. All `station_id` values are unique within the file.

---

## Example — wing LRA

```json
{
  "surface": "wing",
  "stations": [
    {
      "station_id": "WS0.000",
      "position_m": [12.50, 0.000, 2.10],
      "normal_nd": [0.0, 0.0, 1.0]
    },
    {
      "station_id": "WS1.500",
      "position_m": [12.75, 1.500, 2.13],
      "normal_nd": [0.0, -0.05234, 0.99863]
    },
    {
      "station_id": "WS3.000",
      "position_m": [13.00, 3.000, 2.19],
      "normal_nd": [0.0, -0.05234, 0.99863]
    }
  ]
}
```

*(Coordinates are illustrative; replace with actual aircraft geometry.)*

---

## Example — kinked LRA with winglet

The LRA continues past the wing tip and kinks upward into the winglet. Stations
`WT0.000` and `WT0.500` have nearly the same `y_m` as the last wing station but
increasing `z_m`. The `normal_nd` rotates from dorsal to starboard as the
surface turns vertical.

```json
{
  "surface": "wing",
  "stations": [
    {
      "station_id": "WS13.500",
      "position_m": [14.20, 13.500, 2.45],
      "normal_nd": [0.0, -0.05234, 0.99863]
    },
    {
      "station_id": "WS15.000",
      "position_m": [14.40, 15.000, 2.50],
      "normal_nd": [0.0, -0.05234, 0.99863]
    },
    {
      "station_id": "WT0.000",
      "position_m": [14.50, 15.100, 2.60],
      "normal_nd": [0.0, 0.0, 1.0]
    },
    {
      "station_id": "WT0.800",
      "position_m": [14.55, 15.150, 3.40],
      "normal_nd": [0.0, 1.0, 0.0]
    }
  ]
}
```

*(The `WT` stations mark the winglet portion. `normal_nd` at `WT0.000` is still
dorsal because the chord-plane is horizontal there; by `WT0.800` the winglet is
fully vertical so `normal_nd` points starboard. Intermediate stations would blend
the normal vector continuously.)*

---

## Example — fuselage LRA

Fuselage stations are ordered by increasing `x_m` (forward fuselage station to
aft fuselage station). The `y_m` and `z_m` coordinates track the structural
centreline. `normal_nd` is `[0, 0, 1]` (upward) for vertical load reporting.

```json
{
  "surface": "fuselage",
  "stations": [
    {
      "station_id": "FS5.000",
      "position_m": [5.000, 0.000, 1.20],
      "normal_nd": [0.0, 0.0, 1.0]
    },
    {
      "station_id": "FS8.500",
      "position_m": [8.500, 0.000, 1.20],
      "normal_nd": [0.0, 0.0, 1.0]
    },
    {
      "station_id": "FS12.000",
      "position_m": [12.000, 0.000, 1.20],
      "normal_nd": [0.0, 0.0, 1.0]
    },
    {
      "station_id": "FS18.000",
      "position_m": [18.000, 0.000, 1.20],
      "normal_nd": [0.0, 0.0, 1.0]
    }
  ]
}
```

*(Fuselage station `x_m` values are illustrative. The `position_m` x-coordinate
here follows the structural-frame sign convention: positive AFT, so fuselage
station values increase from nose to tail.)*
