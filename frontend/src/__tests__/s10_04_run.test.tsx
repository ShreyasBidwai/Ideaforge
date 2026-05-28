import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

// TEST 1: Setup gate renders steps
it('renders setup steps', async () => {
  const { default: SetupGate } = await import('../components/run/SetupGate');
  const steps = [
    { id: '1', step_type: 'api_key', title: 'Stripe key', env_key: 'STRIPE_SECRET_KEY', is_required: true, is_completed: false },
    { id: '2', step_type: 'env_var', title: 'DB URL', env_key: 'DATABASE_URL', is_required: false, is_completed: true },
  ];
  render(<SetupGate steps={steps as any} onReady={() => {}} onSave={() => {}} onMark={() => {}} />);
  expect(screen.getByText(/stripe key/i)).toBeDefined();
});

// TEST 2: Gate shows completion count
it('shows required completion count', async () => {
  const { default: SetupGate } = await import('../components/run/SetupGate');
  const steps = [{ id: '1', step_type: 'api_key', title: 'K', env_key: 'K', is_required: true, is_completed: false }];
  render(<SetupGate steps={steps as any} onReady={() => {}} onSave={() => {}} onMark={() => {}} />);
  expect(screen.getByText(/0 of 1|1 required|of 1/i)).toBeDefined();
});

// TEST 3: RunPanel renders install + start buttons
it('renders run controls', async () => {
  const { default: RunPanel } = await import('../components/run/RunPanel');
  render(<RunPanel ready={true} installed={false} status="stopped" onInstall={()=>{}} onStart={()=>{}} onStop={()=>{}} />);
  expect(screen.getByText(/install/i)).toBeDefined();
  expect(screen.getByText(/start/i)).toBeDefined();
});

// TEST 4: Start disabled until ready
it('disables start when not ready', async () => {
  const { default: RunPanel } = await import('../components/run/RunPanel');
  render(<RunPanel ready={false} installed={false} status="stopped" onInstall={()=>{}} onStart={()=>{}} onStop={()=>{}} />);
  const start = screen.getByText(/start/i).closest('button');
  expect(start?.disabled).toBe(true);
});

// TEST 5: Running shows URLs
it('shows running urls', async () => {
  const { default: RunPanel } = await import('../components/run/RunPanel');
  render(<RunPanel ready={true} installed={true} status="running" backendUrl="http://localhost:8100" frontendUrl="http://localhost:8101" onInstall={()=>{}} onStart={()=>{}} onStop={()=>{}} />);
  expect(screen.getByText(/8100/)).toBeDefined();
});

// TEST 6: Run logs renders backend/frontend tabs
it('renders log tabs', async () => {
  const { default: RunLogs } = await import('../components/run/RunLogs');
  render(<RunLogs projectId="x" backendLogs={["started"]} frontendLogs={[]} />);
  expect(screen.getByText(/backend/i)).toBeDefined();
});

// TEST 7: run store initializes
it('initializes run store', async () => {
  const { useRunStore } = await import('../stores/runStore');
  const s = useRunStore.getState();
  expect(typeof s.install).toBe('function');
  expect(typeof s.start).toBe('function');
  expect(typeof s.stop).toBe('function');
});
