import os

path = "apps/tms-api/app/modules/organisations/service.py"
with open(path, "r") as f:
    content = f.read()

# Replace audit_log insertions
content = content.replace("from app.modules.audit.models import AuditLog", "")
if "audit = AuditLog(" in content:
    lines = content.split('\n')
    new_lines = []
    skip = False
    for line in lines:
        if "audit = AuditLog(" in line:
            skip = True
        if skip and "db.add(audit)" in line:
            skip = False
            continue
        if not skip:
            new_lines.append(line)
    
    with open(path, "w") as f:
        f.write('\n'.join(new_lines))

print("Patched.")
