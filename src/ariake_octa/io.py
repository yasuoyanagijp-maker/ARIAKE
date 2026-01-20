from pathlib import Path
import fnmatch
import pandas as pd

def scan_images(folder, pattern="*.tif"):
    p = Path(folder)
    files = [str(f) for f in p.rglob(pattern)]
    files.sort()
    return files

def save_results_table(rows, outpath):
    df = pd.DataFrame(rows)
    if df.shape[0] == 0:
        # write minimal header so CSV is not empty
        with open(outpath,'w') as fh:
            fh.write('file\n')
        return outpath
    df.to_csv(outpath, index=False)
    return outpath
