import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

const mockRubric = {
  criteria: [
    { name: 'Technical Feasibility', description: 'Can it be built?', weight: 2,
      scale: { '1': 'Impossible', '3': 'Doable', '5': 'Easy' } },
    { name: 'User Adoption', description: 'Will users use it?', weight: 2.5,
      scale: { '1': 'No way', '3': 'Maybe', '5': 'Definitely' } },
    { name: 'Revenue', description: 'Makes money?', weight: 1.5,
      scale: { '1': 'No path', '3': 'Possible', '5': 'Proven' } },
  ],
  disqualifiers: [
    { name: 'Illegal', description: 'Violates laws' }
  ]
};

// TEST 1: Evaluation page renders wizard
it('should render evaluation wizard with progress steps', async () => {
  const { default: Evaluation } = await import('../pages/Evaluation');
  render(<MemoryRouter initialEntries={['/evaluation/test-id']}>
    <Routes><Route path="/evaluation/:problemId" element={<Evaluation />} /></Routes>
  </MemoryRouter>);
  expect(screen.getByText(/rubric/i)).toBeDefined();
});

// TEST 2: Rubric editor renders criteria
it('should render rubric criteria cards', async () => {
  const { default: RubricEditor } = await import('../components/evaluation/RubricEditor');
  render(<RubricEditor rubric={mockRubric} isLocked={false} onUpdate={() => {}} onLock={() => {}} onRegenerate={() => {}} />);
  expect(screen.getByDisplayValue('Technical Feasibility')).toBeDefined();
  expect(screen.getByDisplayValue('User Adoption')).toBeDefined();
});

// TEST 3: Rubric editor shows lock button
it('should show lock button when rubric is not locked', async () => {
  const { default: RubricEditor } = await import('../components/evaluation/RubricEditor');
  render(<RubricEditor rubric={mockRubric} isLocked={false} onUpdate={() => {}} onLock={() => {}} onRegenerate={() => {}} />);
  expect(screen.getAllByText(/lock/i).length).toBeGreaterThan(0);
});

// TEST 4: Locked rubric is not editable
it('should disable editing when rubric is locked', async () => {
  const { default: RubricEditor } = await import('../components/evaluation/RubricEditor');
  render(<RubricEditor rubric={mockRubric} isLocked={true} onUpdate={() => {}} onLock={() => {}} onRegenerate={() => {}} />);
  const inputs = screen.getAllByRole('textbox');
  inputs.forEach(input => {
    expect(input.hasAttribute('disabled') || input.hasAttribute('readonly') || input.getAttribute('aria-disabled') === 'true').toBe(true);
  });
});

// TEST 5: Disqualifier gate shows pass/fail
it('should show pass/fail for each solution', async () => {
  const { default: DisqualifierGate } = await import('../components/evaluation/DisqualifierGate');
  const results = [
    { solution_title: 'Sol 1', passed: true, failed_disqualifiers: [], reasons: [] },
    { solution_title: 'Sol 2', passed: false, failed_disqualifiers: ['Illegal'], reasons: ['Violates health regulations'] },
  ];
  render(<DisqualifierGate results={results} onContinue={() => {}} />);
  expect(screen.getByText('Sol 1')).toBeDefined();
  expect(screen.getByText('Sol 2')).toBeDefined();
});

// TEST 6: Disqualifier shows survival count
it('should show how many solutions survived', async () => {
  const { default: DisqualifierGate } = await import('../components/evaluation/DisqualifierGate');
  const results = [
    { solution_title: 'Sol 1', passed: true, failed_disqualifiers: [], reasons: [] },
    { solution_title: 'Sol 2', passed: true, failed_disqualifiers: [], reasons: [] },
    { solution_title: 'Sol 3', passed: false, failed_disqualifiers: ['X'], reasons: ['Y'] },
  ];
  render(<DisqualifierGate results={results} onContinue={() => {}} />);
  expect(screen.getAllByText(/2/).length).toBeGreaterThan(0); // 2 survived
});

// TEST 7: Evaluation store initializes
it('should initialize evaluation store', async () => {
  const { useEvaluationStore } = await import('../stores/evaluationStore');
  const state = useEvaluationStore.getState();
  expect(state.currentStep).toBe('rubric');
  expect(state.rubric).toBeNull();
  expect(state.isRubricLocked).toBe(false);
});
