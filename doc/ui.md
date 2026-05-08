# TUI Code Standards — `ui.py`

## Overview

The TUI follows a linear **input → analysis → output** workflow driven by
`rich` for display and `prompt_toolkit` for input. The aesthetic is deliberately
spartan: a 1990s engineering-program look — dark background, monochrome panels,
plain ASCII box art, no animations.

Compatibility target: macOS Terminal, Windows Powwershell, and standard Unix terminals.

---

## Dependency roles

| Library | Role |
|---|---|
| `rich` | All display output — panels, tables, styled text |
| `prompt_toolkit` | All user input — prompts, tab-completion, inline validation |

Never use `print()` or `input()` directly. Route everything through the two
libraries above so colour stripping and cross-platform encoding are handled
consistently.

---

## Workflow pattern: input → analysis → output

Every operation follows three stages in strict order. No stage is skipped or
combined with another.

```
1. INPUT    — collect everything the calculation needs before any computation
2. ANALYSIS — call the computation engine; may chain (analysis 1, 2, … n)
3. OUTPUT   — display results; never interleaved with input prompts
```

A handler function maps cleanly onto this pattern:

```python
def handle_run_analysis():
    # --- INPUT ---
    analysis_type  = ui.select_analysis_type()          # "A" through "F"
    csv_path       = ui.select_condition_csv(analysis_type)
    conditions_df  = condition.load_conditions(csv_path, analysis_type)

    # --- ANALYSIS ---
    results = []
    for _, row in conditions_df.iterrows():
        trim_state    = trim.solve_trim(row)
        section_loads = loads.compute_loads(trim_state, row)
        nastran_out.write(section_loads, row)
        results.append(section_loads)

    # --- OUTPUT ---
    ui.print_batch_summary(results)
    ui.press_enter_to_continue()
```

When multiple analysis steps depend on each other, run them sequentially and
accumulate results before any display call.

---

## Color palette

| Token | Rich markup | Purpose |
|---|---|---|
| Primary | `[cyan]` | Labels, column headers, panel borders, section titles |
| Warning | `[yellow]` | Non-fatal notices |
| Error | `[red]` | Validation failures, out-of-range errors |
| Dim | `[dim]` | Supplemental hints in menu text only |
| Bold | `[bold]` | Panel titles only |

Do **not** introduce additional colours (green, magenta, blue, etc.). If a new
semantic category is needed, use a combination of the tokens above (e.g.
`[bold red]`).

---

## Symbolic elements

Keep decoration minimal.

**Allowed:**

- `Panel` — one per logical result block; border always `cyan`
- `Table` — inside panels; `box=None`; `show_header=True` for data tables,
  `show_header=False` for selection lists

**Not allowed:**

- Progress bars, spinners, live displays, or any animated element
- Emoji or pictographic characters
- Custom box styles (keep `box=None` on tables)
- Nested panels

---

## Panel conventions

```python
console.print(Panel(
    content,                          # Rich renderable (Table, str, markup str)
    title="[bold]Title[/bold]",       # Short noun phrase; bold only
    border_style="cyan",              # Always cyan; never change per-panel
))
```

Panel titles are noun phrases, not sentences. Examples:

- `"Trim Balance"` — correct
- `"Please review the trim balance below:"` — incorrect

---

## Table conventions

**Selection lists** (file pickers, condition lists):

```python
tbl = Table(show_header=False, box=None, padding=(0, 2))
tbl.add_column("Key", style="cyan")   # numeric key, cyan
tbl.add_column("Item")                # filename or label, unstyled
```

**Result tables** (data output):

```python
tbl = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
tbl.add_column("Label", style="cyan", justify="right")   # first col, labels
tbl.add_column("Value",               justify="right")   # data cols, right-aligned
```

Right-align all numeric columns. Label the first column with `style="cyan"`.
Do not apply per-cell styles.

---

## Prompt conventions

All prompts are written in `prompt_toolkit`. Format:

```
Noun phrase: <cursor>
```

