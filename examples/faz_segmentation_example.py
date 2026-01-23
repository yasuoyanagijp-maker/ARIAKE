#!/usr/bin/env python
"""
Example script demonstrating FAZ (Foveal Avascular Zone) segmentation.

This script shows how to use the FAZ segmentation functionality
to detect and analyze the avascular zone in OCTA images.

Based on approaches from:
- macarenadiaz/FAZ_Extraction: Traditional image processing
- ShellRedia/SAM-OCTA: Deep learning with SAM
- Humogjq/S2Anet: CNN+Transformer hybrid

Usage:
    python examples/faz_segmentation_example.py --input image.tif --output results/
"""

import argparse
import numpy as np
import tifffile as tiff
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ariake_octa.preprocess import preprocess_image
from ariake_octa.filters import multi_scale_frangi, gabor_filter_max, fuse_filters
from ariake_octa.binarize import adaptive_binarize_phansalkar
from ariake_octa.faz_segmentation import segment_faz


def load_image(path):
    """Load and convert image to grayscale."""
    img = tiff.imread(str(path))
    if img.ndim == 3 and img.shape[2] == 3:
        img_gray = img[:, :, 1]  # Use green channel
    else:
        img_gray = img
    return img_gray


def visualize_results(image, vessel_mask, faz_mask, metrics, output_path=None):
    """Visualize segmentation results."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 12))
    
    # Original image
    axes[0, 0].imshow(image, cmap='gray')
    axes[0, 0].set_title('Original OCTA Image')
    axes[0, 0].axis('off')
    
    # Vessel segmentation
    axes[0, 1].imshow(image, cmap='gray')
    axes[0, 1].imshow(vessel_mask, alpha=0.3, cmap='Reds')
    axes[0, 1].set_title('Vessel Segmentation')
    axes[0, 1].axis('off')
    
    # FAZ segmentation
    axes[1, 0].imshow(image, cmap='gray')
    axes[1, 0].imshow(faz_mask, alpha=0.5, cmap='Blues')
    if np.any(faz_mask):
        # Mark centroid
        cx = metrics.get('faz_centroid_x_px', image.shape[1] / 2)
        cy = metrics.get('faz_centroid_y_px', image.shape[0] / 2)
        axes[1, 0].plot(cx, cy, 'r+', markersize=15, markeredgewidth=2)
    axes[1, 0].set_title('FAZ Segmentation')
    axes[1, 0].axis('off')
    
    # Metrics text
    axes[1, 1].axis('off')
    metrics_text = "FAZ Metrics:\n\n"
    metrics_text += f"Area: {metrics.get('faz_area_mm2', 0):.3f} mm²\n"
    metrics_text += f"Perimeter: {metrics.get('faz_perimeter_mm', 0):.3f} mm\n"
    metrics_text += f"Circularity: {metrics.get('faz_circularity', 0):.3f}\n"
    metrics_text += f"Equiv. Diameter: {metrics.get('faz_equivalent_diameter_mm', 0):.3f} mm\n"
    metrics_text += f"Acircularity: {metrics.get('faz_acircularity', 0):.3f}\n"
    
    axes[1, 1].text(0.1, 0.5, metrics_text, fontsize=12, 
                    verticalalignment='center', family='monospace')
    axes[1, 1].set_title('Measurements')
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Visualization saved to: {output_path}")
    else:
        plt.show()
    
    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description="FAZ Segmentation Example",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--input", required=True, help="Input OCTA image (TIFF)")
    parser.add_argument("--output", default="./results", help="Output directory")
    parser.add_argument("--scale-mm", type=float, default=6.0, 
                       help="Image width in mm (default: 6.0)")
    parser.add_argument("--refine", action="store_true",
                       help="Refine FAZ boundary with active contour")
    parser.add_argument("--visualize", action="store_true",
                       help="Show visualization window")
    
    args = parser.parse_args()
    
    # Load image
    print(f"Loading image: {args.input}")
    image = load_image(args.input)
    print(f"Image shape: {image.shape}")
    
    # Preprocess
    print("Preprocessing...")
    preprocessed = preprocess_image(image, clahe_clip=3.0, background_sigma=5.0)
    
    # Vessel segmentation
    print("Segmenting vessels...")
    frangi = multi_scale_frangi(preprocessed)
    gabor = gabor_filter_max(preprocessed)
    fused = fuse_filters([frangi, gabor], weights=[0.4, 0.4])
    vessel_mask = adaptive_binarize_phansalkar(fused, radius=15, k=0.1, R=128)
    vessel_mask = vessel_mask > 0
    
    # Calculate pixel size
    mm_per_pixel = args.scale_mm / image.shape[1]
    print(f"Pixel size: {mm_per_pixel:.6f} mm/pixel")
    
    # FAZ segmentation
    print("Segmenting FAZ...")
    faz_mask, faz_metrics = segment_faz(
        preprocessed,
        vessel_mask,
        mm_per_pixel=mm_per_pixel,
        refine=args.refine,
        min_area_px=100
    )
    
    # Print metrics
    print("\n=== FAZ Segmentation Results ===")
    print(f"FAZ Area: {faz_metrics['faz_area_mm2']:.3f} mm²")
    print(f"FAZ Perimeter: {faz_metrics['faz_perimeter_mm']:.3f} mm")
    print(f"FAZ Circularity: {faz_metrics['faz_circularity']:.3f}")
    print(f"FAZ Equivalent Diameter: {faz_metrics['faz_equivalent_diameter_mm']:.3f} mm")
    print(f"FAZ Acircularity: {faz_metrics['faz_acircularity']:.3f}")
    
    if np.any(faz_mask):
        cx = faz_metrics.get('faz_centroid_x_px', 0)
        cy = faz_metrics.get('faz_centroid_y_px', 0)
        print(f"FAZ Centroid: ({cx:.1f}, {cy:.1f}) pixels")
    else:
        print("Warning: No FAZ detected!")
    
    # Save results
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    input_stem = Path(args.input).stem
    
    # Save masks
    tiff.imwrite(str(output_dir / f"{input_stem}_vessel_mask.tif"), 
                vessel_mask.astype(np.uint8) * 255)
    tiff.imwrite(str(output_dir / f"{input_stem}_faz_mask.tif"), 
                faz_mask.astype(np.uint8) * 255)
    
    print(f"\nResults saved to: {output_dir}")
    
    # Visualization
    viz_path = output_dir / f"{input_stem}_faz_visualization.png"
    visualize_results(preprocessed, vessel_mask, faz_mask, faz_metrics, 
                     output_path=viz_path if not args.visualize else None)
    
    if args.visualize:
        visualize_results(preprocessed, vessel_mask, faz_mask, faz_metrics)


if __name__ == "__main__":
    main()
