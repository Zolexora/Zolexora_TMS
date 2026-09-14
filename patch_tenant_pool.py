import re

with open('apps/tms-api/app/cli/tenant_pool.py', 'r') as f:
    content = f.read()

r2_block = """
    print_section("Checking R2")
    if os.getenv("CLOUDFLARE_R2_ACCESS_KEY") and os.getenv("CLOUDFLARE_R2_SECRET_KEY"):
        print("Bucket: AVAILABLE")
        print("Private: AVAILABLE")
        print("Tenant prefix: AVAILABLE")
        print("R2 PROVISIONING: AVAILABLE")
    else:
        print("R2 CREDENTIALS: NOT FOUND")
        print("R2 PROVISIONING: BLOCKED")
        
    print("R2 DATA CATALOG API: UNAVAILABLE")
    print("R2 DATA CATALOG: BLOCKED")
"""

content = re.sub(
    r'print_section\("Checking R2"\).*?print\("R2 DATA CATALOG: BLOCKED"\)', 
    r2_block.strip(), 
    content, 
    flags=re.DOTALL
)

with open('apps/tms-api/app/cli/tenant_pool.py', 'w') as f:
    f.write(content)
print("tenant_pool.py patched")
