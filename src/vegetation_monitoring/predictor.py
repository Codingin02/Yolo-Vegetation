from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from copy import deepcopy
import csv
from datetime import datetime, timezone
from functools import lru_cache
import math
import os
from pathlib import Path
import pickle
import random
import tempfile
from typing import Any

from .storage import PROJECT_ROOT


EVIDENCE_PATH = PROJECT_ROOT / "data" / "prediction" / "prediction_evidence.csv"
PREDICTOR_PATH = PROJECT_ROOT / "models" / "growth_predictor.pkl"
TARGET = "clearance_closure_rate_m_per_day"
CROWN_TARGET = "crown_extension_rate_m_per_day"
TARGETS = (TARGET, CROWN_TARGET)
NUMERIC_FEATURES = (
    "tree_height_m", "crown_width_m", "crown_area_m2", "clearance_m", "month",
    "temperature", "humidity", "rainfall", "previous_height_m", "previous_crown_width_m",
    "previous_crown_area_m2", "previous_clearance_m", "elapsed_days", "time_since_last_pruning_days",
)
FEATURE_LIMITS = (
    (0, 200), (0, 200), (0, 100000), (0, 1000), (1, 12), (-30, 60), (0, 100),
    (0, 20000), (0, 200), (0, 200), (0, 100000), (0, 1000), (0, 36525), (0, 36525),
)
STAGES = {"young", "established", "mature"}
SEVERITIES = ("unknown", "light", "medium", "heavy")
CANDIDATES = ("HistGradientBoostingRegressor", "MLP")
# These are operational minimums, not a claim of statistical adequacy.
MIN_ROWS, MIN_GROUPS = 60, 10


def read_evidence(path: Path = EVIDENCE_PATH) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def observed_rate(row: Mapping[str, Any], target: str = TARGET) -> dict[str, Any]:
    """A reviewed interval is evidence; height, DBH and crown width are not closure targets."""
    if target not in TARGETS:
        raise ValueError("unsupported_rate_target")
    if not _true(row.get("verified")) or _true(row.get("synthetic")) or _true(row.get("fabricated")):
        raise ValueError("verified_real_observations_required")
    if str(row.get("observation_type") or "") != "individual_longitudinal":
        raise ValueError("row_level_longitudinal_observations_required")
    if str(row.get("species") or "").lower().strip() not in {"angsana", "pterocarpus indicus"}:
        raise ValueError("angsana_observations_required")
    stage = _stage(row.get("tree_stage"))
    if stage not in STAGES:
        raise ValueError("compatible_tree_stage_required")
    for name in ("source_id", "source_url", "tree_id", "conductor_id", "measurement_method"):
        if not str(row.get(name) or "").strip():
            raise ValueError(f"{name}_required")
    if row.get("previous_conductor_id") not in (None, "", row["conductor_id"]):
        raise ValueError("conductor_changed_during_interval")
    if row.get("previous_measurement_method") not in (None, "", row["measurement_method"]):
        raise ValueError("measurement_method_changed_during_interval")
    if not _true(row.get("comparable_measurements_verified")):
        raise ValueError("comparable_measurements_required")
    start = _timestamp(row.get("measurement_start_date"))
    end = _timestamp(row.get("measurement_end_date"))
    elapsed = (end - start).total_seconds() / 86400
    supplied_elapsed = _number(row.get("elapsed_days"), "elapsed_days", 0, 36525)
    if elapsed <= 0 or abs(elapsed - supplied_elapsed) > max(0.01, elapsed * 0.001):
        raise ValueError("inconsistent_observation_interval")
    pruning = row.get("pruning_date")
    if pruning not in (None, "") and start < _timestamp(pruning) <= end:
        raise ValueError("pruning_during_growth_interval")
    if target == TARGET:
        first = _number(row.get("previous_clearance_m"), "previous_clearance_m", 0, 1000)
        last = _number(row.get("current_clearance_m"), "current_clearance_m", 0, 1000)
        rate = (first - last) / elapsed
    else:
        if not _true(row.get("extension_toward_conductor_verified")) or not str(row.get("measurement_axis_id") or ""):
            raise ValueError("verified_directional_crown_extension_required")
        first = _number(row.get("crown_extension_start_m"), "crown_extension_start_m", 0, 200)
        last = _number(row.get("crown_extension_end_m"), "crown_extension_end_m", 0, 200)
        rate = (last - first) / elapsed
    if row.get(target) not in (None, "") and not math.isclose(_finite(row[target], target), rate, rel_tol=1e-6, abs_tol=1e-9):
        raise ValueError("supplied_rate_does_not_match_measurements")
    return {
        "status": "ok", "target": target, "rate_m_per_day": rate,
        "rate_low_m_per_day": None, "rate_high_m_per_day": None,
        "model": "observed_interval", "source": str(row["source_id"]),
        "tree_id": str(row["tree_id"]), "conductor_id": str(row["conductor_id"]),
        "measurement_start_date": start.isoformat(), "measurement_end_date": end.isoformat(),
        "elapsed_days": elapsed, "tree_stage": stage,
        "interval_first_m": first, "interval_last_m": last,
    }


