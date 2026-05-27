import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

// TEST 1: Shows tech stack tags in view mode
it('should render tech tags in view mode', async () => {
  const { default: TechStackEditor } = await import('../components/solutions/TechStackEditor');
  render(<TechStackEditor techStack={['React', 'FastAPI', 'PostgreSQL']} onSave={() => {}} />);
  expect(screen.getByText('React')).toBeDefined();
  expect(screen.getByText('FastAPI')).toBeDefined();
  expect(screen.getByText('PostgreSQL')).toBeDefined();
});

// TEST 2: Edit button toggles edit mode
it('should toggle edit mode', async () => {
  const { default: TechStackEditor } = await import('../components/solutions/TechStackEditor');
  render(<TechStackEditor techStack={['React']} onSave={() => {}} />);
  const editBtn = screen.getByRole('button', { name: /edit/i }) || screen.getByTestId('edit-tech-stack');
  fireEvent.click(editBtn);
  expect(screen.getByText(/save/i) || screen.getByText(/cancel/i)).toBeDefined();
});

// TEST 3: Cancel reverts changes
it('should revert on cancel', async () => {
  const { default: TechStackEditor } = await import('../components/solutions/TechStackEditor');
  render(<TechStackEditor techStack={['React']} onSave={() => {}} />);
  const editBtn = screen.getByRole('button', { name: /edit/i }) || screen.getByTestId('edit-tech-stack');
  fireEvent.click(editBtn);
  fireEvent.click(screen.getByText(/cancel/i));
  // Should be back in view mode
  expect(screen.queryByText(/save/i)).toBeNull();
});
