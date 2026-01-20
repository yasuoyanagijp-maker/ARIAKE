import numpy as np
import tifffile as tiff
from pathlib import Path

from .preprocess import preprocess_image
from .filters import multi_scale_frangi, gabor_filter_max, fuse_filters
from .binarize import adaptive_binarize_phansalkar
from .skeleton import compute_skeleton_metrics, compute_graph_metrics
from .fractal import box_counting_fd
from .flow_deficit import flow_deficit_analysis
from .spatial import analyze_spatial_distribution
from .classify import classify_mnv
from .roi import refine_roi_by_intensity, polygon_to_mask_coords
from .arteriolarization import analyze_arteriolarization
from .utils import mm_per_pixel_from_scale

def default_roi_center_circle(shape):
    h,w = shape
    cx, cy = w//2, h//2
    r = min(w,h)//4
    t = np.linspace(0, 2*np.pi, 128)
    xs = (cx + r*np.cos(t)).tolist()
    ys = (cy + r*np.sin(t)).tolist()
    return list(zip(xs, ys))

def process_file(path, output_dir, params):
    out = {}
    img = tiff.imread(str(path))
    if img.ndim == 3 and img.shape[2] == 3:
        img_gray = img[:,:,1]
    else:
        img_gray = img
    pre = preprocess_image(img_gray, clahe_clip=3.0, background_sigma=params.get("background_sigma",5.0))
    out["preprocessed_shape"] = pre.shape
    fr = multi_scale_frangi(pre)
    gb = gabor_filter_max(pre)
    fused = fuse_filters([fr, gb], weights=[0.4,0.4])
    out["fused_mean"] = float(np.mean(fused))
    bin_mask = adaptive_binarize_phansalkar(fused, radius=params.get("phansalkar_radius_px",15),
                                           k=params.get("phansalkar_k",0.1), R=128)
    image_width_px = params.get("image_width_px", pre.shape[1])
    scale_mm = params.get("scale_mm", params.get("scale_mm", 1.0))
    mm_per_pixel = mm_per_pixel_from_scale(image_width_px, scale_mm)
    pixel_size_um = mm_per_pixel * 1000.0 if mm_per_pixel>0 else params.get("pixel_size_um",1.0)
    sk_metrics = compute_skeleton_metrics(bin_mask, pixel_size_um=pixel_size_um)
    out.update(sk_metrics)
    graph_metrics = compute_graph_metrics(bin_mask, pixel_size_um=pixel_size_um)
    # normalize graph keys to macro-like names if available
    out["n_branches"] = graph_metrics.get("n_branches", 0)
    out["n_junctions"] = graph_metrics.get("n_junctions", 0)
    out["n_endpoints"] = graph_metrics.get("n_endpoints", 0)
    out["total_branch_length_mm"] = graph_metrics.get("total_branch_length_mm", 0.0)
    out["tortuosity"] = graph_metrics.get("tortuosity", 0.0)
    fd_val = box_counting_fd((bin_mask>0).astype("uint8"))
    out["fractal_fd"] = float(fd_val)
    # compute distance map
    from scipy.ndimage import distance_transform_edt
    distance_map = distance_transform_edt((bin_mask>0).astype("uint8"))
    # ROI handling
    roi = params.get("roi_coords", None)
    if roi is None:
        roi = default_roi_center_circle(pre.shape)
    # optional refinement using intensity
    try:
        refined_roi = refine_roi_by_intensity(pre, roi, iterations=3)
    except Exception:
        refined_roi = roi
    roi_mask = polygon_to_mask_coords(refined_roi, pre.shape)
    # spatial analysis
    spatial = analyze_spatial_distribution(distance_map=distance_map,
                                           roi_coords=refined_roi,
                                           mm_per_pixel=mm_per_pixel)
    out.update(spatial)
    # flow deficit
    fd = flow_deficit_analysis((bin_mask>0).astype("uint8"), refined_roi, pixel_size_um=pixel_size_um,
                               num_rings=params.get("fd_num_rings",3), enlarge_step_mm=params.get("fd_enlarge_step_mm",0.2))
    out.update(fd)
    # arteriolarization analysis
    arteriol = analyze_arteriolarization(distance_map, skeleton_mask=(bin_mask>0).astype("uint8"),
                                         roi_mask=roi_mask, mm_per_pixel=mm_per_pixel)
    out.update(arteriol)
    # classification
    metrics_for_class = {
        "center_branch": out.get("n_branches",0),
        "periphery_branch": 0,
        "loop_center": out.get("n_endpoints",0),
        "loop_periphery": 0,
        "euler_center": out.get("n_junctions",0)*-1,
        "euler_periphery": 0,
        "vessel_length_center": out.get("total_branch_length_mm",0.0),
        "vessel_length_periphery": 0.0,
        "trunk_eccentricity": out.get("trunk_eccentricity",0.5),
        "angular_distribution_cv": out.get("angular_distribution_cv",0.5),
        "thick_vessel_center_ratio": out.get("thick_vessel_center_ratio",0.0),
        "diameter_center_periphery_ratio": out.get("diameter_center_periphery_ratio",1.0),
        "patternClassification": out.get("patternClassification",""),
        "stability_score": params.get("stability_score",50)
    }
    classification = classify_mnv(metrics_for_class)
    out.update(classification)
    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)
    tiff.imwrite(str(p / (Path(path).stem + "_preprocessed.tif")), pre.astype("uint8"))
    tiff.imwrite(str(p / (Path(path).stem + "_fused.tif")), fused.astype("uint8"))
    tiff.imwrite(str(p / (Path(path).stem + "_binary.tif")), (bin_mask>0).astype("uint8")*255)
    return out
