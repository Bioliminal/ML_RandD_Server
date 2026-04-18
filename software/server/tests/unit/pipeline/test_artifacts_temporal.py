from bioliminal.pipeline.artifacts import MovementTemporalSummary, RepComparison


def test_rep_comparison_serializes_all_fields():
    rc = RepComparison(
        rep_index=0,
        angle="left_knee_flexion",
        ncc_score=0.97,
        dtw_distance=1.4,
        rom_user_deg=88.0,
        rom_reference_deg=90.0,
        rom_deviation_pct=-2.22,
        status="clean",
    )
    data = rc.model_dump(mode="json")
    assert data["rep_index"] == 0
    assert data["angle"] == "left_knee_flexion"
    assert data["ncc_score"] == 0.97
    assert data["status"] == "clean"


def test_movement_temporal_summary_holds_comparisons():
    comparisons = [
        RepComparison(
            rep_index=i,
            angle="left_knee_flexion",
            ncc_score=0.95 - 0.02 * i,
            dtw_distance=1.0 + i,
            rom_user_deg=90.0 - 3.0 * i,
            rom_reference_deg=90.0,
            rom_deviation_pct=-3.33 * i,
            status="concern" if i > 0 else "clean",
        )
        for i in range(3)
    ]
    summary = MovementTemporalSummary(
        primary_angle="left_knee_flexion",
        rep_comparisons=comparisons,
        mean_ncc=0.93,
        ncc_slope_per_rep=-0.02,
        mean_rom_deviation_pct=-3.33,
        form_drift_detected=False,
    )
    assert len(summary.rep_comparisons) == 3
    assert summary.primary_angle == "left_knee_flexion"
    assert summary.ncc_slope_per_rep == -0.02
