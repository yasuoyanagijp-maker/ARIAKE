ARIAKE OCTA Python port (prototype)

Quick start:
1. Create venv and install:
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2. Run (example):
   python run_analysis.py --input /path/to/images --output ./results --mode both --scale-mm 6

This repo provides minimal stubs for:
- I/O (scan images, save CSV)
- Preprocessing (CLAHE, background subtraction)
- Filters (Frangi, Gabor, fusion)
- Adaptive binarization (Phansalkar-like)
- Skeleton metrics (skeletonize + graph analysis)
- **FAZ (Foveal Avascular Zone) segmentation**

## FAZ Segmentation

The FAZ segmentation module provides automatic detection and measurement of the 
Foveal Avascular Zone in OCTA images using traditional image processing techniques.

### Features
- Automatic FAZ detection from vessel segmentation
- Morphological operations for boundary detection
- Optional boundary refinement with active contours
- Comprehensive metrics: area, perimeter, circularity, equivalent diameter

### Usage

#### As part of the pipeline:
```python
python run_analysis.py --input /path/to/images --output ./results --mode both --scale-mm 6
```

FAZ metrics will be automatically included in the output CSV.

#### Standalone example:
```python
python examples/faz_segmentation_example.py --input sample.tif --output ./results --scale-mm 6
```

#### In Python code:
```python
from ariake_octa.faz_segmentation import segment_faz
from ariake_octa.preprocess import preprocess_image

# Preprocess image
preprocessed = preprocess_image(image)

# Segment vessels (using your preferred method)
vessel_mask = segment_vessels(preprocessed)

# Segment FAZ
faz_mask, faz_metrics = segment_faz(
    preprocessed, 
    vessel_mask, 
    mm_per_pixel=0.01,
    refine=True
)

print(f"FAZ Area: {faz_metrics['faz_area_mm2']:.3f} mm²")
print(f"FAZ Circularity: {faz_metrics['faz_circularity']:.3f}")
```

### Implementation References

This implementation is inspired by several open-source FAZ segmentation projects:

1. **ShellRedia/SAM-OCTA**: Uses Meta AI's Segment Anything Model (SAM) with LoRA 
   for OCTA segmentation. Supports both FAZ (local mode) and retinal vessels (global mode).

2. **Humogjq/S2Anet**: CNN+Transformer framework with spatial self-awareness for 
   simultaneous FAZ and vessel segmentation. Achieves 98.54% Dice score on OCTA-500.

3. **macarenadiaz/FAZ_Extraction**: Traditional image processing approach using 
   morphological operations, edge detection, and region growing.

4. **llmir/MultitaskOCTA**: Multi-task learning for simultaneous FAZ segmentation 
   and eye disease classification.

The current implementation uses traditional image processing (similar to FAZ_Extraction) 
for broad compatibility and no dependency on deep learning models. Future versions 
may include deep learning approaches when pre-trained weights are available.

