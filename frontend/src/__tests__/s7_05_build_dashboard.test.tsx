import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import React from 'react';

// TEST 1: Build dashboard renders
it('should render build dashboard', async () => {
  const { default: BuildDashboard } = await import('../pages/BuildDashboard');
  render(<MemoryRouter initialEntries={['/projects/test/build']}>
    <Routes><Route path="/projects/:projectId/build" element={<BuildDashboard />} /></Routes>
  </MemoryRouter>);
});

// TEST 2: Stats component renders 4 cards
it('should render 4 stat cards', async () => {
  const { default: BuildStats } = await import('../components/build/BuildStats');
  render(<BuildStats stats={{ completedTasks: 12, totalTasks: 43, testsPassing: 142, eta: '~6h' }} />);
  expect(screen.getByText('12')).toBeDefined();
  expect(screen.getByText('142')).toBeDefined();
});

// TEST 3: Sprint accordion renders sprints
it('should render sprint list', async () => {
  const { default: SprintAccordion } = await import('../components/build/SprintAccordion');
  const sprints = [
    { id: '1', sprint_number: 1, name: 'Foundation', status: 'completed', tasks: [] },
    { id: '2', sprint_number: 2, name: 'Core Features', status: 'in_progress', tasks: [] },
  ];
  render(<SprintAccordion sprints={sprints as any} />);
  expect(screen.getByText(/foundation/i)).toBeDefined();
  expect(screen.getByText(/core features/i)).toBeDefined();
});

// TEST 4: Build log renders entries
it('should render log entries', async () => {
  const { default: BuildLog } = await import('../components/build/BuildLog');
  const logs = [
    { id: '1', timestamp: '2026-05-27T14:32:00Z', level: 'info', source: 'S3-04', message: 'Creating files...' },
    { id: '2', timestamp: '2026-05-27T14:32:05Z', level: 'success', source: 'S3-04', message: '7/7 tests passed' },
  ];
  render(<BuildLog logs={logs as any} />);
  expect(screen.getByText(/creating files/i)).toBeDefined();
  expect(screen.getByText(/7\/7 tests passed/i)).toBeDefined();
});

// TEST 5: Rate limit gauge renders
it('should render rate limit indicator', async () => {
  const { default: RateLimitGauge } = await import('../components/build/RateLimitGauge');
  render(<RateLimitGauge info={{ isLimited: false, resumeAt: null, usage: 23, capacity: 30 }} />);
  expect(screen.getByText(/23/)).toBeDefined();
});

// TEST 6: Rate limit shows paused state
it('should show paused state when rate limited', async () => {
  const { default: RateLimitGauge } = await import('../components/build/RateLimitGauge');
  render(<RateLimitGauge info={{ isLimited: true, resumeAt: '7:00 PM', usage: 30, capacity: 30 }} />);
  expect(screen.getByText(/paused|resuming|7:00/i)).toBeDefined();
});

// TEST 7: Build store initializes
it('should initialize build store', async () => {
  const { useBuildStore } = await import('../stores/buildStore');
  const state = useBuildStore.getState();
  expect(state.status).toBeDefined();
  expect(typeof state.startBuild).toBe('function');
  expect(typeof state.pauseBuild).toBe('function');
});

// TEST 8: Action buttons render
it('should render pause and cancel buttons', async () => {
  const { default: BuildActions } = await import('../components/build/BuildActions');
  render(<BuildActions status="building" onPause={() => {}} onCancel={() => {}} />);
  expect(screen.getByText(/pause/i)).toBeDefined();
  expect(screen.getByText(/cancel/i)).toBeDefined();
});
