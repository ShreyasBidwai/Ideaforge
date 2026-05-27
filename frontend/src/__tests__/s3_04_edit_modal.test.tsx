import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const mockProblem = {
  id: '1', session_id: 's1', title: 'Test Problem', description: 'Test description',
  target_user: 'Test users', core_pain: 'Test pain', market_context: 'Test market',
  severity: 4, feasibility: 3, market_size: 4, uniqueness: 2, overall_rating: 3.38,
  status: 'draft' as const, created_at: '', updated_at: '', industry: 'Healthcare'
};

// TEST 1: Modal renders with pre-populated data
it('should render modal with current problem data', async () => {
  const { default: EditProblemModal } = await import('../components/problems/EditProblemModal');
  render(<MemoryRouter><EditProblemModal problem={mockProblem} isOpen={true} onClose={() => {}} onSave={() => {}} /></MemoryRouter>);
  expect(screen.getByDisplayValue('Test Problem')).toBeDefined();
  expect(screen.getByDisplayValue('Test description')).toBeDefined();
});

// TEST 2: Modal has all 4 rating sliders
it('should render 4 rating sliders', async () => {
  const { default: EditProblemModal } = await import('../components/problems/EditProblemModal');
  render(<MemoryRouter><EditProblemModal problem={mockProblem} isOpen={true} onClose={() => {}} onSave={() => {}} /></MemoryRouter>);
  expect(screen.getByText(/severity/i)).toBeDefined();
  expect(screen.getByText(/feasibility/i)).toBeDefined();
  expect(screen.getByText(/market size/i)).toBeDefined();
  expect(screen.getByText(/uniqueness/i)).toBeDefined();
});

// TEST 3: Cancel button closes modal
it('should call onClose when cancel is clicked', async () => {
  const onClose = vi.fn();
  const { default: EditProblemModal } = await import('../components/problems/EditProblemModal');
  render(<MemoryRouter><EditProblemModal problem={mockProblem} isOpen={true} onClose={onClose} onSave={() => {}} /></MemoryRouter>);
  fireEvent.click(screen.getByText(/cancel/i));
  expect(onClose).toHaveBeenCalled();
});

// TEST 4: Modal base component closes on escape
it('should close on escape key', async () => {
  const onClose = vi.fn();
  const { default: Modal } = await import('../components/ui/Modal');
  render(<Modal isOpen={true} onClose={onClose} title="Test">Content</Modal>);
  fireEvent.keyDown(document, { key: 'Escape' });
  expect(onClose).toHaveBeenCalled();
});

// TEST 5: Slider component renders
it('should render slider with value', async () => {
  const { default: Slider } = await import('../components/ui/Slider');
  render(<Slider min={1} max={5} step={1} value={3} onChange={() => {}} label="Severity" showValue />);
  expect(screen.getByText('Severity')).toBeDefined();
});

// TEST 6: Modal not visible when isOpen is false
it('should not render content when closed', async () => {
  const { default: EditProblemModal } = await import('../components/problems/EditProblemModal');
  render(<MemoryRouter><EditProblemModal problem={mockProblem} isOpen={false} onClose={() => {}} onSave={() => {}} /></MemoryRouter>);
  expect(screen.queryByText('Edit Problem Statement')).toBeNull();
});

// TEST 7: Save button exists
it('should have a save button', async () => {
  const { default: EditProblemModal } = await import('../components/problems/EditProblemModal');
  render(<MemoryRouter><EditProblemModal problem={mockProblem} isOpen={true} onClose={() => {}} onSave={() => {}} /></MemoryRouter>);
  expect(screen.getByText(/save/i)).toBeDefined();
});
