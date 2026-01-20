import sys, pathlib, numpy as np, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from ariake_octa.pipeline import process_file
import tifffile as tiff

def test_pipeline_smoke(tmp_path):
    # create simple synthetic image
    img = (np.zeros((128,128), dtype=np.uint8))
    img[60:68, 10:118] = 255
    infile = str(tmp_path / "synthetic.tif")
    tiff.imwrite(infile, img)
    out = process_file(infile, str(tmp_path), params={"scale_mm":6.0, "image_width_px":128})
    assert isinstance(out, dict)
    assert "fused_mean" in out
