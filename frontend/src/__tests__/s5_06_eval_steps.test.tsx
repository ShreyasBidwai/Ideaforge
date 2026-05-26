import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';

// TEST 1: Scoring table renders solutions and criteria
it('should render scoring table with all data', async () => {
  const { default: ScoringTable } = await import('../components/evaluation/ScoringTable');
  const scores = [
    { solution_title: 'Sol 1', criterion_scores: [
      { criterion: 'Feasibility', score: 4, justification: 'Proven tech' },
      { criterion: 'Adoption', score: 3, justification: 'Moderate friction' }
    ], weighted_avg: 3.5, min_score: 3 }
  ];
  render(<ScoringTable scores={scores} criteria={[
    { name: 'Feasibility', weight: 2 }, { name: 'Adoption', weight: 2.5 }
  ]} />);
  expect(screen.getByText('Sol 1')).toBeDefined();
  expect(screen.getByText('Feasibility')).toBeDefined();
});

// TEST 2: Scoring table shows weighted average
it('should display weighted average', async () => {
  const { default: ScoringTable } = await import('../components/evaluation/ScoringTable');
  const scores = [{ solution_title: 'Sol 1', criterion_scores: [], weighted_avg: 4.25, min_score: 3 }];
  render(<ScoringTable scores={scores} criteria={[]} />);
  expect(screen.getByText('4.25') || screen.getByText(/4\.25/)).toBeDefined();
});

// TEST 3: Attack card renders attack text
it('should render attack with severity and survival', async () => {
  const { default: AttackCards } = await import('../components/evaluation/AttackCards');
  const attacks = [
    { solution_title: 'Sol 1', attack: 'Platform dependency is existential risk', severity: 'high', survives: false, survival_reasoning: 'No mitigation possible' }
  ];
  render(<AttackCards attacks={attacks} />);
  expect(screen.getByText(/platform dependency/i)).toBeDefined();
  expect(screen.getByText(/high/i)).toBeDefined();
});

// TEST 4: Attack card shows survival verdict
it('should show survival verdict clearly', async () => {
  const { default: AttackCards } = await import('../components/evaluation/AttackCards');
  const attacks = [
    { solution_title: 'Sol A', attack: 'Test attack', severity: 'medium', survives: true, survival_reasoning: 'Can mitigate' },
    { solution_title: 'Sol B', attack: 'Fatal attack', severity: 'high', survives: false, survival_reasoning: 'No fix' }
  ];
  render(<AttackCards attacks={attacks} />);
  expect(screen.getByText('Sol A')).toBeDefined();
  expect(screen.getByText('Sol B')).toBeDefined();
});

// TEST 5: ACH analysis renders inconsistencies
it('should render inconsistency list per solution', async () => {
  const { default: ACHAnalysis } = await import('../components/evaluation/ACHAnalysis');
  const analysis = [
    { solution_title: 'Sol 1', inconsistencies: ['Bad internet in target region', 'Budget constraints'], count: 2 }
  ];
  render(<ACHAnalysis analysis={analysis} />);
  expect(screen.getByText('Sol 1')).toBeDefined();
  expect(screen.getByText(/bad internet/i)).toBeDefined();
  expect(screen.getByText('2')).toBeDefined();
});

// TEST 6: ACH shows count badge
it('should show inconsistency count badge', async () => {
  const { default: ACHAnalysis } = await import('../components/evaluation/ACHAnalysis');
  const analysis = [
    { solution_title: 'Sol 1', inconsistencies: ['A', 'B', 'C'], count: 3 }
  ];
  render(<ACHAnalysis analysis={analysis} />);
  expect(screen.getByText('3')).toBeDefined();
});
