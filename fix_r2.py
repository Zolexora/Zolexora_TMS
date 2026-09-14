import os
env_files = ['apps/tms-api/.env', '.env']
r2_access = "4035f68fc303323d30795e8d9cd5c2e1"
r2_secret = "e387b16d4d55039bbde1e4dad93f73b8569d4a7f6bdaa018d481f5f1c274bbe4"
r2_endpoint = "https://62f44d3cd69c56e16e40ee42a3fdc2ed.r2.cloudflarestorage.com"
r2_bucket = "zolexora-tms-dev"

for ef in env_files:
    if os.path.exists(ef):
        with open(ef, 'a') as f:
            f.write(f"\nCLOUDFLARE_R2_ACCESS_KEY={r2_access}\n")
            f.write(f"CLOUDFLARE_R2_SECRET_KEY={r2_secret}\n")
            f.write(f"R2_ENDPOINT_URL={r2_endpoint}\n")
print("R2 credentials injected.")