- End with `: ` (colon-space), no trailing newline
- Lowercase except proper nouns and acronyms
- No question marks; use imperative noun phrases

| Correct | Incorrect |
|---|---|
| `"Input angle of attack: "` | `"Enter your angle of attack? "` |
| `"Select condition file: "` | `"Which file do you want?"` |
| `"Input gross weight (N): "` | `"Weight:"` |

Tab completion via `WordCompleter` is required on all selection prompts.
Numeric prompts use inline validation for range and type checking.

---

## Error and status messages

Print inline before returning control, not inside a panel.

```python
# range / computation error
console.print(f"[red]Error: {e}[/red]")

# non-fatal / informational
console.print("[yellow]No conditions found in file.[/yellow]")

# action in progress (single line, no panel)
console.print("[cyan]Computing loads...[/cyan]")
```

Never raise a dialog or prompt after an error — print the message and return to
the menu loop.

---

## Navigation

Every handler that shows output must end with:

```python
ui.press_enter_to_continue()
```

This holds the result on screen until the user is ready to return to the menu.

The main menu loop is the only place that renders the top-level menu panel.
There is no submenu state — every operation returns to the top-level menu.

---

## Module structure (`ui.py`)

Organise functions in this order, separated by comment banners:

```
# Analysis-type selection     — select_analysis_type, select_condition_csv
# File-selection helpers      — select_lra_file, select_mass_file, select_aero_file
# Manual numeric input         — prompt_float, prompt_int, ask_unit
# Output helpers — single     — print_trim_result, print_loads_table
# Output helpers — batch      — print_section_loads, print_batch_summary,
#                                print_aeroelastic_results
```

**`select_analysis_type()`** — renders a numbered panel listing Categories A–F
with their names. Category F is labelled `"(Phase 2 — deferred)"` and is not
selectable until Phase 2. Category E (Flap / High-Lift) is Phase 1 and is
selectable. Returns the single-letter category ID (`"A"` through `"E"`).

The module-level dict `CATEGORY_LABELS` in `ui.py` is the **canonical source**
for all TUI menu label strings; do not duplicate these strings elsewhere:

```python
CATEGORY_LABELS = {
    "A": "Static Flight Loads (SFL)",
    "B": "Dynamic Flight Loads (DFL)",
    "C": "Static Ground Loads (SGL)",
    "D": "Dynamic Ground Loads (DGL)",
    "E": "Flap / High-Lift Loads (FLAPS)",
    "F": "Control Surface Loads (CONTROLS) — Phase 2 — deferred",
}
```

The module-level dict `CATEGORY_SUBDIR` maps category IDs to the
`data/conditions/` subdirectory name used by `select_condition_csv`:

```python
CATEGORY_SUBDIR = {
    "A": "static_flight",
    "B": "dynamic_flight",
    "C": "static_ground",
    "D": "dynamic_ground",
    "E": "flap",
    "F": "control_surface",
}
```

**`select_condition_csv(analysis_type)`** — lists CSV files found in
`<data_root>/conditions/<type>/` where `<data_root>` is `APP_CONFIG["data_root"]`
(default: `data/` relative to project root; user-configurable per Decision 22)
and `<type>` is the subdirectory name for the selected category (e.g.
`static_flight`, `dynamic_flight`). Returns the resolved `pathlib.Path` to the
selected file.

**Display units** — when `APP_CONFIG["display_units"] == "imperial"`, TUI result
tables convert SI values before display using named constants from `unit_convert.py`
(`N_LBF`, `NM_FTLBF`, `M_FT`). No bare numeric conversion literals are permitted
in display functions; all output files remain in SI regardless of this setting.

**Airspeed and altitude dual display** — regardless of the `display_units`
setting, airspeed and altitude are always shown in both SI and aviation units:

| Quantity | SI display | Aviation display |
|---|---|---|
| Airspeed | m/s | knots (using `M_S_KTS`) |
| Altitude | m | feet (using `M_FT`) |

