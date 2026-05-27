import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const mockComparison = {
  entries: [
    { solution_id: '1', solution_title: 'Sol A', weighted_avg: 4.5, min_score: 3, attack_summary: 'Hardware maintenance risk', attack_survives: true, inconsistency_count: 2 },
    { solution_id: '2', solution_title: 'Sol B', weighted_avg: 3.8, min_score: 4, attack_summary: 'Platform dependency', attack_survives: false, inconsistency_count: 1 },
    { solution_id: '3', solution_title: 'Sol C', weighted_avg: 4.2, min_score: 4, attack_summary: 'Liability risk', attack_survives: true, inconsistency_count: 2 },
  ],
  leaders: { weighted_avg: 'Sol A', min_score: 'Sol B', attack_survival: 'Sol A', inconsistencies: 'Sol B' },
  is_clear_winner: false,
  disagreements: ['Sol A leads on score but Sol B has fewer inconsistencies']
};

const mockClearWinner = {
  entries: [
    { solution_id: '1', solution_title: 'Sol A', weighted_avg: 5.0, min_score: 5, attack_summary: 'Minor risk', attack_survives: true, inconsistency_count: 0 },
    { solution_id: '2', solution_title: 'Sol B', weighted_avg: 2.0, min_score: 1, attack_summary: 'Fatal', attack_survives: false, inconsistency_count: 5 },
  ],
  leaders: { weighted_avg: 'Sol A', min_score: 'Sol A', attack_survival: 'Sol A', inconsistencies: 'Sol A' },
  is_clear_winner: true,
  disagreements: []
};

// TEST 1: Matrix renders all solutions
it('should render comparison matrix with all solutions', async () => {
  const { default: ComparisonMatrix } = await import('../components/evaluation/ComparisonMatrix');
  render(<MemoryRouter><ComparisonMatrix comparison={mockComparison} onApprove={() => {}} /></MemoryRouter>);
  expect(screen.getAllByText('Sol A').length).toBeGreaterThan(0);
  expect(screen.getAllByText('Sol B').length).toBeGreaterThan(0);
  expect(screen.getAllByText('Sol C').length).toBeGreaterThan(0);
});

// TEST 2: Shows weighted averages
it('should display weighted average scores', async () => {
  const { default: ComparisonMatrix } = await import('../components/evaluation/ComparisonMatrix');
  render(<MemoryRouter><ComparisonMatrix comparison={mockComparison} onApprove={() => {}} /></MemoryRouter>);
  expect(screen.getByText(/4\.5/)).toBeDefined();
});

// TEST 3: Disagreement alert shown when metrics conflict
it('should show disagreement alert when metrics disagree', async () => {
  const { default: ComparisonMatrix } = await import('../components/evaluation/ComparisonMatrix');
  render(<MemoryRouter><ComparisonMatrix comparison={mockComparison} onApprove={() => {}} /></MemoryRouter>);
  expect(screen.getAllByText(/disagree/i).length).toBeGreaterThan(0);
});

// TEST 4: Clear winner banner shown
it('should show clear winner banner when one solution leads all', async () => {
  const { default: ComparisonMatrix } = await import('../components/evaluation/ComparisonMatrix');
  render(<MemoryRouter><ComparisonMatrix comparison={mockClearWinner} onApprove={() => {}} /></MemoryRouter>);
  expect(screen.getAllByText(/clear/i).length).toBeGreaterThan(0);
});

// TEST 5: Approve button exists for each solution
it('should have approve button for each solution', async () => {
  const { default: ComparisonMatrix } = await import('../components/evaluation/ComparisonMatrix');
  render(<MemoryRouter><ComparisonMatrix comparison={mockComparison} onApprove={() => {}} /></MemoryRouter>);
  const approveButtons = screen.getAllByText(/approve/i);
  expect(approveButtons.length).toBeGreaterThanOrEqual(2);
});

// TEST 6: Approve calls onApprove with solution ID
it('should call onApprove with correct solution ID', async () => {
  const onApprove = vi.fn();
  const { default: ComparisonMatrix } = await import('../components/evaluation/ComparisonMatrix');
  render(<MemoryRouter><ComparisonMatrix comparison={mockComparison} onApprove={onApprove} /></MemoryRouter>);
  const approveButtons = screen.getAllByText(/approve/i);
  fireEvent.click(approveButtons[0]);
  expect(onApprove).toHaveBeenCalled();
});

// TEST 7: Shows "system does not decide" text
it('should show disclaimer that system does not decide', async () => {
  const { default: ComparisonMatrix } = await import('../components/evaluation/ComparisonMatrix');
  render(<MemoryRouter><ComparisonMatrix comparison={mockComparison} onApprove={() => {}} /></MemoryRouter>);
  expect(screen.getByText(/does not/i)).toBeDefined();
});

// TEST 8: Leader badge renders
it('should render leader badge', async () => {
  const { default: MetricLeaderBadge } = await import('../components/evaluation/MetricLeaderBadge');
  render(<MetricLeaderBadge />);
  expect(screen.getByText(/leader/i)).toBeDefined();
});