def eligible_rows(rows: Sequence[Mapping[str, Any]], target: str = TARGET) -> list[dict[str, Any]]:
    return _eligible(rows, target)[0]


def evidence_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    counts: dict[str, Any] = {
        "records": len(rows),
        "observation_types": dict(Counter(str(row.get("observation_type") or "unknown") for row in rows)),
        "aggregate_prior_records": sum(
            row.get("observation_type") in {"aggregate_growth", "experimental_growth"} for row in rows
        ),
        "eligible": {}, "rejected": {}, "independent_groups": {},
    }
    for target in TARGETS:
        selected, reasons = _eligible(rows, target)
        counts["eligible"][target] = len(selected)
        counts["rejected"][target] = dict(reasons)
        counts["independent_groups"][target] = len(_groups(selected))
    return counts


def compare_predictors(
    rows: Sequence[Mapping[str, Any]], *, target: str = TARGET, epochs: int = 300, patience: int = 25,
) -> dict[str, Any]:
    """Train two candidates on the same groups; choose on validation, report independent test error."""
    selected = eligible_rows(rows, target)
    groups = _groups(selected)
    report: dict[str, Any] = {
        "status": "insufficient_training_data", "target": target, "counts": evidence_counts(rows),
        "candidates": list(CANDIDATES), "selected_model": None, "metrics": None,
        "minimum_rows": MIN_ROWS, "minimum_independent_groups": MIN_GROUPS,
    }
    if len(selected) < MIN_ROWS or len(groups) < MIN_GROUPS:
        return report
    random.Random(0).shuffle(groups)
    held_out = max(2, len(groups) // 5)
    split_groups = (groups[2 * held_out:], groups[held_out:2 * held_out], groups[:held_out])
    splits = [[selected[index] for group in partition for index in group] for partition in split_groups]
    report["split_counts"] = dict(zip(("train", "validation", "test"), map(len, splits)))
    if len(splits[0]) < 30 or min(len(splits[1]), len(splits[2])) < 10:
        return report
    try:
        import numpy as np
        import torch
        from sklearn.ensemble import HistGradientBoostingRegressor
    except ImportError as exc:
        report.update(status="dependency_unavailable", missing_dependency=exc.name)
        return report
    if not 1 <= int(epochs) <= 2000 or not 1 <= int(patience) <= 200:
        raise ValueError("invalid_training_schedule")
    stages = sorted({_stage(row["tree_stage"]) for row in splits[0]})
    if any(_stage(row["tree_stage"]) not in stages for partition in splits[1:] for row in partition):
        report["status"] = "insufficient_stage_coverage"
        return report
    raw_train = [_interval_features(row) for row in splits[0]]
    preprocessing = _fit_preprocessing(raw_train, stages)
    matrices = [_matrix([_interval_features(row) for row in partition], preprocessing) for partition in splits]
    targets = [np.asarray([row["_rate"]["rate_m_per_day"] for row in partition], dtype=np.float32) for partition in splits]
    if float(targets[0].std()) <= 1e-12:
        report["status"] = "insufficient_target_variation"
        return report
    hgb = HistGradientBoostingRegressor(
        learning_rate=0.05, max_iter=200, max_leaf_nodes=15, min_samples_leaf=10,
        l2_regularization=1.0, early_stopping=False, random_state=0,
    )
    hgb.fit(matrices[0], targets[0])
    mlp, device, target_mean, target_scale = _train_mlp(matrices, targets, epochs, patience)
    with torch.inference_mode():
        mlp_outputs = [mlp(torch.as_tensor(matrix, device=device)).cpu().numpy() * target_scale + target_mean for matrix in matrices[1:]]
    predictions = {
        CANDIDATES[0]: [hgb.predict(matrix) for matrix in matrices[1:]],
        CANDIDATES[1]: mlp_outputs,
    }
    metrics = {
        name: {"validation": _metrics(values[0], targets[1]), "test": _metrics(values[1], targets[2])}
        for name, values in predictions.items()
    }
    winner = min(CANDIDATES, key=lambda name: (metrics[name]["validation"]["mae"], metrics[name]["validation"]["rmse"]))
    residual_interval = None
    if len(targets[2]) >= 20 and len(split_groups[2]) >= 4:
        residual_interval = np.quantile(targets[2] - predictions[winner][1], (0.1, 0.9)).tolist()
    checkpoint = {
        "format_version": 2, "accepted": False, "target": target, "model": winner,
        "feature_names": list(NUMERIC_FEATURES), "preprocessing": preprocessing,
        "metrics": metrics, "training_rows": len(selected), "independent_groups": len(groups),
        "selection_split": "validation", "test_groups_held_out": True,
        "residual_interval": residual_interval,
        "interval_method": "empirical_heldout_residual_80pct" if residual_interval else None,
        "source_ids": sorted({str(row["source_id"]) for row in selected}),
        "estimator": hgb if winner == CANDIDATES[0] else None,
        "model_state_dict": {key: value.detach().cpu() for key, value in mlp.state_dict().items()} if winner == CANDIDATES[1] else None,
        "target_mean": target_mean, "target_scale": target_scale,
    }
    report.update(status="evaluated_not_accepted", selected_model=winner, metrics=metrics, checkpoint=checkpoint, device=device.type)
    return report


def predict_rate(features: Mapping[str, Any]) -> dict[str, Any]:
    if not PREDICTOR_PATH.is_file():
        return _result("model_unavailable")
    try:
        checkpoint, model, device = _loaded_predictor(PREDICTOR_PATH.stat().st_mtime_ns)
        flattened = _flatten_features(features)
        _number(flattened.get("clearance_m"), "clearance_m", 0, 1000)
        matrix = _matrix([flattened], checkpoint["preprocessing"])
        if checkpoint["model"] == CANDIDATES[0]:
            rate = float(model.predict(matrix)[0])
        else:
            import torch
            with torch.inference_mode():
                rate = float(model(torch.as_tensor(matrix, device=device)).item()) * checkpoint["target_scale"] + checkpoint["target_mean"]
        if not math.isfinite(rate):
            raise ValueError("invalid_predicted_rate")
        result = _result("ok", target=checkpoint["target"], model=checkpoint["model"])
        result.update(rate_m_per_day=rate, source=checkpoint["source_ids"])
        interval = checkpoint.get("residual_interval")
        if interval is not None:
            result.update(rate_low_m_per_day=rate + interval[0], rate_high_m_per_day=rate + interval[1], interval_method=checkpoint["interval_method"])
        return result
    except (KeyError, TypeError, ValueError):
        return _result("insufficient_input")
    except (ImportError, OSError, RuntimeError, pickle.UnpicklingError, EOFError):
        return _result("error")


def promote_predictor(training_result: Mapping[str, Any], *, accepted: bool) -> Path:
    checkpoint = dict(training_result.get("checkpoint") or {})
    if accepted is not True or training_result.get("status") != "evaluated_not_accepted":
        raise ValueError("explicit_acceptance_of_evaluated_model_required")
    if checkpoint.get("accepted") is not False or checkpoint.get("target") not in TARGETS:
        raise ValueError("invalid_training_result")
    if checkpoint.get("training_rows", 0) < MIN_ROWS or checkpoint.get("independent_groups", 0) < MIN_GROUPS:
        raise ValueError("insufficient_verified_training_data")
    if checkpoint.get("selection_split") != "validation" or checkpoint.get("test_groups_held_out") is not True:
        raise ValueError("grouped_evaluation_required")
    checkpoint["accepted"] = True
    PREDICTOR_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=PREDICTOR_PATH.parent, suffix=".pkl", delete=False) as handle:
            temporary_path = Path(handle.name)
            pickle.dump(checkpoint, handle, protocol=pickle.HIGHEST_PROTOCOL)
        os.replace(temporary_path, PREDICTOR_PATH)
    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()
    _loaded_predictor.cache_clear()
    return PREDICTOR_PATH


