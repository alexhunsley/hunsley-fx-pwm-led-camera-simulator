#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

OUTPUT_DIR = Path("generated_pwm_tables")

MIN_PWM_CYCLES_PER_EXPOSURE = 15.0
INTEGER_CYCLE_TOLERANCE = 1e-9

CANDIDATE_CRANK_FPS = [30, 40, 48, 50, 60, 72, 96, 100, 120, 144, 200, 240]

BASE_SETUPS = [
    {"fps": 24, "shutter_angle_deg": 172.8,
     "comments": "At 24 fps there are no good PWM LED options below 1 kHz PWM."},
    {"fps": 25, "shutter_angle_deg": 180.0,
     "comments": "At 25 fps there are no good PWM LED options below 1 kHz PWM."},
    {"fps": 30, "shutter_angle_deg": 216.0,
     "comments": "At 30 fps there are no good PWM LED options below 1 kHz PWM."},
]

LED_DEVICES = [
    {"pwm_hz": 400, "label": "400 Hz", "device": "old WS2812/WS2812B"},
    {"pwm_hz": 580, "label": "580 Hz*", "device": "APA102 global brightness"},
    {"pwm_hz": 1000, "label": "1 kHz", "device": "some SK6812 variants"},
    {"pwm_hz": 1200, "label": "1.2 kHz", "device": "SK6812"},
    {"pwm_hz": 2000, "label": "2 kHz", "device": "WS2813/14, newer WS2812"},
    {"pwm_hz": 2500, "label": "2.5 kHz", "device": "WS2801 class"},
    {"pwm_hz": 4700, "label": "4.7 kHz", "device": "SK9822"},
    {"pwm_hz": 8000, "label": "8 kHz", "device": "GS8208 / CS8812 class"},
    {"pwm_hz": 10000, "label": "10 kHz", "device": "WS2816B class"},
    {"pwm_hz": 19200, "label": "19.2 kHz", "device": "APA102 RGB PWM"},
    {"pwm_hz": 20000, "label": "20 kHz", "device": "generic high-frequency PWM"},
    {"pwm_hz": 26000, "label": "26 kHz", "device": "HD107S class"},
    {"pwm_hz": 27000, "label": "27 kHz", "device": "HD108 class"},
]

BASE_OK_MARK = "✅"
BASE_NOT_OK_MARK = "❌"
EMPTY_CELL = "-"

HUGO_TABLE_OPEN = """<div class="spaced-columns-table">
{{< centered-table border="1px" >}}"""
HUGO_TABLE_CLOSE = """{{< /centered-table >}}
</div>"""

FOOTNOTE_TEXT = (
    r"\* APA102's ~580 Hz figure refers to global-brightness modulation "
    "rather than its normal RGB PWM."
)

@dataclass(frozen=True)
class TableRow:
    led_pwm: str
    device: str
    base_rate_ok: str
    ideal_crank_fps: list[float]
    maybe_crank_fps: list[float]

def exposure_time_s(fps: float, shutter_angle_deg: float) -> float:
    return (shutter_angle_deg / 360.0) / fps

def pwm_cycles_per_exposure(pwm_hz: float, fps: float, shutter_angle_deg: float) -> float:
    return pwm_hz * exposure_time_s(fps, shutter_angle_deg)

def is_integer_cycles(value: float) -> bool:
    return math.isclose(value, round(value), rel_tol=0.0, abs_tol=INTEGER_CYCLE_TOLERANCE)

def classify_crank_rate(pwm_hz: float, crank_fps: float, shutter_angle_deg: float) -> str | None:
    cycles = pwm_cycles_per_exposure(pwm_hz, crank_fps, shutter_angle_deg)
    if cycles + INTEGER_CYCLE_TOLERANCE < MIN_PWM_CYCLES_PER_EXPOSURE:
        return None
    return "ideal" if is_integer_cycles(cycles) else "maybe"

def build_rows(base_fps: float, shutter_angle_deg: float) -> list[TableRow]:
    rows = []
    for led in LED_DEVICES:
        base_cycles = pwm_cycles_per_exposure(led["pwm_hz"], base_fps, shutter_angle_deg)
        base_ok = BASE_OK_MARK if base_cycles + INTEGER_CYCLE_TOLERANCE >= MIN_PWM_CYCLES_PER_EXPOSURE else BASE_NOT_OK_MARK

        ideal, maybe = [], []
        for crank_fps in CANDIDATE_CRANK_FPS:
            if crank_fps <= base_fps:
                continue
            cls = classify_crank_rate(led["pwm_hz"], crank_fps, shutter_angle_deg)
            if cls == "ideal":
                ideal.append(crank_fps)
            elif cls == "maybe":
                maybe.append(crank_fps)

        rows.append(TableRow(
            led_pwm=led["label"],
            device=led["device"],
            base_rate_ok=base_ok,
            ideal_crank_fps=ideal,
            maybe_crank_fps=maybe,
        ))
    return rows

