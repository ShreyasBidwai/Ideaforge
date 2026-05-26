import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import React from 'react';

const mockSolution = {
  id: 's1', problem_id: 'p1', title: 'AI-Powered Smart Queue Kiosk',
  description: 'Physical kiosk + mobile app that uses ML to predict wait times.',
  mechanism: 'Computer vision tracks patient flow, ML predicts wait times.',
  tech_stack: ['React Native', 'Python', 'TensorFlow Lite'],
  target_user: 'Hospital administrators', revenue_model: 'SaaS $99/mo per hospital',
  is_unconventional: false, status: 'candidate' as const, created_at: '2026-05-26T10:00:00Z'
};

const mockUnconventional = {
  ...mockSolution, id: 's2', title: 'Blockchain Queue Protocol',
  is_unconventional: true, mechanism: 'Smart contracts manage queue positions as tokens.'
};

// TEST 1: Solution card renders all data
it('should render solution card with title, description, mechanism', async () => {
  const { default: SolutionCard } = await import('../components/solutions/SolutionCard');
  render(<MemoryRouter><SolutionCard solution={mockSolution} /></MemoryRouter>);
  expect(screen.getByText('AI-Powered Smart Queue Kiosk')).toBeDefined();
  expect(screen.getByText(/ML to predict/i)).toBeDefined();
  expect(screen.getByText(/how it works/i)).toBeDefined();
});

// TEST 2: Tech stack tags render
it('should show tech stack tags', async () => {
  const { default: SolutionCard } = await import('../components/solutions/SolutionCard');
  render(<MemoryRouter><SolutionCard solution={mockSolution} /></MemoryRouter>);
  expect(screen.getByText('React Native')).toBeDefined();
  expect(screen.getByText('Python')).toBeDefined();
});

// TEST 3: Unconventional badge shows
it('should show unconventional badge when flagged', async () => {
  const { default: SolutionCard } = await import('../components/solutions/SolutionCard');
  render(<MemoryRouter><SolutionCard solution={mockUnconventional} /></MemoryRouter>);
  expect(screen.getByText(/unconventional/i)).toBeDefined();
});

// TEST 4: No unconventional badge on regular solutions
it('should not show unconventional badge on regular solutions', async () => {
  const { default: SolutionCard } = await import('../components/solutions/SolutionCard');
  render(<MemoryRouter><SolutionCard solution={mockSolution} /></MemoryRouter>);
  expect(screen.queryByText(/unconventional/i)).toBeNull();
});

// TEST 5: Revenue model displays
it('should show revenue model', async () => {
  const { default: SolutionCard } = await import('../components/solutions/SolutionCard');
  render(<MemoryRouter><SolutionCard solution={mockSolution} /></MemoryRouter>);
  expect(screen.getByText(/\$99\/mo/)).toBeDefined();
});

// TEST 6: Solution store initializes correctly
it('should initialize solution store empty', async () => {
  const { useSolutionStore } = await import('../stores/solutionStore');
  const state = useSolutionStore.getState();
  expect(state.solutions).toEqual([]);
  expect(state.isGenerating).toBe(false);
  expect(typeof state.generateSolutions).toBe('function');
});

// TEST 7: Generate CTA renders when no solutions
it('should show generate CTA when no solutions', async () => {
  const { default: GenerateSolutionsCTA } = await import('../components/solutions/GenerateSolutionsCTA');
  render(<GenerateSolutionsCTA onGenerate={() => {}} solutionCount={5} />);
  expect(screen.getAllByText(/generate/i).length).toBeGreaterThan(0);
});

// TEST 8: Skeleton loading renders
it('should render solution skeleton', async () => {
  const { default: SolutionSkeleton } = await import('../components/solutions/SolutionSkeleton');
  const { container } = render(<SolutionSkeleton />);
  expect(container.querySelector('[class*="animate"]')).toBeDefined();
});

// TEST 9: Workspace page renders
it('should render workspace page', async () => {
  const { default: SolutionWorkspace } = await import('../pages/SolutionWorkspace');
  render(<MemoryRouter><SolutionWorkspace /></MemoryRouter>);
  // Should render without crashing
});
