# Vegetation Growth Risk Engine

Phase 5 menyediakan skeleton deterministic rule-based untuk `pohon_sono` dan kelas vegetasi lain nanti.

## Input

Template CSV:

```text
data/templates/environmental_manual_input_template.csv
```

Kolom:

- `point_id`
- `vegetation_class`
- `current_tree_height_m`
- `current_clearance_m`
- `estimated_growth_cm_per_month`
- `rainfall_monthly_mm`
- `season_label`
- `soil_ph`
- `soil_type`
- `temperature_c`
- `humidity_percent`
- `pruning_history_date`
- `observation_date`
- `confidence_source`

## Output

- `risk_level`: `SAFE`, `WATCH`, `WARNING`, `CRITICAL`, atau `UNKNOWN`
- `predicted_months_to_threshold`
- `recommended_action_window`
- `missing_factors`
- `source_quality`
- `explanation`

## Batasan

Tidak ada scraping BPS/BMKG/KLHK di Phase 5. Nilai pH, curah hujan, suhu, dan musim tidak boleh diisi dari asumsi.
