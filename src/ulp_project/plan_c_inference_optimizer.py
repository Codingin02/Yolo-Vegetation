"""Backend inference optimizer for Plan C System C YOLOv8 runtime.

The functions here only improve runtime inference. They do not train models,
change datasets, touch labels, or alter the operator UI.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import math
import os
import tempfile
import time
from typing import Any, Callable


TARGET_CLASSES = {"pohon_sono", "konduktor", "struktur_penyangga", "pohon_non_sono"}
TREE_CLASSES = {"pohon_sono", "pohon_non_sono"}


PredictCallback = Callable[[Path, float, float, int, int], list[dict[str, Any]]]


def run_optimized_yolo_inference(
    original_path: Path,
    *,
    predict_callback: PredictCallback,
    conf: float,
    iou: float,
    imgsz: int,
    max_det: int,
    model_policy: str,
) -> dict[str, Any]:
    started = time.perf_counter()
    image_quality = analyze_image_quality(original_path)
    device_profile = _device_profile()
    scales = _select_scales(imgsz, device_profile=device_profile)
    rejected: list[dict[str, Any]] = []
    raw_detections: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="plan_c_infer_") as tmp:
        variants = build_adaptive_preprocessing_variants(original_path, Path(tmp), image_quality)
        variants = _cap_variants_for_device(variants, device_profile=device_profile)
        for variant in variants:
            for scale in scales:
                variant_detections = _safe_predict(
                    predict_callback,
                    variant["path"],
                    conf,
                    iou,
                    scale,
                    max_det,
                    rejected,
                    variant_name=variant["name"],
                )
                raw_detections.extend(
                    _restore_variant_detection(
                        detection,
                        variant=variant,
                        image_width=int(image_quality.get("width") or 0),
                    )
                    for detection in variant_detections
                )

        recovery_used = False
        if not raw_detections and _image_quality_supports_sensitive_recovery(image_quality):
            recovery_used = True
            recovery_conf = max(0.08, min(conf * 0.55, 0.14))
            recovery_scales = _select_recovery_scales(scales, device_profile=device_profile)
            for variant in variants[:2]:
                for scale in recovery_scales:
                    variant_detections = _safe_predict(
                        predict_callback,
                        variant["path"],
                        recovery_conf,
                        max(0.35, iou - 0.1),
                        scale,
                        max_det,
                        rejected,
                        variant_name=f"{variant['name']}:recovery",
                    )
                    for detection in variant_detections:
                        restored = _restore_variant_detection(
                            detection,
                            variant=variant,
                            image_width=int(image_quality.get("width") or 0),
                        )
                        restored["review_status"] = "REVIEW_ONLY"
                        restored["source"] = f"{restored.get('source', 'yolo_v8')}_sensitive_recovery"
                        restored["recovery_mode"] = True
                        raw_detections.append(restored)

    merged = weighted_box_fusion(raw_detections, iou_threshold=0.55)
    refined = refine_detection_boxes(merged, original_path=original_path, image_quality=image_quality)
    filtered, sanity_rejected = apply_object_sanity_filter(
        refined,
        image_quality=image_quality,
        model_policy=model_policy,
        original_path=original_path,
    )
    rejected.extend(sanity_rejected)
    calibrated = calibrate_detection_confidences(filtered, image_quality=image_quality)
    elapsed_ms = int(round((time.perf_counter() - started) * 1000))

    return {
        "detections": calibrated,
        "raw_detection_count": len(raw_detections),
        "merged_detection_count": len(merged),
        "rejected_detections_redacted": rejected[:120],
        "image_quality": image_quality,
        "inference_optimization": {
            "status": "PLAN_C_OPTIMIZED_INFERENCE_READY",
            "pipeline": [
                "adaptive_preprocessing",
                "yolo_multiscale",
                "tta",
                "weighted_box_fusion",
                "sanity_filter",
                "confidence_calibration",
            ],
            "device_profile": device_profile,
            "scales": scales,
            "tta_enabled": True,
            "weighted_box_fusion": True,
            "sensitive_recovery_used": recovery_used,
            "elapsed_ms": elapsed_ms,
            "target_under_5s_rtx3050": True,
        },
    }


def analyze_image_quality(image_path: Path) -> dict[str, Any]:
    quality: dict[str, Any] = {
        "status": "IMAGE_QUALITY_UNKNOWN",
        "width": 0,
        "height": 0,
        "brightness_mean": None,
        "contrast_stddev": None,
        "edge_mean": None,
        "laplacian_variance": None,
        "dark_pixel_ratio": None,
        "bright_pixel_ratio": None,
        "reasons": [],
        "preprocessing_recommendations": [],
    }
    try:
        from PIL import ImageFilter, ImageStat

        rgb = _open_rgb_image(image_path)
        gray = rgb.convert("L")
        width, height = rgb.size
        stat = ImageStat.Stat(gray)
        brightness = float(stat.mean[0])
        contrast = float(stat.stddev[0])
        edge = gray.filter(ImageFilter.FIND_EDGES)
        edge_mean = float(ImageStat.Stat(edge).mean[0])
        histogram = gray.histogram()
        total = max(width * height, 1)
        dark_ratio = sum(histogram[:35]) / total
        bright_ratio = sum(histogram[225:]) / total
        lap_var = _laplacian_variance(gray)
        reasons: list[str] = []
        recommendations: list[str] = []
        if min(width, height) < 480:
            reasons.append("LOW_RESOLUTION")
            recommendations.append("resize_preserve_aspect")
        if brightness < 52:
            reasons.append("UNDER_EXPOSURE")
            recommendations.append("gamma_lift")
        if brightness > 205 or bright_ratio > 0.42:
            reasons.append("OVER_EXPOSURE")
            recommendations.append("gamma_reduce")
        if contrast < 28:
            reasons.append("LOW_CONTRAST")
            recommendations.append("adaptive_histogram")
        if edge_mean < 5.0 or lap_var < 24:
            reasons.append("BLUR_OR_LOW_EDGE")
            recommendations.append("sharpen")
        if dark_ratio > 0.55:
            reasons.append("HEAVY_SHADOW")
            recommendations.append("shadow_lift")
        if brightness > 125 and contrast < 28 and edge_mean < 8:
            reasons.append("FOG_OR_HAZE_POSSIBLE")
            recommendations.append("contrast_normalization")
        if contrast < 22 and edge_mean < 6:
            reasons.append("RAIN_OR_WET_LENS_POSSIBLE")
            recommendations.append("denoise_then_sharpen")
        top = gray.crop((0, 0, width, max(1, height // 3)))
        center = gray.crop((0, height // 3, width, max(height // 3 + 1, 2 * height // 3)))
        if ImageStat.Stat(top).mean[0] - ImageStat.Stat(center).mean[0] > 52:
            reasons.append("BACKLIGHT_POSSIBLE")
            recommendations.append("shadow_lift")
        quality.update(
            {
                "status": "LOW_IMAGE_QUALITY" if reasons else "IMAGE_QUALITY_ACCEPTABLE",
                "width": width,
                "height": height,
                "brightness_mean": round(brightness, 3),
                "contrast_stddev": round(contrast, 3),
                "edge_mean": round(edge_mean, 3),
                "laplacian_variance": round(lap_var, 3),
                "dark_pixel_ratio": round(dark_ratio, 4),
                "bright_pixel_ratio": round(bright_ratio, 4),
                "reasons": sorted(set(reasons)),
                "preprocessing_recommendations": sorted(set(recommendations)),
            }
        )
    except Exception as exc:
        quality["status"] = "IMAGE_QUALITY_ANALYSIS_FAILED"
        quality["reasons"] = [f"{type(exc).__name__}: {exc}"]
    return quality


def build_adaptive_preprocessing_variants(original_path: Path, temp_dir: Path, image_quality: dict[str, Any]) -> list[dict[str, Any]]:
    variants: list[dict[str, Any]] = [
        {"name": "original", "path": original_path, "flip_horizontal": False, "weight": 1.0}
    ]
    try:
        from PIL import Image, ImageEnhance, ImageFilter, ImageOps

        base = _open_rgb_image(original_path)
        reasons = set(image_quality.get("reasons") or [])
        if reasons & {"LOW_CONTRAST", "FOG_OR_HAZE_POSSIBLE", "BACKLIGHT_POSSIBLE"}:
            variants.append(_save_variant(ImageOps.autocontrast(base, cutoff=1), temp_dir, "adaptive_histogram", weight=0.96))
        if reasons & {"UNDER_EXPOSURE", "HEAVY_SHADOW", "BACKLIGHT_POSSIBLE"}:
            lifted = _gamma_correct(base, gamma=0.72)
            lifted = ImageEnhance.Contrast(lifted).enhance(1.12)
            variants.append(_save_variant(lifted, temp_dir, "gamma_lift", weight=0.92))
        if reasons & {"OVER_EXPOSURE"}:
            reduced = _gamma_correct(base, gamma=1.22)
            variants.append(_save_variant(reduced, temp_dir, "gamma_reduce", weight=0.9))
        if reasons & {"BLUR_OR_LOW_EDGE", "RAIN_OR_WET_LENS_POSSIBLE"}:
            sharpened = base.filter(ImageFilter.UnsharpMask(radius=1.3, percent=135, threshold=3))
            variants.append(_save_variant(sharpened, temp_dir, "sharpened", weight=0.88))

        wire = _wire_enhanced_variant(base)
        variants.append(_save_variant(wire, temp_dir, "wire_edge_enhanced", weight=0.82))

        flipped_path = temp_dir / "tta_flip_horizontal.jpg"
        base.transpose(Image.Transpose.FLIP_LEFT_RIGHT).save(flipped_path, quality=92)
        variants.append({"name": "tta_flip_horizontal", "path": flipped_path, "flip_horizontal": True, "weight": 0.78})
    except Exception:
        return variants
    return variants


def weighted_box_fusion(detections: list[dict[str, Any]], *, iou_threshold: float = 0.55) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for detection in detections:
        class_name = str(detection.get("class_name") or "")
        if class_name not in TARGET_CLASSES or not _valid_bbox(detection.get("bbox_xyxy")):
            continue
        grouped.setdefault(class_name, []).append(detection)

    fused: list[dict[str, Any]] = []
    for class_name, class_dets in grouped.items():
        remaining = sorted(class_dets, key=lambda item: float(item.get("confidence") or 0.0), reverse=True)
        while remaining:
            seed = remaining.pop(0)
            cluster = [seed]
            rest: list[dict[str, Any]] = []
            for candidate in remaining:
                threshold = 0.36 if class_name == "konduktor" else iou_threshold
                if _bbox_iou(seed["bbox_xyxy"], candidate["bbox_xyxy"]) >= threshold:
                    cluster.append(candidate)
                else:
                    rest.append(candidate)
            remaining = rest
            fused.append(_fuse_cluster(cluster, class_name=class_name))
    return sorted(fused, key=lambda item: float(item.get("confidence") or 0.0), reverse=True)


def refine_detection_boxes(detections: list[dict[str, Any]], *, original_path: Path, image_quality: dict[str, Any]) -> list[dict[str, Any]]:
    refined: list[dict[str, Any]] = []
    for detection in detections:
        item = dict(detection)
        bbox = item.get("bbox_xyxy")
        if not _valid_bbox(bbox):
            refined.append(item)
            continue
        class_name = str(item.get("class_name") or "")
        if class_name in TREE_CLASSES:
            refined_bbox = _refine_tree_bbox(original_path, bbox)
            if refined_bbox:
                item["bbox_xyxy"] = refined_bbox
                item["bbox_refinement"] = "tree_crown_edge_refinement"
        elif class_name == "konduktor":
            refined_bbox = _refine_conductor_bbox(original_path, bbox)
            if refined_bbox:
                item["bbox_xyxy"] = refined_bbox
                item["bbox_refinement"] = "wire_edge_refinement"
        refined.append(item)
    return refined


def apply_object_sanity_filter(
    detections: list[dict[str, Any]],
    *,
    image_quality: dict[str, Any],
    model_policy: str,
    original_path: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    width = int(image_quality.get("width") or 0)
    height = int(image_quality.get("height") or 0)
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for detection in detections:
        item = dict(detection)
        class_name = str(item.get("class_name") or "")
        bbox = item.get("bbox_xyxy")
        reason = _sanity_reject_reason(bbox, class_name=class_name, width=width, height=height)
        if reason:
            rejected.append(_redacted_rejection(item, reason))
            continue
        texture_score = _crop_texture_score(original_path, bbox)
        if texture_score is not None and texture_score < 4.5 and class_name != "konduktor":
            rejected.append(_redacted_rejection(item, "BBOX_LOW_TEXTURE_EMPTY_AREA"))
            continue
        quality_flags = _bbox_quality_flags(bbox, class_name=class_name, width=width, height=height)
        if texture_score is not None and texture_score < 18.0:
            quality_flags.append("BBOX_LOW_TEXTURE_REVIEW")
        if texture_score is not None:
            item["bbox_texture_score"] = round(texture_score, 3)
        if quality_flags:
            item["review_status"] = "REVIEW"
            item["sanity_flags"] = quality_flags
        accepted.append(item)

    accepted = _remove_duplicate_boxes(accepted)
    if model_policy != "system_c_detector":
        accepted = [item for item in accepted if item.get("class_name") == "pohon_sono"]
    return accepted, rejected


def calibrate_detection_confidences(
    detections: list[dict[str, Any]],
    *,
    image_quality: dict[str, Any],
    ai_raw: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    calibrated: list[dict[str, Any]] = []
    ai_summary = ai_raw or {}
    for detection in detections:
        item = dict(detection)
        raw_conf = _clamp(float(item.get("confidence") or 0.0), 0.0, 1.0)
        vote_count = int(item.get("fusion_vote_count") or 1)
        vote_bonus = min(0.14, max(0.0, vote_count - 1) * 0.035)
        quality_penalty = _image_quality_penalty(image_quality)
        bbox_penalty = 0.0
        for flag in item.get("sanity_flags") or []:
            bbox_penalty += 0.035
        ai_adjust = _ai_adjustment_for_detection(item, ai_summary)
        final_conf = _clamp(raw_conf + vote_bonus + ai_adjust - quality_penalty - bbox_penalty, 0.01, 0.99)
        item["raw_confidence"] = round(raw_conf, 4)
        item["confidence"] = round(final_conf, 4)
        item["confidence_calibrated"] = round(final_conf, 4)
        item["confidence_components"] = {
            "yolo_score": round(raw_conf, 4),
            "fusion_vote_bonus": round(vote_bonus, 4),
            "ai_adjustment": round(ai_adjust, 4),
            "image_quality_penalty": round(quality_penalty, 4),
            "bbox_quality_penalty": round(bbox_penalty, 4),
        }
        if final_conf < 0.35 or item.get("recovery_mode"):
            item["review_status"] = "REVIEW_ONLY"
        elif item.get("review_status") not in {"REVIEW_ONLY", "REVIEW"}:
            item["review_status"] = "REVIEW"
        label_conf = f"{final_conf:.2f}"
        item["label"] = f"YOLOv8 {item.get('class_name')} {label_conf}"
        calibrated.append(item)
    return calibrated


def summarize_detection_quality(detections: list[dict[str, Any]], image_quality: dict[str, Any]) -> dict[str, Any]:
    class_counts = Counter(str(item.get("class_name") or "unknown") for item in detections)
    return {
        "image_quality_status": image_quality.get("status"),
        "image_quality_reasons": image_quality.get("reasons", []),
        "detection_count": len(detections),
        "class_counts": dict(class_counts),
        "review_only_count": sum(1 for item in detections if item.get("review_status") == "REVIEW_ONLY"),
        "calibrated_confidence_mean": _mean([item.get("confidence") for item in detections]),
    }


def _safe_predict(
    predict_callback: PredictCallback,
    path: Path,
    conf: float,
    iou: float,
    imgsz: int,
    max_det: int,
    rejected: list[dict[str, Any]],
    *,
    variant_name: str,
) -> list[dict[str, Any]]:
    try:
        return predict_callback(path, conf, iou, imgsz, max_det)
    except Exception as exc:
        rejected.append({"variant": variant_name, "reason": f"PREDICT_FAILED:{type(exc).__name__}: {exc}"})
        return []


def _restore_variant_detection(detection: dict[str, Any], *, variant: dict[str, Any], image_width: int) -> dict[str, Any]:
    item = dict(detection)
    bbox = item.get("bbox_xyxy")
    if variant.get("flip_horizontal") and _valid_bbox(bbox):
        x1, y1, x2, y2 = [float(value) for value in bbox]
        item["bbox_xyxy"] = [round(image_width - x2, 2), round(y1, 2), round(image_width - x1, 2), round(y2, 2)]
    item["tta_variant"] = variant.get("name")
    item["variant_weight"] = variant.get("weight", 1.0)
    return item


def _fuse_cluster(cluster: list[dict[str, Any]], *, class_name: str) -> dict[str, Any]:
    weighted_sum = [0.0, 0.0, 0.0, 0.0]
    total_weight = 0.0
    confidences: list[float] = []
    variants: set[str] = set()
    for item in cluster:
        conf = _clamp(float(item.get("confidence") or 0.0), 0.01, 1.0)
        weight = conf * float(item.get("variant_weight") or 1.0)
        bbox = [float(value) for value in item["bbox_xyxy"]]
        for idx in range(4):
            weighted_sum[idx] += bbox[idx] * weight
        total_weight += weight
        confidences.append(conf)
        variants.add(str(item.get("tta_variant") or "original"))
    fused_bbox = [round(value / max(total_weight, 1e-6), 2) for value in weighted_sum]
    best = max(cluster, key=lambda item: float(item.get("confidence") or 0.0))
    confidence = min(0.99, max(confidences) + min(0.12, 0.025 * (len(cluster) - 1)))
    output = dict(best)
    output.update(
        {
            "class_name": class_name,
            "bbox_xyxy": fused_bbox,
            "confidence": round(confidence, 4),
            "fusion_vote_count": len(cluster),
            "fusion_variants": sorted(variants),
            "source": f"{best.get('source', 'yolo_v8')}_wbf",
        }
    )
    return output


def _sanity_reject_reason(bbox: Any, *, class_name: str, width: int, height: int) -> str:
    if not _valid_bbox(bbox):
        return "BBOX_INVALID"
    if width <= 0 or height <= 0:
        return "IMAGE_SIZE_INVALID"
    x1, y1, x2, y2 = [float(value) for value in bbox]
    if x1 < -2 or y1 < -2 or x2 > width + 2 or y2 > height + 2:
        return "BBOX_OUT_OF_FRAME"
    box_w = x2 - x1
    box_h = y2 - y1
    area_ratio = (box_w * box_h) / max(width * height, 1)
    if area_ratio < (0.00018 if class_name == "konduktor" else 0.0008):
        return "BBOX_TOO_SMALL"
    if area_ratio > (0.88 if class_name in TREE_CLASSES else 0.72):
        return "BBOX_TOO_LARGE"
    aspect = box_w / max(box_h, 1.0)
    if class_name == "konduktor" and aspect < 2.2 and box_h > height * 0.045:
        return "CONDUCTOR_SHAPE_NOT_LINE_LIKE"
    if class_name == "struktur_penyangga" and aspect > 1.15 and area_ratio > 0.18:
        return "STRUCTURE_SHAPE_NOT_SUPPORT_LIKE"
    if class_name in TREE_CLASSES and aspect > 7.0 and area_ratio < 0.08:
        return "TREE_SHAPE_WIRE_LIKE"
    if class_name in TREE_CLASSES and aspect < 0.10 and area_ratio < 0.16:
        return "TREE_SHAPE_POLE_LIKE"
    return ""


def _bbox_quality_flags(bbox: Any, *, class_name: str, width: int, height: int) -> list[str]:
    if not _valid_bbox(bbox) or width <= 0 or height <= 0:
        return ["BBOX_REVIEW_REQUIRED"]
    x1, y1, x2, y2 = [float(value) for value in bbox]
    box_w = x2 - x1
    box_h = y2 - y1
    area_ratio = (box_w * box_h) / max(width * height, 1)
    flags: list[str] = []
    margin = min(width, height) * 0.012
    if x1 <= margin or y1 <= margin or x2 >= width - margin or y2 >= height - margin:
        flags.append("BBOX_NEAR_FRAME_EDGE")
    if class_name in TREE_CLASSES and area_ratio > 0.70:
        flags.append("TREE_BBOX_LARGE_REVIEW")
    if class_name == "konduktor" and box_h / max(height, 1) > 0.08:
        flags.append("CONDUCTOR_BBOX_THICK_REVIEW")
    return flags


def _crop_texture_score(original_path: Path, bbox: Any) -> float | None:
    if not _valid_bbox(bbox):
        return None
    try:
        from PIL import ImageFilter, ImageStat

        gray = _open_rgb_image(original_path).convert("L")
        width, height = gray.size
        x1, y1, x2, y2 = [float(value) for value in bbox]
        crop_box = (
            max(0, int(math.floor(x1))),
            max(0, int(math.floor(y1))),
            min(width, int(math.ceil(x2))),
            min(height, int(math.ceil(y2))),
        )
        if crop_box[2] <= crop_box[0] or crop_box[3] <= crop_box[1]:
            return None
        crop = gray.crop(crop_box)
        contrast = float(ImageStat.Stat(crop).stddev[0])
        edge = crop.filter(ImageFilter.FIND_EDGES)
        edge_mean = float(ImageStat.Stat(edge).mean[0])
        return (contrast * 0.65) + (edge_mean * 0.35)
    except Exception:
        return None


def _remove_duplicate_boxes(detections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for detection in sorted(detections, key=lambda item: float(item.get("confidence") or 0.0), reverse=True):
        duplicate = False
        for kept in output:
            if kept.get("class_name") == detection.get("class_name") and _bbox_iou(kept.get("bbox_xyxy"), detection.get("bbox_xyxy")) > 0.82:
                duplicate = True
                break
        if not duplicate:
            output.append(detection)
    return output


def _image_quality_supports_sensitive_recovery(image_quality: dict[str, Any]) -> bool:
    reasons = set(image_quality.get("reasons") or [])
    severe = {"LOW_RESOLUTION", "OVER_EXPOSURE"}
    if severe & reasons:
        return False
    return image_quality.get("status") in {"IMAGE_QUALITY_ACCEPTABLE", "LOW_IMAGE_QUALITY"}


def _select_scales(base_imgsz: int, *, device_profile: str) -> list[int]:
    env_value = os.getenv("PLAN_C_INFERENCE_SCALES", "").strip()
    if env_value:
        values = []
        for item in env_value.split(","):
            try:
                values.append(int(item.strip()))
            except ValueError:
                continue
        if values:
            return sorted(set(values))
    if device_profile == "cuda":
        return sorted(set([base_imgsz, 768, 896, 1024]))
    return sorted(set([base_imgsz, 768]))


def _select_recovery_scales(scales: list[int], *, device_profile: str) -> list[int]:
    if device_profile == "cuda":
        return sorted(set([min(max(scales), 1024), 896]))
    return [max(scales)]


def _cap_variants_for_device(variants: list[dict[str, Any]], *, device_profile: str) -> list[dict[str, Any]]:
    max_variants = 5 if device_profile == "cuda" else 3
    try:
        max_variants = int(os.getenv("PLAN_C_INFERENCE_MAX_VARIANTS", max_variants))
    except ValueError:
        pass
    return variants[: max(1, max_variants)]


def _device_profile() -> str:
    forced = os.getenv("PLAN_C_INFERENCE_DEVICE_PROFILE", "").strip().lower()
    if forced in {"cuda", "cpu"}:
        return forced
    try:
        import torch  # type: ignore

        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"


def _save_variant(image: Any, temp_dir: Path, name: str, *, weight: float) -> dict[str, Any]:
    path = temp_dir / f"{name}.jpg"
    image.save(path, quality=92)
    return {"name": name, "path": path, "flip_horizontal": False, "weight": weight}


def _gamma_correct(image: Any, *, gamma: float) -> Any:
    inv = 1.0 / max(gamma, 1e-6)
    table = [min(255, max(0, int(((i / 255.0) ** inv) * 255.0))) for i in range(256)]
    return image.point(table * 3)


def _wire_enhanced_variant(image: Any) -> Any:
    try:
        from PIL import ImageChops, ImageEnhance, ImageFilter, ImageOps

        gray_edges = ImageOps.grayscale(image).filter(ImageFilter.FIND_EDGES).convert("RGB")
        blended = ImageChops.screen(image, gray_edges)
        return ImageEnhance.Contrast(blended).enhance(1.12)
    except Exception:
        return image


def _laplacian_variance(gray_image: Any) -> float:
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore

        arr = np.array(gray_image)
        return float(cv2.Laplacian(arr, cv2.CV_64F).var())
    except Exception:
        try:
            from PIL import ImageFilter, ImageStat

            edge = gray_image.filter(ImageFilter.FIND_EDGES)
            return float(ImageStat.Stat(edge).var[0])
        except Exception:
            return 0.0


def _refine_tree_bbox(original_path: Path, bbox: Any) -> list[float] | None:
    return _refine_bbox_by_edges(original_path, bbox, shrink_limit=0.22, min_area_keep=0.55)


def _refine_conductor_bbox(original_path: Path, bbox: Any) -> list[float] | None:
    refined = _refine_bbox_by_edges(original_path, bbox, shrink_limit=0.35, min_area_keep=0.35)
    if not refined:
        return None
    x1, y1, x2, y2 = refined
    if (y2 - y1) < 3:
        center = (y1 + y2) / 2.0
        y1 = center - 1.5
        y2 = center + 1.5
    return [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)]


def _refine_bbox_by_edges(original_path: Path, bbox: Any, *, shrink_limit: float, min_area_keep: float) -> list[float] | None:
    if not _valid_bbox(bbox):
        return None
    try:
        from PIL import ImageFilter

        gray = _open_rgb_image(original_path).convert("L")
        width, height = gray.size
        x1, y1, x2, y2 = [float(value) for value in bbox]
        crop_box = (
            max(0, int(math.floor(x1))),
            max(0, int(math.floor(y1))),
            min(width, int(math.ceil(x2))),
            min(height, int(math.ceil(y2))),
        )
        if crop_box[2] <= crop_box[0] or crop_box[3] <= crop_box[1]:
            return None
        crop = gray.crop(crop_box).filter(ImageFilter.FIND_EDGES)
        hist = crop.histogram()
        if not hist:
            return None
        threshold = max(12, int(sum(value * idx for idx, value in enumerate(hist)) / max(sum(hist), 1) * 1.15))
        points: list[tuple[int, int]] = []
        pix = crop.load()
        for yy in range(crop.height):
            for xx in range(crop.width):
                if pix[xx, yy] >= threshold:
                    points.append((xx, yy))
        if len(points) < 16:
            return None
        min_x = min(point[0] for point in points)
        min_y = min(point[1] for point in points)
        max_x = max(point[0] for point in points)
        max_y = max(point[1] for point in points)
        pad_x = max(4, int(crop.width * 0.06))
        pad_y = max(4, int(crop.height * 0.06))
        nx1 = crop_box[0] + max(0, min_x - pad_x)
        ny1 = crop_box[1] + max(0, min_y - pad_y)
        nx2 = crop_box[0] + min(crop.width, max_x + pad_x)
        ny2 = crop_box[1] + min(crop.height, max_y + pad_y)
        old_area = max((x2 - x1) * (y2 - y1), 1.0)
        new_area = max((nx2 - nx1) * (ny2 - ny1), 1.0)
        if new_area < old_area * min_area_keep:
            return None
        max_shrink_x = (x2 - x1) * shrink_limit
        max_shrink_y = (y2 - y1) * shrink_limit
        if abs(nx1 - x1) > max_shrink_x or abs(x2 - nx2) > max_shrink_x:
            return None
        if abs(ny1 - y1) > max_shrink_y or abs(y2 - ny2) > max_shrink_y:
            return None
        return [round(float(nx1), 2), round(float(ny1), 2), round(float(nx2), 2), round(float(ny2), 2)]
    except Exception:
        return None


def _bbox_iou(a: Any, b: Any) -> float:
    if not _valid_bbox(a) or not _valid_bbox(b):
        return 0.0
    ax1, ay1, ax2, ay2 = [float(value) for value in a]
    bx1, by1, bx2, by2 = [float(value) for value in b]
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    denom = area_a + area_b - inter
    return inter / denom if denom > 0 else 0.0


def _valid_bbox(value: Any) -> bool:
    if not isinstance(value, list) or len(value) != 4:
        return False
    try:
        x1, y1, x2, y2 = [float(item) for item in value]
    except (TypeError, ValueError):
        return False
    return x2 > x1 and y2 > y1


def _redacted_rejection(item: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "class_name": item.get("class_name"),
        "confidence": item.get("confidence"),
        "bbox_xyxy": item.get("bbox_xyxy"),
        "source": item.get("source"),
        "reason": reason,
    }


def _ai_adjustment_for_detection(detection: dict[str, Any], ai_raw: dict[str, Any]) -> float:
    if not ai_raw:
        return 0.0
    class_name = str(detection.get("class_name") or "")
    summary = ai_raw.get("summary") if isinstance(ai_raw.get("summary"), dict) else {}
    tree_visible = summary.get("tree_visible_consensus")
    ok_count = int(summary.get("ok_count") or 0)
    provider_adjust = float(summary.get("confidence_adjustment_mean") or 0.0)
    false_positive = float(summary.get("false_positive_likelihood_mean") or 0.0)
    false_negative = float(summary.get("false_negative_likelihood_mean") or 0.0)
    adjustment = max(-0.12, min(0.12, provider_adjust))
    if class_name in TREE_CLASSES and tree_visible is True:
        adjustment += min(0.08, 0.025 * ok_count)
    if class_name in TREE_CLASSES and tree_visible is False:
        adjustment -= 0.12
    if false_positive >= 0.65:
        adjustment -= 0.08
    if class_name in TREE_CLASSES and false_negative >= 0.65 and detection.get("recovery_mode"):
        adjustment += 0.05
    return max(-0.18, min(0.16, adjustment))


def _image_quality_penalty(image_quality: dict[str, Any]) -> float:
    reasons = set(image_quality.get("reasons") or [])
    penalty = 0.0
    for reason in reasons:
        if reason in {"BLUR_OR_LOW_EDGE", "LOW_CONTRAST", "UNDER_EXPOSURE"}:
            penalty += 0.035
        elif reason in {"LOW_RESOLUTION", "OVER_EXPOSURE"}:
            penalty += 0.05
        elif reason in {"FOG_OR_HAZE_POSSIBLE", "RAIN_OR_WET_LENS_POSSIBLE", "BACKLIGHT_POSSIBLE", "HEAVY_SHADOW"}:
            penalty += 0.025
    return min(0.18, penalty)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _mean(values: list[Any]) -> float | None:
    cleaned = []
    for value in values:
        try:
            cleaned.append(float(value))
        except (TypeError, ValueError):
            pass
    if not cleaned:
        return None
    return round(sum(cleaned) / len(cleaned), 4)


def _open_rgb_image(path: Path) -> Any:
    try:
        from PIL import Image, ImageFile, ImageOps

        ImageFile.LOAD_TRUNCATED_IMAGES = True
        with Image.open(path) as image:
            return ImageOps.exif_transpose(image).convert("RGB").copy()
    except Exception:
        try:
            import cv2  # type: ignore
            from PIL import Image

            arr = cv2.imread(str(path), cv2.IMREAD_COLOR)
            if arr is None:
                raise ValueError("OpenCV could not read image")
            rgb = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
            return Image.fromarray(rgb)
        except Exception:
            raise
