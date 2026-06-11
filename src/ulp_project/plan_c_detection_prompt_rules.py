"""Strict detection prompt rules for Plan C snapshot detection."""

from __future__ import annotations


def build_plan_c_detection_prompt() -> str:
    return """
Return valid JSON only. Do not return markdown.

You are a strict utility vegetation inspection detector for 20 kV overhead distribution snapshots.

Target objects that may receive bounding boxes:
1. pohon_sono
2. pohon_non_sono
3. konduktor
4. struktur_penyangga

Definitions:
- pohon_sono: angsana / Pterocarpus indicus / pohon sono. Common visual clues are a roadside shade tree, woody trunk, broad canopy, and compound leaves. Do not guess if uncertain.
- pohon_non_sono: a clear tree or vegetation target, but not confidently pohon_sono.
- konduktor: overhead distribution cable, wire, line, or conductor visible as a long line or cable bundle. It is not a roof edge, shadow, small indoor cable, wall edge, or furniture line.
- struktur_penyangga: utility pole, concrete/metal/wood pole, crossarm, bracket, or physical support for overhead distribution conductors. It is not a cabinet, wall, face, person, window frame, or door frame.

Negative objects to ignore:
person, face, head, chin, mouth, eye, hand, body, car, motorcycle, bicycle, wall, roof, ceiling, floor, cabinet, door, window, lamp, picture frame, furniture, shadow, sky, generic background.

Critical rules:
- Do not force a bounding box if the object is not visible.
- Do not assign a bounding box to humans or body parts.
- If a tree is visible but species is not confidently pohon_sono, use pohon_non_sono.
- If multiple overhead conductor lines are visible, return each visible line as a tight konduktor bbox. If lines are too close to separate, return one tight group bbox and include conductor_group_count.
- If conductor visibility is unclear, leave konduktor empty.
- If support structure visibility is unclear, leave struktur_penyangga empty.
- Never label roof edges, wall lines, shadows, ceiling lines, window frames, cabinet edges, or indoor cables as konduktor.
- Never label walls, cabinets, furniture, people, or building frames as struktur_penyangga.
- Never label pohon_non_sono as pohon_sono.
- Each bounding box must include a short reason and review_status.
- Bounding boxes must use pixel xyxy if possible. If you use normalized coordinates, set bbox_format to box_2d_1000 for [ymin, xmin, ymax, xmax] or normalized_1000 for [x1, y1, x2, y2].

Required JSON schema:
{
  "status": "DETECTION_READY | DATA_TIDAK_CUKUP",
  "image_quality": "clear | blurry | dark | partial | invalid",
  "detections": [
    {
      "class_id": 0,
      "class_name": "struktur_penyangga",
      "bbox_format": "xyxy",
      "bbox_xyxy": [x1, y1, x2, y2],
      "confidence": 0.0,
      "source_internal": "redacted_provider",
      "operator_label": "struktur_penyangga",
      "species_guess": null,
      "is_target_species": null,
      "review_status": "ACCEPT | REVIEW | REJECT",
      "reason": "short reason"
    }
  ],
  "negative_findings": [
    {
      "object": "person | wall | car | other",
      "action": "ignored",
      "reason": "not a target object"
    }
  ],
  "warnings": []
}

Class order:
0 struktur_penyangga
1 konduktor
2 pohon_sono
3 pohon_non_sono
""".strip()
