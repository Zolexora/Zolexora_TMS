import re

with open("backend/app/modules/customization/models.py", "r") as f:
    content = f.read()

# For every class that has application_id, we add customer_id right below it.
# We skip OrganisationApplication itself.
models = [
    "ApplicationModule",
    "ApplicationConfiguration",
    "ApplicationWorkflow",
    "ApplicationRule",
    "ApplicationForm",
    "ApplicationReport",
    "ApplicationApproval"
]

for model in models:
    pattern = rf"(class {model}\(Base\):[\s\S]*?application_id = Column\(.*?index=True\))"
    replacement = r"\1\n    customer_id = Column(UUID(as_uuid=True), nullable=True, index=True)"
    content = re.sub(pattern, replacement, content, count=1)

with open("backend/app/modules/customization/models.py", "w") as f:
    f.write(content)
