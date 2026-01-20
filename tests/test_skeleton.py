import sys, pathlib, numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from ariake_octa.skeleton import compute_skeleton_metrics
from skimage.draw import disk

def test_skeleton_metrics():
    img = np.zeros((200,200), dtype=bool)
    rr, cc = disk((100,100), 40)
    img[rr,cc] = True
    res = compute_skeleton_metrics((img>0).astype("uint8"), pixel_size_um=5.0)
    assert "skeleton_mean_um" in res
    assert res["skeleton_mean_um"] >= 0
