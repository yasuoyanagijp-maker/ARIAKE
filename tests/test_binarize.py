import sys, pathlib, numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from ariake_octa.binarize import adaptive_binarize_phansalkar

def test_binarize_basic():
    img = (np.linspace(0,255,256).astype("uint8")).reshape(16,16)
    mask = adaptive_binarize_phansalkar(img, radius=3, k=0.1, R=128)
    assert mask.shape == img.shape
    assert mask.dtype == np.uint8
    assert mask.max() in (0,255)
