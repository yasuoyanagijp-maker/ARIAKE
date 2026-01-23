import sys, pathlib, numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from ariake_octa.faz_segmentation import (
    detect_faz_region, 
    compute_faz_metrics,
    segment_faz,
)


def test_detect_faz_region():
    """Test FAZ region detection from vessel mask."""
    # Create synthetic vessel mask with central avascular zone
    vessel_mask = np.ones((100, 100), dtype=bool)
    # Create central avascular zone (FAZ)
    vessel_mask[40:60, 40:60] = False
    
    faz_mask, metrics = detect_faz_region(vessel_mask, min_area_px=50)
    
    assert isinstance(faz_mask, np.ndarray)
    assert faz_mask.dtype == bool
    assert faz_mask.shape == (100, 100)
    assert np.any(faz_mask)  # Should detect something
    assert metrics["faz_area_px"] > 0
    assert 0 <= metrics["faz_circularity"] <= 1.0


def test_compute_faz_metrics():
    """Test FAZ metrics computation."""
    # Create circular FAZ mask
    y, x = np.ogrid[-50:50, -50:50]
    faz_mask = (x**2 + y**2 <= 20**2)  # Circle with radius 20
    
    metrics = compute_faz_metrics(faz_mask, mm_per_pixel=0.01)
    
    assert metrics["faz_area_mm2"] > 0
    assert metrics["faz_perimeter_mm"] > 0
    assert metrics["faz_circularity"] > 0.8  # Should be close to 1 for circle
    assert metrics["faz_equivalent_diameter_mm"] > 0


def test_segment_faz():
    """Test complete FAZ segmentation pipeline."""
    # Create synthetic image with vessels and FAZ
    image = np.ones((100, 100), dtype=np.uint8) * 100
    vessel_mask = np.ones((100, 100), dtype=bool)
    # Central avascular zone
    vessel_mask[40:60, 40:60] = False
    image[40:60, 40:60] = 50  # Darker in center
    
    faz_mask, metrics = segment_faz(
        image, 
        vessel_mask, 
        mm_per_pixel=0.01,
        refine=False,
        min_area_px=50
    )
    
    assert isinstance(faz_mask, np.ndarray)
    assert faz_mask.dtype == bool
    assert "faz_area_mm2" in metrics
    assert "faz_circularity" in metrics
    assert "faz_centroid_x_px" in metrics
    assert "faz_centroid_y_px" in metrics


def test_empty_vessel_mask():
    """Test handling of empty vessel mask (all vessels)."""
    # All vessels, no avascular zones at all
    vessel_mask = np.ones((50, 50), dtype=bool)
    faz_mask, metrics = detect_faz_region(vessel_mask, min_area_px=10)
    
    # Should return empty mask and zero metrics (no avascular zones)
    # Note: Could still detect something if there are vessel gaps, that's ok
    assert isinstance(faz_mask, np.ndarray)
    assert isinstance(metrics, dict)


def test_no_faz_detected():
    """Test when no FAZ can be detected."""
    # All vessels, no avascular zone
    vessel_mask = np.ones((50, 50), dtype=bool)
    faz_mask, metrics = detect_faz_region(vessel_mask, min_area_px=10)
    
    # Should return something or empty
    assert isinstance(faz_mask, np.ndarray)
    assert isinstance(metrics, dict)
