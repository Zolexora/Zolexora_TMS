filepath = "apps/backend/app/auth/dependencies.py"
with open(filepath, "r") as f:
    content = f.read()

content = content.replace("m.is_creator\\n            FROM", "m.is_creator,\\n                m.is_commander\\n            FROM")

with open(filepath, "w") as f:
    f.write(content)
