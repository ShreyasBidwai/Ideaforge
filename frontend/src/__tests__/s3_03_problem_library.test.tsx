import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const mockProblem = {
  id: '1', session_id: 's1', title: 'Digital Patient Queue System',
  description: 'Build a digital queue management system for hospitals to reduce patient wait times from 3+ hours to under 30 minutes.',
  target_user: 'Hospital administrators', core_pain: 'Long wait times',
  market_context: 'India healthcare $100B+', severity: 4, feasibility: 5,
  market_size: 4, uniqueness: 3, overall_rating: 4.08, status: 'draft',
  created_at: '2026-05-26T10:00:00Z', updated_at: '2026-05-26T10:00:00Z',
  industry: 'Healthcare'
};

// TEST 1: Problem statement card renders all data
it('should render problem card with title, description, and ratings', async () => {
  const { default: ProblemStatementCard } = await import('../components/problems/ProblemStatementCard');
  render(<MemoryRouter><ProblemStatementCard problem={mockProblem} /></MemoryRouter>);
  expect(screen.getByText('Digital Patient Queue System')).toBeDefined();
  expect(screen.getByText(/Build a digital queue/i)).toBeDefined();
});

// TEST 2: Rating bars render for all 4 dimensions
it('should show 4 rating dimensions', async () => {
  const { default: ProblemStatementCard } = await import('../components/problems/ProblemStatementCard');
  render(<MemoryRouter><ProblemStatementCard problem={mockProblem} /></MemoryRouter>);
  expect(screen.getByText(/sev/i)).toBeDefined();
  expect(screen.getByText(/feas/i)).toBeDefined();
  expect(screen.getByText(/mkt/i)).toBeDefined();
  expect(screen.getByText(/uniq/i)).toBeDefined();
});

// TEST 3: Overall rating badge shows correct value
it('should display overall rating', async () => {
  const { default: ProblemStatementCard } = await import('../components/problems/ProblemStatementCard');
  render(<MemoryRouter><ProblemStatementCard problem={mockProblem} /></MemoryRouter>);
  expect(screen.getByText('4.1') || screen.getByText('4.08')).toBeDefined();
});

// TEST 4: Selected problem shows selected badge
it('should show selected badge when status is selected', async () => {
  const { default: ProblemStatementCard } = await import('../components/problems/ProblemStatementCard');
  const selectedProblem = { ...mockProblem, status: 'selected' as const };
  render(<MemoryRouter><ProblemStatementCard problem={selectedProblem} /></MemoryRouter>);
  expect(screen.getByText(/selected/i)).toBeDefined();
});

// TEST 5: Filter bar renders all filter options
it('should render filter bar with industry, status, sort dropdowns', async () => {
  const { default: ProblemFilters } = await import('../components/problems/ProblemFilters');
  render(<ProblemFilters industries={['Healthcare', 'Fintech']} filters={{
    industry: null, status: null, sortBy: 'overall_rating', sortOrder: 'desc', search: ''
  }} onChange={() => {}} />);
  const selects = screen.getAllByRole('combobox');
  expect(selects.length).toBeGreaterThanOrEqual(2);
});

// TEST 6: Empty library shows CTA
it('should show empty state with discovery CTA', async () => {
  const { default: EmptyLibrary } = await import('../components/problems/EmptyLibrary');
  render(<MemoryRouter><EmptyLibrary /></MemoryRouter>);
  expect(screen.getByText(/no problem statements/i)).toBeDefined();
  expect(screen.getByText(/start discovery/i)).toBeDefined();
});

// TEST 7: Problem store initializes correctly
it('should initialize problem store with empty state', async () => {
  const { useProblemStore } = await import('../stores/problemStore');
  const state = useProblemStore.getState();
  expect(state.problems).toEqual([]);
  expect(state.isLoading).toBe(false);
  expect(state.filters.sortBy).toBe('overall_rating');
});

// TEST 8: RatingBar renders with correct value
it('should render rating bar with value', async () => {
  const { default: RatingBar } = await import('../components/problems/RatingBar');
  render(<RatingBar label="SEV" value={4} maxValue={5} />);
  expect(screen.getByText('SEV')).toBeDefined();
  expect(screen.getByText('4.0')).toBeDefined();
});

// TEST 9: Library page renders
it('should render problem library page', async () => {
  const { default: ProblemLibrary } = await import('../pages/ProblemLibrary');
  render(<MemoryRouter><ProblemLibrary /></MemoryRouter>);
  expect(screen.getByRole('heading', { name: /problem library/i })).toBeDefined();
});
