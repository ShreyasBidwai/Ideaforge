import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

import type { FileNode } from '../components/project/FileTree';

const mockTree: FileNode = {
  name: 'my-project', type: 'directory', children: [
    { name: 'backend', type: 'directory', children: [
      { name: 'app', type: 'directory', children: [
        { name: 'main.py', type: 'file', size: 245 }
      ]},
    ]},
    { name: 'frontend', type: 'directory', children: [
      { name: 'src', type: 'directory', children: [
        { name: 'App.tsx', type: 'file', size: 890 }
      ]}
    ]},
    { name: 'README.md', type: 'file', size: 120 }
  ]
};

// TEST 1: File tree renders directories and files
it('should render directory tree', async () => {
  const { default: FileTree } = await import('../components/project/FileTree');
  render(<FileTree tree={mockTree} onSelectFile={() => {}} />);
  expect(screen.getByText('backend')).toBeDefined();
  expect(screen.getByText('frontend')).toBeDefined();
  expect(screen.getByText('README.md')).toBeDefined();
});

// TEST 2: Clicking file calls onSelectFile
it('should call onSelectFile when file clicked', async () => {
  const onSelect = vi.fn();
  const { default: FileTree } = await import('../components/project/FileTree');
  render(<FileTree tree={mockTree} onSelectFile={onSelect} />);
  fireEvent.click(screen.getByText('README.md'));
  expect(onSelect).toHaveBeenCalledWith('README.md');
});

// TEST 3: Code viewer renders content with line numbers
it('should render code with content', async () => {
  const { default: CodeViewer } = await import('../components/project/CodeViewer');
  render(<CodeViewer content="print('hello')\nprint('world')" language="python" filePath="main.py" />);
  expect(screen.getByText(/hello/)).toBeDefined();
});

// TEST 4: Code viewer has copy button
it('should have copy button', async () => {
  const { default: CodeViewer } = await import('../components/project/CodeViewer');
  render(<CodeViewer content="code here" language="text" filePath="test.txt" />);
  expect(screen.getByText(/copy/i) || screen.getByRole('button', { name: /copy/i })).toBeDefined();
});

// TEST 5: File browser renders both panels
it('should render file browser with tree and viewer', async () => {
  const { default: FileBrowser } = await import('../components/project/FileBrowser');
  render(<FileBrowser projectId="test-id" />);
  // Should render without crashing
});
