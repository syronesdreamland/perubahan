from shortGPT.config.asset_db import AssetDatabase, AssetType
from pathlib import Path
import os

# Ensure we are in the right directory or adjust paths
# Assuming running from ShortGPT/ directory

path = Path('public/black_background.mp4')
if path.exists():
    print(f"Found file at {path.absolute()}")
    # Force add/update
    AssetDatabase.add_local_asset("black_background", AssetType.BACKGROUND_VIDEO, str(path))
    print("Added black_background as BACKGROUND_VIDEO")
    
    # Verify
    df = AssetDatabase.get_df()
    print(df[df['name'] == 'black_background'])
else:
    print(f"File not found at {path.absolute()}")
