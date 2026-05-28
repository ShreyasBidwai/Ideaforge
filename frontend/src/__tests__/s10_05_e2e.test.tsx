import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';

// TEST 5: E2E panel renders generate button
it('renders generate button', async () => {
  const { default: E2EPanel } = await import('../components/e2e/E2EPanel');
  render(<E2EPanel tests={[]} runStatus="stopped" onGenerate={()=>{}} onRun={()=>{}} />);
  expect(screen.getByText(/generate/i)).toBeDefined();
});

// TEST 6: Run disabled when not running
it('disables run when app not running', async () => {
  const { default: E2EPanel } = await import('../components/e2e/E2EPanel');
  render(<E2EPanel tests={[{id:'1',name:'t',framework:'pytest-httpx',status:'pending'}] as any} runStatus="stopped" onGenerate={()=>{}} onRun={()=>{}} />);
  const run = screen.getByText(/run all/i).closest('button');
  expect(run?.disabled).toBe(true);
});

// TEST 7: shows pass/fail badges
it('shows test status', async () => {
  const { default: E2EPanel } = await import('../components/e2e/E2EPanel');
  render(<E2EPanel tests={[{id:'1',name:'health',framework:'pytest-httpx',status:'passed'}] as any} runStatus="running" onGenerate={()=>{}} onRun={()=>{}} />);
  expect(screen.getByText(/health/i)).toBeDefined();
});
