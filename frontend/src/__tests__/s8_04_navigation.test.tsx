import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

beforeEach(() => {
  localStorage.setItem("sidebar_collapsed", "false");
});

// TEST 1: Sidebar has Projects link
it('should show Projects in sidebar', async () => {
  vi.mock('../stores/authStore', () => ({
    useAuthStore: vi.fn(() => ({
      isAuthenticated: true, isLoading: false,
      user: { full_name: 'Test User', email: 'test@test.com' },
      logout: vi.fn(),
    })),
  }));
  const { default: AppShell } = await import('../components/layout/AppShell');
  render(<MemoryRouter><AppShell /></MemoryRouter>);
  expect(screen.getByText(/projects/i)).toBeDefined();
});

// TEST 2: Projects list page renders
it('should render projects list page', async () => {
  const { default: ProjectsList } = await import('../pages/ProjectsList');
  render(<MemoryRouter><ProjectsList /></MemoryRouter>);
  expect(screen.getByText(/projects/i)).toBeDefined();
});

// TEST 3: Project routes are accessible
it('should render project detail route', async () => {
  const { default: ProjectDetail } = await import('../pages/ProjectDetail');
  const { Route, Routes } = await import('react-router-dom');
  render(<MemoryRouter initialEntries={['/projects/test-id']}>
    <Routes><Route path="/projects/:projectId" element={<ProjectDetail />} /></Routes>
  </MemoryRouter>);
});

// TEST 4: Build dashboard route works
it('should render build dashboard route', async () => {
  const { default: BuildDashboard } = await import('../pages/BuildDashboard');
  const { Route, Routes } = await import('react-router-dom');
  render(<MemoryRouter initialEntries={['/projects/test-id/build']}>
    <Routes><Route path="/projects/:projectId/build" element={<BuildDashboard />} /></Routes>
  </MemoryRouter>);
});

// TEST 5: Sidebar has Discover and Build sections
it('should have discover and build nav sections', async () => {
  vi.mock('../stores/authStore', () => ({
    useAuthStore: vi.fn(() => ({
      isAuthenticated: true, isLoading: false,
      user: { full_name: 'Test', email: 'test@test.com' },
      logout: vi.fn(),
    })),
  }));
  const { default: AppShell } = await import('../components/layout/AppShell');
  render(<MemoryRouter><AppShell /></MemoryRouter>);
  expect(screen.getAllByText(/dashboard/i)[0]).toBeDefined();
  expect(screen.getByText(/discovery/i)).toBeDefined();
  expect(screen.getByText(/projects/i)).toBeDefined();
});
