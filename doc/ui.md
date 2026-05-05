# TUI Code Standards — `ui.py`

## Overview

The TUI follows a linear **input → analysis → output** workflow driven by
`rich` for display and `prompt_toolkit` for input. The aesthetic is deliberately
spartan: a 1990s engineering-program look — dark background, monochrome panels,
plain ASCII box art, no animations.

Compatibility target: macOS Terminal and standard Unix terminals.

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
with their names; Category F is labelled `"(Phase 2 — deferred)"` and is not
selectable until Phase 2. Returns the single-letter category ID (`"A"` through
`"E"`).

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
`data/conditions/<type>/` where `<type>` is the subdirectory name for the
selected category (e.g. `static_flight`, `dynamic_flight`). Returns the resolved
`pathlib.Path` to the selected file.

**Display units** — when `APP_CONFIG["display_units"] == "imperial"`, TUI result
tables convert SI values before display using named constants from `unit_convert.py`
(`N_LBF`, `NM_FTLBF`, `M_FT`). No bare numeric conversion literals are permitted
in display functions; all output files remain in SI regardless of this setting.

The module exposes a single `Console` instance (`console`) used by both `ui.py`
and `menu.py`. Do not instantiate additional consoles.

---

## Cross-platform notes

- `rich` detects terminal capabilities at import time. Do not force colour depth
  or unicode — let the library negotiate with the host terminal.
- Avoid `os.get_terminal_size()` calls; `rich` handles width negotiation
  internally.
- `prompt_toolkit` handles readline-style editing without additional
  configuration.