@lru_cache(maxsize=1)
def _loaded_predictor(modified_ns: int) -> tuple[dict[str, Any], Any, Any]:
    # Trusted local training artifact only: never accept a pickle through an upload/API.
    with PREDICTOR_PATH.open("rb") as handle:
        checkpoint = pickle.load(handle)
    if not isinstance(checkpoint, dict) or checkpoint.get("accepted") is not True or checkpoint.get("format_version") != 2:
        raise ValueError("unaccepted_predictor")
    if checkpoint.get("target") not in TARGETS or checkpoint.get("feature_names") != list(NUMERIC_FEATURES):
        raise ValueError("unsupported_predictor_contract")
    if checkpoint.get("model") == CANDIDATES[0]:
        return checkpoint, checkpoint["estimator"], None
    if checkpoint.get("model") != CANDIDATES[1]:
        raise ValueError("unsupported_predictor_model")
    import torch
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = _network(checkpoint["preprocessing"]["input_size"]).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    return checkpoint, model, device


def _eligible(rows: Sequence[Mapping[str, Any]], target: str) -> tuple[list[dict[str, Any]], Counter]:
    selected, rejected = [], Counter()
    for row in rows:
        try:
            record = dict(row)
            record["_rate"] = observed_rate(row, target)
            _raw_features(_interval_features(record))
            selected.append(record)
        except (KeyError, TypeError, ValueError) as exc:
            rejected[str(exc)] += 1
    selected.sort(key=lambda row: (str(row["tree_id"]), row["_rate"]["measurement_start_date"]))
    accepted, last_by_tree = [], {}
    for row in selected:
        rate = row["_rate"]
        previous = last_by_tree.get(str(row["tree_id"]))
        if previous and rate["measurement_start_date"] < previous["measurement_end_date"]:
            rejected["duplicate_or_overlapping_tree_interval"] += 1
            continue
        if previous and rate["measurement_start_date"] == previous["measurement_end_date"] and not math.isclose(rate["interval_first_m"], previous["interval_last_m"], abs_tol=1e-6):
            rejected["inconsistent_repeated_measurement"] += 1
            continue
        last_by_tree[str(row["tree_id"])] = rate
        accepted.append(row)
    return accepted, rejected


