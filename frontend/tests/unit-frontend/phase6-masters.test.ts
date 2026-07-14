import { describe, expect, it } from 'vitest';
import fs from 'node:fs';

describe('Phase 6 master UI contracts', () => {
  it('uses stable account IDs as dropdown values', () => {
    const source = fs.readFileSync('src/frontend/features/accounts/components/AccountSelect.tsx', 'utf8');
    expect(source).toContain('value={account.id}');
    expect(source).not.toContain('value={account.name}');
  });

  it('exposes company-scoped account search and status filtering', () => {
    const source = fs.readFileSync('src/frontend/features/accounts/pages/AccountsPage.tsx', 'utf8');
    expect(source).toContain('search=${encodeURIComponent(search)}');
    expect(source).toContain('is_active=${activeFilter}');
    expect(source).toContain('Posted balances are immutable');
  });
});
