with open("apps/tms/src/App.tsx", "r") as f:
    content = f.read()

content = content.replace(
    "import { SettingsPage } from './features/settings/SettingsPage';",
    "import { SettingsPage } from './features/settings/SettingsPage';\nimport { R1TikriOperationsPage } from './features/extensions/r1rcm/R1TikriOperationsPage';"
)

with open("apps/tms/src/App.tsx", "w") as f:
    f.write(content)