Format: `<SI_value> m/s (<KTAS_value> kts)` and `<SI_value> m (<FT_value> ft)`.
This applies to condition summaries, trim balance tables, and batch result tables.

The module exposes a single `Console` instance (`console`) used by both `ui.py`
and `menu.py`. Do not instantiate additional consoles.

---

## Numeric input validation ranges (Decision 21)

All numeric prompts enforce the ranges below using inline `prompt_toolkit`
validation. Values outside the range show a `[red]` inline error and refuse
submission. Values that exceed a "soft limit" (flagged range) show a `[yellow]`
warning and ask the user to confirm before proceeding; they are not rejected
outright.

| Variable | Hard limits | Soft / confirm-required range | Notes |
|---|---|---|---|
| Pressure altitude `h_m` | 0 – 15 850 m | — | 51 900 ft troposphere + lower stratosphere |
| Equivalent airspeed `v_eas_m_s` | 25 – 260 m/s | aircraft-specific | ~50–500 kts |
| CG position `x_cg_nd` | 0 – 1 (fraction MAC) | outside 0.05–0.60 → confirm | 5–60 % MAC normal range; warn if outside |
| Gross mass `m_ac_kg` | > 0 | outside MFL–MRW → confirm | MFL = Minimum Flight Weight; MRW = Maximum Ramp Weight; values from aircraft config |
| Angle of attack `alpha_deg` | −30 – +40 deg | — | |
| Sideslip `beta_deg` | −40 – +40 deg | — | |
| Normal load factor `nz_nd` | −3.0 – +5.0 | — | Wider than FAR 25 to accommodate ferry and failure cases |

When a soft-limit confirmation is required:

```python
console.print(f"[yellow]Warning: value {val} is outside the normal range "
              f"{lo}–{hi}. Confirm? (y/n): [/yellow]", end="")
```

The user must enter `y` or `yes` (case-insensitive) to continue. Any other
input re-presents the prompt.

---

## VMT / SMT charts (Decisions 20 and 29)

VMT (V=Shear, M=Moment, T=Torque) section load plots are produced using
`matplotlib` in a separate pop-up window. The TUI pauses while the window is
open; `plt.show()` blocks until the user closes it.

**Two access paths (Decision 29, Option C):**
- **TUI "Review cases" menu item** — interactive session; calls the helpers
  below against in-memory results or a previously written VMT CSV.
- **`tools/plot_vmt.py` standalone script** — offline use; reads saved VMT
  CSV files without launching the TUI. See `doc/architecture.md
  §tools/plot_vmt.py` for CLI usage.

The TUI chart helpers are called from the "Review cases" menu item (not
automatically after each batch run):

```python
ui.show_vmt_single(section_loads_df, condition_id, surface)
    # Opens one matplotlib figure with 3 subplots: Vz, Mx, My vs. spanwise station

ui.show_vmt_compare(loads_list, condition_ids, surface)
    # Overlays multiple conditions on the same subplot axes for comparison

ui.show_vmt_vs_envelope(section_loads_df, envelope_df, condition_id, surface)
    # Plots a single condition against a reference envelope (loaded from CSV)
```

Inertia and aerodynamic contributions are plotted as separate series using
`[cyan]` and unstyled (white/default) line colors so the balance is visible.

Chart display rules:
- Always use `plt.show()` (blocking); never `plt.savefig()` from within the TUI
- The TUI prints `[cyan]Displaying VMT chart — close window to continue[/cyan]`
  before the `plt.show()` call
- A headless environment (no display) raises `RuntimeError`; the handler catches
  it, prints `[red]Error: no display available for chart[/red]`, and returns to
  the menu

The `CATEGORY_SUBDIR`, `CATEGORY_LABELS`, and `CATEGORY_FILE_PREFIX` dicts
remain the sole source of category metadata; chart functions receive the surface
tag and condition data as arguments, not a category ID.

---

## Pre-Analysis Check 1 — Aero Data Review

