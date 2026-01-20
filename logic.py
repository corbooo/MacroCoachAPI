from __future__ import annotations

from datetime import date, timedelta
from typing import Optional, List, Dict, Any

from models import DailyMacro, Weight, Target


def _r2(x: Optional[float]) -> Optional[float]:
    return None if x is None else round(x, 2)


def _r0(x: Optional[float]) -> Optional[float]:
    return None if x is None else round(x)


def build_weekly_insight(*, start: date, macro_rows: List[DailyMacro], weight_rows: List[Weight], target: Optional[Target]) -> Dict[str, Any]:
    end = start + timedelta(days=7)

    days_logged = len(macro_rows)
    adherence = days_logged / 7

    if days_logged > 0:
        avg_calories = sum(r.calories for r in macro_rows) / days_logged
        avg_protein = sum(r.protein_g for r in macro_rows) / days_logged
        avg_carbs = sum(r.carbs_g for r in macro_rows) / days_logged
        avg_fat = sum(r.fat_g for r in macro_rows) / days_logged
    else:
        avg_calories = avg_protein = avg_carbs = avg_fat = None

    if len(weight_rows) >= 2:
        start_weight = weight_rows[0].weight_lbs
        end_weight = weight_rows[-1].weight_lbs
        weight_change = end_weight - start_weight
    else:
        start_weight = weight_rows[0].weight_lbs if len(weight_rows) == 1 else None
        end_weight = None
        weight_change = None

    total_calories = sum(r.calories for r in macro_rows)
    total_protein = sum(r.protein_g for r in macro_rows)
    total_carbs = sum(r.carbs_g for r in macro_rows)
    total_fat = sum(r.fat_g for r in macro_rows)

    targets_block = None
    vs_targets = None

    if target:
        targets_block = {
            "calories_target": target.calories_target,
            "protein_target_g": target.protein_target_g,
            "carbs_target_g": target.carbs_target_g,
            "fat_target_g": target.fat_target_g,
        }

        avg_cal_delta = (avg_calories - target.calories_target) if avg_calories is not None else None
        avg_pro_delta = (avg_protein - target.protein_target_g) if avg_protein is not None else None
        avg_car_delta = (avg_carbs - target.carbs_target_g) if avg_carbs is not None else None
        avg_fat_delta = (avg_fat - target.fat_target_g) if avg_fat is not None else None

        if days_logged > 0:
            total_cal_delta = total_calories - target.calories_target * days_logged
            total_pro_delta = total_protein - target.protein_target_g * days_logged
            total_car_delta = total_carbs - target.carbs_target_g * days_logged
            total_fat_delta = total_fat - target.fat_target_g * days_logged
        else:
            total_cal_delta = total_pro_delta = total_car_delta = total_fat_delta = None

        vs_targets = {
            "avg": {
                "calories_delta": _r0(avg_cal_delta),
                "protein_delta_g": _r2(avg_pro_delta),
                "carbs_delta_g": _r2(avg_car_delta),
                "fat_delta_g": _r2(avg_fat_delta),
            },
            "total_over_logged_days": {
                "calories_delta": _r0(total_cal_delta),
                "protein_delta_g": _r2(total_pro_delta),
                "carbs_delta_g": _r2(total_car_delta),
                "fat_delta_g": _r2(total_fat_delta),
            }
        }

    daily_macros = [
        {"day": r.day, "calories": r.calories, "protein_g": r.protein_g, "carbs_g": r.carbs_g, "fat_g": r.fat_g}
        for r in macro_rows
    ]
    daily_weights = [{"day": r.day, "weight_lbs": r.weight_lbs} for r in weight_rows]

    return {
        "week_start": start,
        "week_end_exclusive": end,
        "adherence_%": _r2(adherence * 100),
        "macros": {
            "days_logged": days_logged,
            "avg_calories": _r2(avg_calories),
            "avg_protein_g": _r2(avg_protein),
            "avg_carbs_g": _r2(avg_carbs),
            "avg_fat_g": _r2(avg_fat),
            "daily_macros": daily_macros,
            "totals": {
                "total_calories": total_calories,
                "total_protein": total_protein,
                "total_carbs": total_carbs,
                "total_fat": total_fat,
            },
        },
        "weight": {
            "entries": len(weight_rows),
            "start_weight_lbs": start_weight,
            "end_weight_lbs": end_weight,
            "change_lbs": _r2(weight_change),
            "daily_weights": daily_weights,
        },
        "targets": targets_block,
        "vs_targets": vs_targets,
    }


def build_rolling_insights(*, days: int, start: date, end: date, macro_rows: List[DailyMacro], weight_rows: List[Weight]) -> Dict[str, Any]:
    macro_days = len(macro_rows)

    if macro_days > 0:
        avg_calories = sum(r.calories for r in macro_rows) / macro_days
        avg_protein = sum(r.protein_g for r in macro_rows) / macro_days
    else:
        avg_calories = avg_protein = None

    if len(weight_rows) >= 2:
        weight_trend = weight_rows[-1].weight_lbs - weight_rows[0].weight_lbs
    else:
        weight_trend = None

    return {
        "window_days": days,
        "range": {"start": start, "end": end},
        "macros": {
            "days_logged": macro_days,
            "avg_calories": round(avg_calories, 1) if avg_calories is not None else None,
            "avg_protein": round(avg_protein, 1) if avg_protein is not None else None,
        },
        "weight": {
            "entries": len(weight_rows),
            "trend_lbs": round(weight_trend, 2) if weight_trend is not None else None,
            "direction": (
                "up" if weight_trend is not None and weight_trend > 0
                else "down" if weight_trend is not None and weight_trend < 0
                else "flat"
            ),
        },
    }

