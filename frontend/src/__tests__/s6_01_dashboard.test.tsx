import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

vi.mock('../stores/authStore', () => ({
  useAuthStore: vi.fn(() => ({
    user: { full_name: 'John Doe', email: 'john@example.com' },
    isAuthenticated: true, isLoading: false,
  })),
}));

// TEST 5: Dashboard renders welcome message
it('should show welcome message with user name', async () => {
  const { default: Dashboard } = await import('../pages/Dashboard');
  render(<MemoryRouter><Dashboard /></MemoryRouter>);
  expect(screen.getByText(/john doe/i) || screen.getByText(/welcome/i)).toBeDefined();
});

// TEST 6: Dashboard has quick start form
it('should render quick start discovery form', async () => {
  const { default: Dashboard } = await import('../pages/Dashboard');
  render(<MemoryRouter><Dashboard /></MemoryRouter>);
  expect(screen.getByText(/start/i)).toBeDefined();
  expect(screen.getByLabelText(/industry/i)).toBeDefined();
});

// TEST 7: Dashboard shows stat cards
it('should render 4 stat cards', async () => {
  const { default: Dashboard } = await import('../pages/Dashboard');
  render(<MemoryRouter><Dashboard /></MemoryRouter>);
  expect(screen.getByText("Total Sessions")).toBeDefined();
  expect(screen.getByText("Problem Statements")).toBeDefined();
  expect(screen.getByText("Approved Solutions")).toBeDefined();
});

// TEST 8: Dashboard has recent sessions section
it('should show recent sessions section', async () => {
  const { default: Dashboard } = await import('../pages/Dashboard');
  render(<MemoryRouter><Dashboard /></MemoryRouter>);
  expect(screen.getAllByText(/recent sessions/i).length).toBeGreaterThan(0);
});

// TEST 9: Dashboard store initializes
it('should initialize dashboard store', async () => {
  const { useDashboardStore } = await import('../stores/dashboardStore');
  const state = useDashboardStore.getState();
  expect(state.stats).toBeNull();
  expect(state.recentSessions).toEqual([]);
  expect(typeof state.fetchDashboardData).toBe('function');
});