Check 1 is the primary aerodynamic model verification step. Its input flow is
two-stage by design, enforcing a clear separation between total-airplane
aerodynamics and per-surface detail:

**Stage 1 — Total airplane composition (required):**

```
ui.select_total_airplane_files()
```

Presents all available baseline `aero_*.csv` files. The user must select every
surface that contributes to the total airplane (wing, horizontal tail, vertical
tail, fuselage). Selection of at least one surface is enforced — pressing Enter
without a choice re-prompts with an error. The prompt text explicitly reads:
`"Total Airplane Components — select ALL contributing surfaces"`.

**Stage 2 — Detail surface (single-select from Stage 1 list):**

```
ui.select_detail_surface(airplane_paths)
```

Presents only the surfaces already selected in Stage 1. The user picks one for
the detailed strip coefficient table and VMT plot. If only one surface was
selected in Stage 1, this step is skipped automatically.

**Why this order matters:**

The total-airplane CL/CM vs alpha sweep and derivative table are computed from
the Stage 1 set using baseline coefficients (no control-surface increments).
The detail strip table and VMT are computed from the Stage 2 surface loaded
with any control-surface increment files specified by the user. The two
calculations are always kept separate so neither contaminates the other.

**Output sequence for Check 1:**

1. Confirmation line: `[cyan]Total airplane: N surface(s) — <names>[/cyan]`
2. Strip coefficient table — detail surface at nominal (α, β, M)
3. Integrated totals panel — detail surface lift, drag, pitching moment
4. VMT plot — detail surface section loads at nominal state
5. CL / CM vs α chart — total airplane, all Stage 1 surfaces summed, with
   nominal α marked
6. Airplane aerodynamic derivatives panel — CL0, CLα, CM0, CMα from linear
   regression over the full alpha grid

---

## LRA 3D viewer (Decision 31)

The "L — View LRA" menu option displays a station table followed immediately by a
3D interactive chart in the default browser. The chart is produced by
`ui.show_lra_3d(surface, stations)` using **Plotly** (`plotly.graph_objects`).
The VMT charts use matplotlib; the LRA 3D viewer uses Plotly. They are separate
tools for separate purposes.

```python
ui.show_lra_3d(surface: str, stations: list) -> None
    # Opens a Plotly Scatter3d figure in the default browser showing:
    #   - LRA spine: cyan connected line + markers at all station positions
    #   - Unit normals: gold line segments, each scaled to 8% of the spine
    #     bounding-box diagonal
    #   - Station labels: white text beside each station (every other label
    #     when more than 14 stations, to avoid overlap)
```

Chart display rules:
- Uses `fig.show()` (Plotly); opens the default browser automatically
- The TUI prints `[cyan]Opening LRA 3D viewer in browser — close tab when done[/cyan]`
  before `fig.show()`
- If `plotly` is not installed, prints `[red]Error: plotly unavailable: ...[/red]`
  and returns to the menu; no further error handling is needed (no display
  environment required)
- Equal spatial scale is enforced via `scene.aspectmode="data"` in the layout

---

## Non-convergence display (Decision 23)

When a condition is skipped due to non-convergence:

```python
console.print(f"[yellow]Warning: trim did not converge for condition "
              f"{condition_id}. Skipped.[/yellow]")
```

The batch summary table marks the skipped condition with status `SKIP` in a
`[yellow]` cell. Non-converged conditions are omitted from the NASTRAN output
file. The count of skipped conditions is printed in the batch summary footer:

```
[yellow]1 condition(s) skipped due to non-convergence.[/yellow]
```

No dialog or additional prompt is shown; the program continues automatically
to the next condition.

---

## Cross-platform notes

- `rich` detects terminal capabilities at import time. Do not force colour depth
  or unicode — let the library negotiate with the host terminal.
- Avoid `os.get_terminal_size()` calls; `rich` handles width negotiation
  internally.
- `prompt_toolkit` handles readline-style editing without additional
  configuration.