def fmt_number(v: float) -> str:
    return f"{v:g}"

def fmt_fps_list(values: list[float]) -> str:
    return ", ".join(fmt_number(v) for v in values) if values else EMPTY_CELL

def markdown_table(rows: list[TableRow]) -> str:
    lines = [
        "| LED PWM | Example device/class | Base rate OK? | Ideal crank FPS | Maybe crank FPS |",
        "| ---: | --- | :---: | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row.led_pwm} | {row.device} | {row.base_rate_ok} | "
            f"{fmt_fps_list(row.ideal_crank_fps)} | {fmt_fps_list(row.maybe_crank_fps)} |"
        )
    return "\n".join(lines)

def write_markdown(path: Path, setup: dict, rows: list[TableRow]) -> None:
    fps = setup["fps"]
    shutter = setup["shutter_angle_deg"]
    ideal_explanation = (
        f"**Ideal crank FPS** *means at least {MIN_PWM_CYCLES_PER_EXPOSURE:g} nominal PWM cycles[^1] "
        "per exposure[^2] and an integer number of PWM cycles per exposure.*"
    )
    maybe_explanation = (
        f"**Maybe crank FPS** *means at least {MIN_PWM_CYCLES_PER_EXPOSURE:g} nominal PWM cycles "
        "per exposure, but not an integer number of cycles.*"
    )
    blocks = [
        f"## {fmt_number(fps)} fps base",
        f"Assuming we're using shutter angle of {fmt_number(shutter)}°:",
        HUGO_TABLE_OPEN,
        markdown_table(rows),
        HUGO_TABLE_CLOSE,
        f"**Comments:** {setup['comments']}",
        ideal_explanation,
        maybe_explanation,
        FOOTNOTE_TEXT,
    ]
    path.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")


def write_csv(path: Path, setup: dict, rows: list[TableRow]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow([
            "Shutter angle (deg)",
            "LED PWM",
            "Example device/class",
            "Base rate OK?",
            "Ideal crank FPS",
            "Maybe crank FPS",
        ])

        for row in rows:
            writer.writerow([
                fmt_number(setup["shutter_angle_deg"]),
                row.led_pwm,
                row.device,
                row.base_rate_ok,
                fmt_fps_list(row.ideal_crank_fps),
                fmt_fps_list(row.maybe_crank_fps),
            ])

def validate_current_tables() -> None:
    rows24 = {r.led_pwm: r for r in build_rows(24, 172.8)}
    assert rows24["2 kHz"].ideal_crank_fps == [30, 40, 48, 60]
    assert rows24["2 kHz"].maybe_crank_fps == [50]

    rows25 = {r.led_pwm: r for r in build_rows(25, 180)}
    assert rows25["1.2 kHz"].ideal_crank_fps == [30, 40]
    assert rows25["1.2 kHz"].maybe_crank_fps == []

    rows30 = {r.led_pwm: r for r in build_rows(30, 216)}
    assert rows30["2.5 kHz"].ideal_crank_fps == [50, 60, 100]
    assert rows30["2.5 kHz"].maybe_crank_fps == [40, 48, 72, 96]

    assert rows24["400 Hz"].base_rate_ok == BASE_NOT_OK_MARK
    assert rows24["1 kHz"].base_rate_ok == BASE_OK_MARK

def main() -> None:
    validate_current_tables()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for setup in BASE_SETUPS:
        rows = build_rows(setup["fps"], setup["shutter_angle_deg"])
        stem = f"pwm_crank_rates_{fmt_number(setup['fps'])}fps"
        md_path = OUTPUT_DIR / f"{stem}.md"
        csv_path = OUTPUT_DIR / f"{stem}.csv"
        write_markdown(md_path, setup, rows)
        write_csv(csv_path, setup, rows)
        print(f"Wrote {md_path}")
        print(f"Wrote {csv_path}")

if __name__ == "__main__":
    main()
