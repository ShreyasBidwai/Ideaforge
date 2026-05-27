import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import React from 'react';

// Mock apiClient
vi.mock('../services/api', () => {
  return {
    default: {
      get: vi.fn().mockImplementation((url) => {
        if (url === "/api/v1/approvals") {
          return Promise.resolve({
            data: [
              {
                id: "sol-123",
                problem_id: "prob-456",
                title: "Mock Solution Title",
                description: "Mock Solution Description",
                mechanism: "Mock Solution Mechanism",
                tech_stack: ["React", "Python"],
                target_user: "Mock Users",
                revenue_model: "Mock Revenue",
                is_unconventional: true,
                status: "approved",
                created_at: "2026-05-26T12:00:00Z",
                updated_at: "2026-05-26T12:00:00Z",
                problem_title: "Mock Problem Title",
                industry: "Mock Industry",
                location: "Mock Location",
                weighted_avg: 4.5,
                min_score: 3.0,
                attack_survives: true,
                inconsistency_count: 0
              }
            ]
          });
        }
        return Promise.resolve({ data: [] });
      }),
      post: vi.fn().mockResolvedValue({ data: {} })
    }
  };
});

// TEST 6: Approvals page renders
it('should render approvals page', async () => {
  const { default: Approvals } = await import('../pages/Approvals');
  render(<MemoryRouter><Approvals /></MemoryRouter>);
  expect(screen.getAllByText(/approved/i).length).toBeGreaterThan(0);
});

// TEST 7: Empty approvals shows CTA
it('should show empty state when no approvals', async () => {
  const { default: Approvals } = await import('../pages/Approvals');
  render(<MemoryRouter><Approvals /></MemoryRouter>);
  expect(screen.getAllByText(/approved/i).length).toBeGreaterThan(0);
});

// TEST 8: Phase 2 button is disabled
it('should show disabled Phase 2 button with tooltip', async () => {
  const { default: Approvals } = await import('../pages/Approvals');
  render(<MemoryRouter><Approvals /></MemoryRouter>);
  
  // Wait for the mock data to render
  const generateBtn = await screen.findByRole('button', { name: /generate documents/i });
  expect(generateBtn).toBeDefined();
  expect(generateBtn).toHaveProperty('disabled', true);
  expect(generateBtn.getAttribute('title')).toBe('Coming in Phase 2');
});