def calorie_adjustment(days: int, start: date, end: date, macro_rows: List[DailyMacro], weight_rows: List[Weight], desired_lbs_per_week: float) -> Dict[str, Any]:
    macro_days = len(macro_rows)
    if macro_days > 0:
        avg_calories = sum(r.calories for r in macro_rows) / macro_days
        avg_protein = sum(r.protein_g for r in macro_rows) / macro_days
        avg_carbs = sum(r.carbs_g for r in macro_rows) / macro_days
        avg_fat = sum(r.fat_g for r in macro_rows) / macro_days
    else:
        avg_calories = avg_protein = avg_carbs = avg_fat = None

    current_rate_lbs_per_week: Optional[float] = None
    trend_lbs: Optional[float] = None
    span_days: Optional[int] = None
    start_weight: Optional[float] = None
    end_weight: Optional[float] = None

    if len(weight_rows) >= 2:
        start_weight = weight_rows[0].weight_lbs
        end_weight = weight_rows[-1].weight_lbs
        trend_lbs = end_weight - start_weight

        span_days = (weight_rows[-1].day - weight_rows[0].day).days
        if span_days and span_days > 0:
            current_rate_lbs_per_week = (trend_lbs / span_days) * 7.0
    elif len(weight_rows) == 1:
        start_weight = weight_rows[0].weight_lbs

    kcal_adjustment_per_day: Optional[float] = None
    capped_kcal_adjustment_per_day: Optional[float] = None
    recommended_daily_calories: Optional[float] = None
    HARD_CAP = 250.0  # kcal/day

    notes: List[str] = []
    warnings: List[str] = []

    if len(weight_rows) >= 21 and macro_days >= 21:
        confidence = "high"
    elif len(weight_rows) >= 14 and macro_days >= 14:
        confidence = "medium"
    else:
        confidence = "low"

    if len(weight_rows) < 2:
        warnings.append("Not enough weight entries to estimate a trend (need at least 2).")
    if macro_days == 0:
        warnings.append("No macro entries found in the lookback window.")

    if current_rate_lbs_per_week is not None:
        delta_rate = desired_lbs_per_week - current_rate_lbs_per_week
        kcal_adjustment_per_day = (delta_rate * 3500.0) / 7.0

        # If confidence is low, be more conservative
        cap = HARD_CAP if confidence != "low" else min(HARD_CAP, 100.0)
        capped_kcal_adjustment_per_day = max(-cap, min(cap, kcal_adjustment_per_day))

        # Round to the nearest 5 kcal/day for nicer UX
        capped_kcal_adjustment_per_day = round(capped_kcal_adjustment_per_day / 5.0) * 5.0

        if avg_calories is not None:
            recommended_daily_calories = avg_calories + capped_kcal_adjustment_per_day

        notes.append("Weight trend computed using first/last weigh-in over the window (simple slope).")
        notes.append("Calorie adjustment uses 3500 kcal ≈ 1 lb and is capped for safety.")
        if confidence == "low":
            notes.append("Low confidence: adjustment cap reduced to 100 kcal/day.")
    else:
        delta_rate = None

    if current_rate_lbs_per_week is None:
        status = "insufficient_data"
    else:
        # “on_track” if within ±0.05 lb/week of desired
        if abs(desired_lbs_per_week - current_rate_lbs_per_week) <= 0.05:
            status = "on_track"
        elif desired_lbs_per_week > current_rate_lbs_per_week:
            status = "increase_calories"
        else:
            status = "decrease_calories"

    return {
            "window_days_requested": days,
            "range": {"start": start, "end": end},
            "status": status,
            "confidence": confidence,
            "macros": {
                "days_logged": macro_days,
                "avg_calories": _r2(avg_calories),
                "avg_protein_g": _r2(avg_protein),
                "avg_carbs_g": _r2(avg_carbs),
                "avg_fat_g": _r2(avg_fat),
            },
            "weight": {
                "entries": len(weight_rows),
                "start_weight_lbs": start_weight,
                "end_weight_lbs": end_weight,
                "trend_lbs": _r2(trend_lbs),
                "span_days": span_days,
                "current_rate_lbs_per_week": _r2(current_rate_lbs_per_week),
                "desired_rate_lbs_per_week": _r2(desired_lbs_per_week),
                "delta_rate_lbs_per_week": _r2(delta_rate) if current_rate_lbs_per_week is not None else None,
            },
            "recommendation": {
                "calorie_adjustment_per_day": _r0(capped_kcal_adjustment_per_day),
                "uncapped_calorie_adjustment_per_day": _r0(kcal_adjustment_per_day),
                "recommended_daily_calories": _r0(recommended_daily_calories),
            },
            "notes": notes,
            "warnings": warnings,
        }