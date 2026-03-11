import sys
import pandas as pd
import numpy as np

print(f"Python version: {sys.version}")
print(f"pandas version: {pd.__version__}")
print(f"numpy version: {np.__version__}")

df = pd.DataFrame({
    'task': ['IAM Setup', 'EC2 Launch', 'Python Install', 'Test Script'],
    'status': ['Done', 'Done', 'Done', 'Running']
})
print(f"\nRoadmap Progress:\n{df.to_string(index=False)}")
print("\n✅ All systems go!")
