import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

const mockSolutions = [
  { id: '1', title: 'Solution A', description: 'Desc A', mechanism: 'Mech A',
    tech_stack: ['React'], target_user: 'Users', revenue_model: 'SaaS',
    is_unconventional: false, status: 'candidate' },
  { id: '2', title: 'Solution B', description: 'Desc B', mechanism: 'Mech B',
    tech_stack: ['Vue'], target_user: 'Admins', revenue_model: 'Marketplace',
    is_unconventional: true, status: 'candidate' },
];

// TEST 1: Comparison table renders all solutions
it('should render a column for each solution', async () => {
  const { default: SolutionComparison } = await import('../components/solutions/SolutionComparison');
  render(<SolutionComparison solutions={mockSolutions as any} />);
  expect(screen.getByText('Solution A')).toBeDefined();
  expect(screen.getByText('Solution B')).toBeDefined();
});

// TEST 2: Comparison shows tech stacks
it('should show tech stacks in comparison', async () => {
  const { default: SolutionComparison } = await import('../components/solutions/SolutionComparison');
  render(<SolutionComparison solutions={mockSolutions as any} />);
  expect(screen.getByText('React')).toBeDefined();
  expect(screen.getByText('Vue')).toBeDefined();
});

// TEST 3: View toggle renders both options
it('should render cards and compare toggle', async () => {
  const { default: ViewToggle } = await import('../components/solutions/ViewToggle');
  render(<ViewToggle view="cards" onChange={() => {}} />);
  expect(screen.getByText(/cards/i)).toBeDefined();
  expect(screen.getByText(/compare/i)).toBeDefined();
});

// TEST 4: Toggle calls onChange
it('should call onChange on toggle', async () => {
  const onChange = (await import('vitest')).vi.fn();
  const { default: ViewToggle } = await import('../components/solutions/ViewToggle');
  render(<ViewToggle view="cards" onChange={onChange} />);
  fireEvent.click(screen.getByText(/compare/i));
  expect(onChange).toHaveBeenCalledWith('compare');
});

// TEST 5: Unconventional solution marked in comparison
it('should mark unconventional solution', async () => {
  const { default: SolutionComparison } = await import('../components/solutions/SolutionComparison');
  render(<SolutionComparison solutions={mockSolutions as any} />);
  expect(screen.getByText(/unconventional/i)).toBeDefined();
});
