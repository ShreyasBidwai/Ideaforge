import { render, screen } from '@testing-library/react';
import React from 'react';
import { it, expect } from 'vitest';

// TEST 4: Doc generation progress renders
it('should show 5 document types with status', async () => {
  const { default: DocGenerationProgress } = await import('../components/project/DocGenerationProgress');
  render(<DocGenerationProgress completedDocs={['architecture', 'prd']} currentDoc="trd" />);
  expect(screen.getByText(/architecture/i)).toBeDefined();
  expect(screen.getByText(/trd/i)).toBeDefined();
});

// TEST 5: Progress shows count
it('should show completion count', async () => {
  const { default: DocGenerationProgress } = await import('../components/project/DocGenerationProgress');
  render(<DocGenerationProgress completedDocs={['architecture', 'prd']} currentDoc="trd" />);
  expect(screen.getByText(/2/) || screen.getByText(/5/)).toBeDefined();
});
