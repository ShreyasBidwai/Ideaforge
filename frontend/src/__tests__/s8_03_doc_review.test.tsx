import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';

// TEST 6: Document viewer renders markdown
it('should render markdown content', async () => {
  const { default: DocumentViewer } = await import('../components/project/DocumentViewer');
  render(<DocumentViewer content="# Hello World\n\nThis is a **test**." />);
  expect(screen.getByText('Hello World', { exact: false })).toBeDefined();
});

// TEST 7: Document editor has edit and preview
it('should render editor with save button', async () => {
  const { default: DocumentEditor } = await import('../components/project/DocumentEditor');
  render(<DocumentEditor content="# Test" onSave={() => {}} onApprove={() => {}} onCancel={() => {}} />);
  expect(screen.getByText(/save/i)).toBeDefined();
  expect(screen.getByText(/approve/i)).toBeDefined();
});

// TEST 8: Sprint review shows tasks
it('should render sprint tasks with prompts', async () => {
  const { default: SprintReview } = await import('../components/project/SprintReview');
  const sprints = [{
    id: '1', sprint_number: 1, name: 'Foundation', status: 'pending',
    tasks: [{ id: 't1', task_number: 1, name: 'Backend setup', prompt: 'Create FastAPI project...', status: 'pending' }]
  }];
  render(<SprintReview sprints={sprints as any} onEditPrompt={() => {}} onApproveAndBuild={() => {}} />);
  expect(screen.getByText(/foundation/i)).toBeDefined();
  expect(screen.getByText(/backend setup/i)).toBeDefined();
});
