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
