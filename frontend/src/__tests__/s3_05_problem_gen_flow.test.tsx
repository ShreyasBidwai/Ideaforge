import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

// TEST 1: Generate Problem Statements button exists on discovery page
it('should show generate button after pain points', async () => {
  const { useDiscoveryStore } = await import('../stores/discoveryStore');
  useDiscoveryStore.setState({
    currentSession: { id: '1', industry: 'Healthcare', location: 'India', status: 'problem_generation', pain_points: [
      { name: 'Test', description: 'Test', severity: 5, affected_stakeholders: ['Users'], evidence: 'Data' }
    ] } as any,
    painPoints: [{ name: 'Test', description: 'Test', severity: 5, affected_stakeholders: ['Users'], evidence: 'Data' }],
    isDiscovering: false,
  });
  const { default: Discovery } = await import('../pages/Discovery');
  render(<MemoryRouter><Discovery /></MemoryRouter>);
  expect(screen.getByText(/generate problem statements/i)).toBeDefined();
});

// TEST 2: Discovery store has problem generation state
it('should have problem generation state in store', async () => {
  const { useDiscoveryStore } = await import('../stores/discoveryStore');
  const state = useDiscoveryStore.getState();
  expect('generatedProblems' in state).toBe(true);
  expect('isGeneratingProblems' in state).toBe(true);
  expect(typeof state.generateProblems).toBe('function');
});

// TEST 3: Problem generation progress component renders
it('should render generation progress steps', async () => {
  const { default: ProblemGenerationProgress } = await import('../components/discovery/ProblemGenerationProgress');
  render(<ProblemGenerationProgress currentStep="generating" />);
  expect(screen.getByText(/generating/i) || screen.getByText(/problem statements/i)).toBeDefined();
});

// TEST 4: Generated problems display after generation
it('should display generated problems', async () => {
  const { useDiscoveryStore } = await import('../stores/discoveryStore');
  useDiscoveryStore.setState({
    currentSession: { id: '1', industry: 'Healthcare', location: 'India', status: 'solution_generation' } as any,
    painPoints: [{ name: 'Test', description: 'Test', severity: 5, affected_stakeholders: ['Users'], evidence: 'Data' }],
    generatedProblems: [{
      id: 'p1', title: 'Digital Queue System', description: 'Build a queue system',
      severity: 4, feasibility: 5, market_size: 4, uniqueness: 3, overall_rating: 4.08,
      status: 'draft'
    }] as any,
    isDiscovering: false,
    isGeneratingProblems: false,
  });
  const { default: Discovery } = await import('../pages/Discovery');
  render(<MemoryRouter><Discovery /></MemoryRouter>);
  expect(screen.getByText('Digital Queue System')).toBeDefined();
});

// TEST 5: Select & Continue button exists on generated problems
it('should have select and continue button on problem cards', async () => {
  const { useDiscoveryStore } = await import('../stores/discoveryStore');
  useDiscoveryStore.setState({
    currentSession: { id: '1', industry: 'Healthcare', location: 'India', status: 'solution_generation' } as any,
    generatedProblems: [{
      id: 'p1', title: 'Test Problem', description: 'Test', severity: 4, feasibility: 4,
      market_size: 4, uniqueness: 3, overall_rating: 3.85, status: 'draft'
    }] as any,
    painPoints: [{ name: 'Pain', description: 'Desc', severity: 5, affected_stakeholders: ['Users'], evidence: 'Data' }],
    isDiscovering: false, isGeneratingProblems: false,
  });
  const { default: Discovery } = await import('../pages/Discovery');
  render(<MemoryRouter><Discovery /></MemoryRouter>);
  expect(screen.getByText(/select/i) || screen.getByText(/continue/i)).toBeDefined();
});
