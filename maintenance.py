def convert_numpy(obj):
    import numpy as np
    import pandas as pd
    import json

    if isinstance(obj, dict):
        # Ensure all keys are stringified to avoid JSON issues with mixed keys
        return {str(k): convert_numpy(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy(i) for i in obj]
    elif isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    elif isinstance(obj, pd.Series):
        return convert_numpy(obj.to_dict())
    elif isinstance(obj, pd.DataFrame):
        return convert_numpy(obj.to_dict(orient="records"))
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, (np.str_, str)):
        return str(obj)
    elif obj is None:
        return None
    else:
        try:
            json.dumps(obj)  # test serialization
            return obj
        except TypeError:
            return str(obj)



def wipe_all_files_in_folder(folder_path, max_age_minutes=None):
    import os
    import time
    now = time.time()
    deleted = 0
    for fname in os.listdir(folder_path):
        fpath = os.path.join(folder_path, fname)
        if os.path.isfile(fpath):
            age_minutes = (now - os.path.getmtime(fpath)) / 60
            if max_age_minutes is None or age_minutes > max_age_minutes:
                try:
                    os.remove(fpath)
                    deleted += 1
                except Exception as e:
                    print(f"⚠️ Could not delete {fpath}: {e}")
    print(f"🧹 Wiped {deleted} file(s) from {folder_path}")