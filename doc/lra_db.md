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
| `normal_nd` | float[3] | — | yes | Unit vector in the direction of positive Cn (positive section normal force); magnitude must be 1.0 ± 1 × 10⁻⁶ |

---

## Conventions

- **Station ordering:** stations must be listed in order of increasing spanwise
  `y_m` (index 1 of `position_m`).  `lra.py` raises `ValueError` if this
  ordering is violated.
- **Normal vector orientation:**
  - Wing: `normal_nd` points dorsally, approximately `[0, 0, 1]` for an
    undihedraled wing.
  - Horizontal tail: same convention as wing.
  - Vertical tail: `normal_nd` points in the positive-y (starboard) direction,
    approximately `[0, 1, 0]`.
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
4. `normal_nd` arrays are length 3; magnitude is 1.0 ± 1 × 10⁻⁶.
5. Stations are ordered by increasing `y_m`.
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
      "normal_nd": [0.0, -0.052, 0.999]
    },
    {
      "station_id": "WS3.000",
      "position_m": [13.00, 3.000, 2.19],
      "normal_nd": [0.0, -0.052, 0.999]
    }
  ]
}
```

*(Coordinates are illustrative; replace with actual aircraft geometry.)*
