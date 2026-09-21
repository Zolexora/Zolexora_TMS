import re

filepath = "apps/frontend/zolexora-tms/src/features/auth/useAuth.ts"
with open(filepath, "r") as f:
    content = f.read()

content = content.replace("authMe?.role_code === 'COMMANDER'", "authMe?.is_commander === true")

with open(filepath, "w") as f:
    f.write(content)
