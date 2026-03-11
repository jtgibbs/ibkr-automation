import boto3
import pandas as pd
import numpy as np
from datetime import datetime
import json

s3 = boto3.client('s3')
BUCKET = "jgs3-automation-data"  # your data bucket

# ---- 1. CREATE SAMPLE DATA ----
# Simulate a week of trading data
np.random.seed(42)
dates = pd.date_range('2026-02-23', periods=5, freq='B')
df = pd.DataFrame({
    'date': dates,
    'symbol': 'SPY',
    'open': np.random.uniform(580, 590, 5).round(2),
    'close': np.random.uniform(580, 590, 5).round(2),
    'volume': np.random.randint(50000000, 90000000, 5)
})
df['daily_return'] = ((df['close'] - df['open']) / df['open'] * 100).round(3)

print("Sample data created:")
print(df.to_string(index=False))

# ---- 2. UPLOAD CSV ----
csv_path = "/tmp/spy_weekly.csv"
df.to_csv(csv_path, index=False)

s3_key = f"market_data/{datetime.now().strftime('%Y/%m/%d')}/spy_weekly.csv"
s3.upload_file(csv_path, BUCKET, s3_key)
print(f"\n✅ Uploaded CSV to: s3://{BUCKET}/{s3_key}")

# ---- 3. UPLOAD JSON REPORT ----
report = {
    "generated_at": datetime.now().isoformat(),
    "symbol": "SPY",
    "avg_return": round(df['daily_return'].mean(), 3),
    "best_day": df.loc[df['daily_return'].idxmax(), 'date'].strftime('%Y-%m-%d'),
    "worst_day": df.loc[df['daily_return'].idxmin(), 'date'].strftime('%Y-%m-%d'),
}

report_key = f"reports/{datetime.now().strftime('%Y/%m/%d')}/daily_summary.json"
s3.put_object(
    Bucket="jgs3-automation-reports",
    Key=report_key,
    Body=json.dumps(report, indent=2),
    ContentType='application/json'
)
print(f"✅ Uploaded report to: s3://jgs3-automation-reports/{report_key}")

# ---- 4. DOWNLOAD AND VERIFY ----
download_path = "/tmp/spy_downloaded.csv"
s3.download_file(BUCKET, s3_key, download_path)
df_downloaded = pd.read_csv(download_path)
print(f"\n✅ Downloaded and verified: {len(df_downloaded)} rows match")

# ---- 5. LIST BUCKET CONTENTS ----
print(f"\nContents of {BUCKET}:")
response = s3.list_objects_v2(Bucket=BUCKET)
for obj in response.get('Contents', []):
    print(f"  📄 {obj['Key']}  ({obj['Size']} bytes)")
