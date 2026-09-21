import re

filepath = "apps/frontend/zolexora-tms/src/App.tsx"
with open(filepath, "r") as f:
    content = f.read()

content = content.replace(
    "import { SettingsPage } from './features/onboarding/SettingsPage';",
    "import { WorkspaceSettingsPage } from './features/organization/WorkspaceSettingsPage';"
)

content = content.replace(
    "<Route path=\"/settings\" element={<SettingsPage />} />",
    "<Route path=\"/settings\" element={<WorkspaceSettingsPage />} />"
)

with open(filepath, "w") as f:
    f.write(content)