def _groups(rows: Sequence[Mapping[str, Any]]) -> list[list[int]]:
    parents: dict[str, str] = {}
    def root(node: str) -> str:
        parents.setdefault(node, node)
        while parents[node] != node:
            parents[node] = parents[parents[node]]
            node = parents[node]
        return node
    for row in rows:
        parents[root("tree:" + str(row["tree_id"]))] = root("source:" + str(row["source_id"]))
    grouped: dict[str, list[int]] = {}
    for index, row in enumerate(rows):
        grouped.setdefault(root("tree:" + str(row["tree_id"])), []).append(index)
    return list(grouped.values())


def _interval_features(row: Mapping[str, Any]) -> dict[str, Any]:
    # End-of-interval geometry defines the target and must never enter its input features.
    features = {
        "tree_height_m": row.get("height_start_m"), "crown_width_m": row.get("crown_width_start_m"),
        "crown_area_m2": row.get("crown_area_start_m2"), "clearance_m": row.get("previous_clearance_m"),
        "month": _timestamp(row.get("measurement_start_date")).month,
        "temperature": row.get("temperature"), "humidity": row.get("humidity"), "rainfall": row.get("rainfall"),
        "tree_stage": row.get("tree_stage"), "previous_pruning_severity": row.get("previous_pruning_severity"),
        "time_since_last_pruning_days": row.get("time_since_last_pruning_days"),
    }
    for name in ("previous_height_m", "previous_crown_width_m", "previous_crown_area_m2", "previous_clearance_m", "elapsed_days"):
        features[name] = row.get("history_" + name)
    return features


