import re

with open("apps/tms/src/features/rate-cards/RateCardsPage.tsx", "r") as f:
    content = f.read()

import_statement = "import { RateCardForm } from './RateCardForm';\n"
content = content.replace("import { apiClient } from '../../lib/api';", "import { apiClient } from '../../lib/api';\n" + import_statement)

# Add state
state_statement = "  const [searchTerm, setSearchTerm] = useState('');\n  const [isFormOpen, setIsFormOpen] = useState(false);\n"
content = content.replace("  const [searchTerm, setSearchTerm] = useState('');", state_statement)

# Fix button
button_old = """<button className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-600/30 hover:bg-indigo-500 transition">"""
button_new = """<button onClick={() => setIsFormOpen(true)} className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-600/30 hover:bg-indigo-500 transition">"""
content = content.replace(button_old, button_new)

# Add modal at the end
modal_code = """      {isFormOpen && <RateCardForm onClose={() => setIsFormOpen(false)} />}
    </div>
  );
}"""
content = content.replace("    </div>\n  );\n}", modal_code)

with open("apps/tms/src/features/rate-cards/RateCardsPage.tsx", "w") as f:
    f.write(content)
