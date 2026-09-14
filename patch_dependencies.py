import re

with open('apps/tms-api/app/auth/dependencies.py', 'r') as f:
    content = f.read()

fallback_code = """
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant infrastructure is not fully provisioned for this organisation.",
        )
"""

content = re.sub(
    r'# Fallback to defaults or raise error.*?r2_prefix=f"organisations/\{user\.organisation_id\}/"\n        \)', 
    fallback_code.strip(), 
    content, 
    flags=re.DOTALL
)

with open('apps/tms-api/app/auth/dependencies.py', 'w') as f:
    f.write(content)
print("dependencies patched")
