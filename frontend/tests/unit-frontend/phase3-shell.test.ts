import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { api } from '../../src/frontend/api/client';
import { PAGE_COMPONENTS, VALID_ROUTES, resolveInitialRoute } from '../../src/frontend/app/router';
import { ROUTE_ROLES } from '../../src/frontend/app/route-permissions';
import { Button } from '../../src/frontend/components/Button';
import { EmptyState } from '../../src/frontend/components/EmptyState';
import { ErrorState } from '../../src/frontend/components/ErrorState';
import { Input } from '../../src/frontend/components/Input';
import { LoadingState } from '../../src/frontend/components/LoadingState';
import { Select } from '../../src/frontend/components/Select';
import { Table } from '../../src/frontend/components/Table';

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('Phase 3 frontend shell', () => {
  it('registers every documented page route with permissions', () => {
    expect(VALID_ROUTES).toEqual([
      '/login', '/dashboard', '/companies', '/periods', '/groups', '/accounts',
      '/manual-entry', '/entry-history', '/bulk-upload', '/import-history',
      '/reports', '/comparison', '/audit-logs', '/settings',
    ]);
    expect(Object.keys(PAGE_COMPONENTS)).toHaveLength(13);
    expect(Object.keys(PAGE_COMPONENTS).every((path) => path in ROUTE_ROLES)).toBe(true);
  });

  it('resolves known hashes and safe authentication defaults', () => {
    expect(resolveInitialRoute('#/reports', false)).toBe('/reports');
    expect(resolveInitialRoute('#/unknown', false)).toBe('/login');
    expect(resolveInitialRoute('#/unknown', true)).toBe('/dashboard');
  });

  it('renders reusable controls with accessible labels and errors', () => {
    const input = renderToStaticMarkup(React.createElement(Input, {
      id: 'company-code',
      label: 'Company code',
      error: 'Required',
    }));
    expect(input).toContain('for="company-code"');
    expect(input).toContain('aria-invalid="true"');
    expect(input).toContain('aria-describedby="company-code-error"');

    const select = renderToStaticMarkup(React.createElement(Select, {
      id: 'period',
      label: 'Period',
      helperText: 'Choose a reporting period',
      options: [{ value: '2026-07', label: 'July 2026' }],
    }));
    expect(select).toContain('for="period"');
    expect(select).toContain('aria-describedby="period-help"');

    const button = renderToStaticMarkup(React.createElement(Button, { isLoading: true }, 'Save'));
    expect(button).toContain('disabled');
    expect(button).toContain('Save');
  });

  it('renders reusable table, loading, empty, and error states', () => {
    const table = renderToStaticMarkup(React.createElement(Table<{ id: string; name: string }>, {
      columns: [{ key: 'name', header: 'Name' }],
      data: [{ id: '1', name: 'Example company' }],
      keyExtractor: (item) => item.id,
    }));
    expect(table).toContain('<th');
    expect(table).toContain('Example company');
    expect(renderToStaticMarkup(React.createElement(LoadingState))).toContain('Loading dashboard assets');
    expect(renderToStaticMarkup(React.createElement(EmptyState, { description: 'Nothing here' }))).toContain('Nothing here');
    expect(renderToStaticMarkup(React.createElement(ErrorState, { message: 'Try again' }))).toContain('Try again');
  });

  it('preserves plain-text API error responses without consuming the body twice', async () => {
    vi.stubGlobal('localStorage', { getItem: () => null });
    vi.stubGlobal('fetch', vi.fn(async () => new Response('gateway unavailable', { status: 502 })));

    await expect(api.get('/health')).rejects.toMatchObject({
      name: 'ApiError',
      message: 'gateway unavailable',
      status: 502,
    });
  });
});
