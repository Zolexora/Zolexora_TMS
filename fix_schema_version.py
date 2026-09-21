filepath = "apps/backend/app/modules/core/platform/models.py"
with open(filepath, "r") as f:
    content = f.read()

content = content.replace("schema_version = Column(Integer, nullable=False, default=0)", "schema_version = Column(Integer, nullable=False, server_default='0', default=0)")

with open(filepath, "w") as f:
    f.write(content)