def _raw_features(row: Mapping[str, Any]) -> list[float]:
    values = []
    for name, (low, high) in zip(NUMERIC_FEATURES, FEATURE_LIMITS):
        value = row.get(name)
        parsed = math.nan if value in (None, "") else _number(value, name, low, high)
        if name == "month" and math.isfinite(parsed) and not parsed.is_integer():
            raise ValueError("month_must_be_integer")
        values.append(parsed)
    if _stage(row.get("tree_stage")) not in STAGES:
        raise ValueError("compatible_tree_stage_required")
    if str(row.get("previous_pruning_severity") or "unknown").lower() not in SEVERITIES:
        raise ValueError("invalid_pruning_severity")
    return values


def _fit_preprocessing(rows: Sequence[Mapping[str, Any]], stages: Sequence[str]) -> dict[str, Any]:
    import numpy as np
    raw = np.asarray([_raw_features(row) for row in rows], dtype=np.float32)
    active = np.flatnonzero(np.isfinite(raw).any(axis=0))
    raw = raw[:, active]
    medians = np.nanmedian(raw, axis=0)
    imputed = np.where(np.isnan(raw), medians, raw)
    scale = imputed.std(axis=0)
    scale[scale < 1e-8] = 1.0
    return {
        "active": active.tolist(), "medians": medians.tolist(), "mean": imputed.mean(axis=0).tolist(),
        "scale": scale.tolist(), "stages": list(stages),
        "input_size": len(active) * 2 + len(stages) + len(SEVERITIES),
    }


def _matrix(rows: Sequence[Mapping[str, Any]], preprocessing: Mapping[str, Any]) -> Any:
    import numpy as np
    raw = np.asarray([_raw_features(row) for row in rows], dtype=np.float32)[:, preprocessing["active"]]
    missing = np.isnan(raw)
    numeric = (np.where(missing, preprocessing["medians"], raw) - preprocessing["mean"]) / preprocessing["scale"]
    categories = []
    for row in rows:
        stage = _stage(row.get("tree_stage"))
        if stage not in preprocessing["stages"]:
            raise ValueError("tree_stage_outside_training_scope")
        severity = str(row.get("previous_pruning_severity") or "unknown").lower()
        categories.append([stage == item for item in preprocessing["stages"]] + [severity == item for item in SEVERITIES])
    values = np.concatenate((numeric, missing, categories), axis=1).astype(np.float32)
    if not np.isfinite(values).all():
        raise ValueError("invalid_feature_normalization")
    return values


def _network(input_size: int) -> Any:
    from torch import nn
    return nn.Sequential(
        nn.Linear(input_size, 128), nn.GELU(), nn.Dropout(0.1),
        nn.Linear(128, 64), nn.GELU(), nn.Dropout(0.1),
        nn.Linear(64, 32), nn.GELU(), nn.Linear(32, 1), nn.Flatten(0),
    )


