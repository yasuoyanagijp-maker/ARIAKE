import sys, pathlib, numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from ariake_octa.filters import multi_scale_frangi, gabor_filter_max, fuse_filters

def test_filters_shapes():
    img = np.zeros((128,128), dtype=np.uint8)
    img[60:68, 20:108] = 255
    fr = multi_scale_frangi(img)
    gb = gabor_filter_max(img, thetas=(0,45,90))
    fused = fuse_filters([fr, gb], weights=[0.5,0.5])
    assert fr.shape == img.shape
    assert gb.shape == img.shape
    assert fused.shape == img.shape
    assert fr.dtype == np.uint8
