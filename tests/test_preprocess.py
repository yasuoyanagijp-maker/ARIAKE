import sys, pathlib, numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from ariake_octa.preprocess import preprocess_image

def test_preprocess_basic():
    img = np.zeros((200,200,3), dtype=np.uint8)
    # draw a bright background and darker vessel-like line
    img[:] = 200
    img[90:110, 50:150] = 50
    out = preprocess_image(img, clahe_clip=3.0, background_sigma=5.0)
    assert out.ndim == 2
    assert out.dtype == np.uint8
    assert out.shape == (200,200)
