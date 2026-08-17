# Calibration Topic

## 1. Importance
Calibration is critical for the Huenit robotic arm to ensure consistent pen pressure and accurate drawing within the 125mm x 125mm area. Without calibration, the pen may drag or fail to reach the paper.

## 2. Process
- **Tool**: `huenit_draw.py calibrate`
- **Steps**:
    1. Manually jog the arm to the home position.
    2. The arm touches several points on the surface to determine the plane and tilt.
    3. The Z-height for pen-up (`Z_UP=6.0mm`) and pen-down is established.
- **Output**: Writes `calibration.json` which is consumed by all hardware control scripts.

## 3. Operations
Calibration must be run after every physical restart of the arm. It is triggered by the operator using a desktop shortcut: `Calibrate Robot Ross.command`.

## 4. Uncertainty & Contradictions
- **Surface Leveling**: Software calibration can compensate for some tilt (`TILT_SLOPE`), but physical documentation emphasizes that the table should be as level as possible. The limit of software-based tilt compensation is not explicitly documented.
- **Auto-Calibration**: There is no mention of a "re-calibration" trigger during long-running sessions, which might be necessary if the arm drifts or the surface shifts.

## 5. FAQ (from `huenit_draw.log`, 38 calibration runs 2026-03-28 to 2026-07-18)

**Q: What commands does calibration actually send to the arm?**
A: Almost entirely `G1 Z<value> F<rate>` moves, each immediately followed by `M400` (wait for motion complete) before the next command — this pairing keeps the control script in sync with the firmware over serial. Three feedrates, three purposes: `F50` for the fine 0.1mm touch-probe jog (93% of all moves), `F100` for the coarse 0.5mm "find the surface" step, `F800` for travel/lift moves between the 4 tilt-probe points.

**Q: I got `TIMEOUT waiting for ok on: G21` right after connecting. What do I do?**
A: Seen once, right after the serial port was opened with `DTR=LOW (no reset)`, which skips the controller's auto-reset-on-connect and can leave the firmware unresponsive to the first command. Close and reopen the connection (allow the normal boot sequence) rather than retrying on the same connection — this fixed it immediately in the one recorded case.

**Q: My saved calibration shows `tilt_y=0.000 tilt_x=0.000` — is my surface confirmed level?**
A: Not necessarily. The 4-point tilt probe asks the operator to fine-jog (W/S) at each cross-point, then confirm with Enter. Pressing Enter immediately without jogging records that point as "already touching" (0.00mm) — so an all-zero result can mean a genuinely flat surface, or an operator who accepted the default at every point without re-touching. In sessions where the operator did fine-jog (March 2026 data), `tilt_y` typically measured 0.038–0.061 mm/mm and `tilt_x` ±0.01 mm/mm — a real, repeatable slope along Y. `z_up` itself has never needed adjustment across any of the 38 runs; 6.00mm has held since the first calibration.

---
**Sources:**
- `~/.openclaw/workspace/skills/huenit/huenit_draw.py`
- `AGENTS/CONTEXT/robot_ross_artist.md`
- `skills/huenit/huenit_draw.log` (operational log)
