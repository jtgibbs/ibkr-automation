import boto3

s3 = boto3.client('s3')
region = 'us-east-1'  # change if you picked a different region

prefix = "jgs3-automation"  # change jg to your initials

buckets = [
    f"{prefix}-data",      # trading data, CSVs, Parquet files
    f"{prefix}-reports",   # generated reports, email content
    f"{prefix}-logs",      # script logs, error tracking
]

for bucket in buckets:
    if region == 'us-east-1':
        s3.create_bucket(Bucket=bucket)
    else:
        s3.create_bucket(
            Bucket=bucket,
            CreateBucketConfiguration={'LocationConstraint': region}
        )
    print(f"✅ Created: {bucket}")

# Verify
print("\nAll buckets in your account:")
for b in s3.list_buckets()['Buckets']:
    print(f"  📦 {b['Name']}")