def _train_mlp(matrices: Sequence[Any], targets: Sequence[Any], epochs: int, patience: int) -> tuple[Any, Any, float, float]:
    import torch
    from torch.utils.data import DataLoader, TensorDataset
    torch.manual_seed(0)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    target_mean, target_scale = float(targets[0].mean()), float(targets[0].std())
    model = _network(matrices[0].shape[1]).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    loss_fn = torch.nn.SmoothL1Loss()
    loader = DataLoader(TensorDataset(torch.as_tensor(matrices[0]), torch.as_tensor((targets[0] - target_mean) / target_scale)), batch_size=min(64, len(targets[0])), shuffle=True)
    validation_x = torch.as_tensor(matrices[1], device=device)
    validation_y = torch.as_tensor((targets[1] - target_mean) / target_scale, device=device)
    best_error, best_state, stale = math.inf, None, 0
    for _ in range(int(epochs)):
        model.train()
        for x, y in loader:
            optimizer.zero_grad(set_to_none=True)
            loss = loss_fn(model(x.to(device)), y.to(device))
            loss.backward()
            optimizer.step()
        model.eval()
        with torch.inference_mode():
            error = float((model(validation_x) - validation_y).abs().mean().item())
        if error < best_error - 1e-6:
            best_error, best_state, stale = error, deepcopy(model.state_dict()), 0
        else:
            stale += 1
            if stale >= int(patience):
                break
    if best_state is None:
        raise RuntimeError("invalid_predictor_training_result")
    model.load_state_dict(best_state)
    model.eval()
    return model, device, target_mean, target_scale


def _metrics(predictions: Any, targets: Any) -> dict[str, Any]:
    import numpy as np
    errors = np.asarray(predictions) - targets
    if not np.isfinite(errors).all():
        raise ValueError("nonfinite_model_predictions")
    return {"mae": float(np.abs(errors).mean()), "rmse": float(np.sqrt(np.square(errors).mean())), "unit": "m/day", "samples": len(targets)}


def _flatten_features(row: Mapping[str, Any]) -> dict[str, Any]:
    flattened = dict(row)
    for name in ("geometry", "measurements", "weather", "history"):
        section = row.get(name)
        if isinstance(section, Mapping):
            for key, value in section.items():
                if flattened.get(key) in (None, ""):
                    flattened[key] = value
            if isinstance(section.get("measurements"), Mapping):
                for key, value in section["measurements"].items():
                    if flattened.get(key) in (None, ""):
                        flattened[key] = value
    if flattened.get("clearance_m") in (None, ""):
        flattened["clearance_m"] = flattened.get("current_clearance_m")
    return flattened


def _timestamp(value: Any) -> datetime:
    text = str(value or "")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid_observation_date") from exc
    if len(text) == 10:
        parsed = parsed.replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp_requires_timezone")
    return parsed.astimezone(timezone.utc)


def _true(value: Any) -> bool:
    return value is True or isinstance(value, str) and value.lower().strip() == "true"


def _stage(value: Any) -> str:
    stage = str(value or "").strip().lower()
    return {"adult": "mature", "dewasa": "mature"}.get(stage, stage)


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name}_must_be_numeric")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name}_must_be_numeric") from exc
    if not math.isfinite(parsed):
        raise ValueError(f"{name}_must_be_finite")
    return parsed


def _number(value: Any, name: str, low: float, high: float) -> float:
    parsed = _finite(value, name)
    if not low <= parsed <= high:
        raise ValueError(f"{name}_outside_supported_range")
    return parsed


def _result(status: str, *, target: str = TARGET, model: str | None = None) -> dict[str, Any]:
    return {"status": status, "target": target, "rate_m_per_day": None, "rate_low_m_per_day": None, "rate_high_m_per_day": None, "model": model, "source": None}
