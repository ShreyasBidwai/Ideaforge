import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import React from 'react';

// Mock authStore to avoid loading state
vi.mock('../stores/authStore', () => ({
  useAuthStore: vi.fn(() => ({
    user: { full_name: 'John Doe', email: 'john@example.com' },
    isAuthenticated: true,
    isLoading: false,
  })),
}));

// Mock apiClient to return mock data for all API requests
vi.mock('../services/api', () => {
  return {
    default: {
      get: vi.fn().mockImplementation((url) => {
        if (url.includes("/solutions")) {
          return Promise.resolve({ data: [] });
        }
        if (url.includes("/industries")) {
          return Promise.resolve({ data: [] });
        }
        if (url.includes("/api/v1/problem-statements/")) {
          // Single problem statement
          return Promise.resolve({
            data: {
              id: "test-problem-id",
              title: "Mock Problem Title",
              description: "Mock Description",
              overall_rating: 4.5,
              status: "selected",
              industry: "Mock Industry",
              location: "Mock Location"
            }
          });
        }
        if (url.includes("/evaluation")) {
          // Evaluation data
          return Promise.resolve({
            data: {
              rubric: {
                criteria: [
                  { name: "Feasibility", description: "Feas", weight: 2, scale: { "1": "No", "3": "Maybe", "5": "Yes" } }
                ],
                disqualifiers: []
              },
              is_rubric_locked: true,
              disqualifier_results: [],
              scores: {},
              attacks: {},
              ach_analysis: {},
              comparison: {
                entries: [
                  {
                    solution_title: "Mock Solution",
                    weighted_avg: 4.2,
                    min_score: 3,
                    attack_survives: true,
                    attack_summary: "Survives",
                    inconsistency_count: 0
                  }
                ],
                leaders: {
                  weighted_avg: "Mock Solution",
                  min_score: "Mock Solution"
                },
                is_clear_winner: true,
                disagreements: []
              }
            }
          });
        }
        if (url === "/api/v1/maturity-levels") {
          return Promise.resolve({
            data: [
              { level: "mvp", label: "MVP", description: "MVP desc" }
            ]
          });
        }
        if (url === "/api/v1/approvals") {
          return Promise.resolve({ data: [] });
        }
        return Promise.resolve({ data: [] });
      }),
      post: vi.fn().mockResolvedValue({ data: {} })
    }
  };
});

describe('IdeaForge End-to-End Flow Integration Tests', () => {
  // TEST 1: Main routes render without error
  it('should render main page routes without error', async () => {
    // Dashboard Page
    const { default: Dashboard } = await import('../pages/Dashboard');
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );
    expect(screen.getByText(/recent sessions/i) || screen.getByText(/welcome/i)).toBeDefined();

    // Discovery Page
    const { default: Discovery } = await import('../pages/Discovery');
    render(
      <MemoryRouter>
        <Discovery />
      </MemoryRouter>
    );
    expect(screen.getByRole('heading', { name: /Discover Industry Pain Points/i })).toBeDefined();

    // Problem Library Page
    const { ProblemLibrary } = await import('../pages/ProblemLibrary');
    render(
      <MemoryRouter>
        <ProblemLibrary />
      </MemoryRouter>
    );
    expect(screen.getByText(/problem library/i)).toBeDefined();

    // Approvals Page
    const { default: Approvals } = await import('../pages/Approvals');
    render(
      <MemoryRouter>
        <Approvals />
      </MemoryRouter>
    );
    expect(screen.getByRole('heading', { name: /Approved Solutions/i })).toBeDefined();
  });

  // TEST 2: Solution Workspace renders with route param
  it('should render solution workspace page when given a problemId param', async () => {
    const { default: SolutionWorkspace } = await import('../pages/SolutionWorkspace');
    render(
      <MemoryRouter initialEntries={['/workspace/test-problem-id']}>
        <Routes>
          <Route path="/workspace/:problemId" element={<SolutionWorkspace />} />
        </Routes>
      </MemoryRouter>
    );
    const runBtn = await screen.findByText(/Run Evaluation/i);
    expect(runBtn).toBeDefined();
  });

  // TEST 3: Evaluation page renders with route param
  it('should render evaluation wizard page when given a problemId param', async () => {
    const { default: Evaluation } = await import('../pages/Evaluation');
    render(
      <MemoryRouter initialEntries={['/evaluation/test-problem-id']}>
        <Routes>
          <Route path="/evaluation/:problemId" element={<Evaluation />} />
        </Routes>
      </MemoryRouter>
    );
    const wizardHeader = await screen.findByText(/Evaluation Protocol Wizard/i);
    expect(wizardHeader).toBeDefined();
  });

  // TEST 4: Toast store adds success/error toasts
  it('should correctly add and track toasts in the toast store', async () => {
    const { useToastStore } = await import('../stores/toastStore');
    const store = useToastStore.getState();

    // Add success toast
    store.addToast('success', 'Flow integration test success message');
    expect(useToastStore.getState().toasts.some(t => t.message === 'Flow integration test success message' && t.type === 'success')).toBe(true);

    // Add error toast
    store.addToast('error', 'Flow integration test error message');
    expect(useToastStore.getState().toasts.some(t => t.message === 'Flow integration test error message' && t.type === 'error')).toBe(true);
  });
});
