import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import React from 'react';

// TEST 1: Project detail page renders
it('should render project detail page', async () => {
  const { default: ProjectDetail } = await import('../pages/ProjectDetail');
  render(<MemoryRouter initialEntries={['/projects/test']}>
    <Routes><Route path="/projects/:projectId" element={<ProjectDetail />} /></Routes>
  </MemoryRouter>);
});

// TEST 2: Setup checklist renders steps
it('should render setup checklist', async () => {
  const { default: SetupChecklist } = await import('../components/project/SetupChecklist');
  const steps = [
    { label: 'Create PostgreSQL database', command: 'createdb myapp' },
    { label: 'Install dependencies', command: 'pip install -r requirements.txt' },
    { label: 'Run migrations', command: 'alembic upgrade head' },
  ];
  render(<SetupChecklist steps={steps} />);
  expect(screen.getByText(/create postgresql/i)).toBeDefined();
  expect(screen.getByText(/run migrations/i)).toBeDefined();
});

// TEST 3: Setup checklist has copy buttons
it('should have copy buttons for commands', async () => {
  const { default: SetupChecklist } = await import('../components/project/SetupChecklist');
  const steps = [{ label: 'Run server', command: 'uvicorn app.main:app' }];
  render(<SetupChecklist steps={steps} />);
  const copyButtons = screen.getAllByRole('button');
  expect(copyButtons.length).toBeGreaterThan(0);
});

// TEST 4: Tabs exist
it('should show overview documents build tabs', async () => {
  const { useBuildStore } = await import('../stores/buildStore');
  useBuildStore.setState({
    project: {
      id: 'test',
      name: 'Test Project',
      description: 'Test Description',
      status: 'complete',
      tech_stack: ['FastAPI', 'React'],
      industry: 'SaaS',
      maturity_level: 'MVP',
      created_at: new Date().toISOString()
    } as any,
    sprints: [],
    logs: [],
    status: 'complete',
    stats: { completedTasks: 5, totalTasks: 5, testsPassing: 12, eta: '--' }
  });

  const { default: ProjectDetail } = await import('../pages/ProjectDetail');
  render(<MemoryRouter initialEntries={['/projects/test']}>
    <Routes><Route path="/projects/:projectId" element={<ProjectDetail />} /></Routes>
  </MemoryRouter>);
  
  expect(screen.getByText(/overview/i)).toBeDefined();
  expect(screen.getAllByText(/documents/i).length).toBeGreaterThan(0);
});
