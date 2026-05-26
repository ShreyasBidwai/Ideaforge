import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

describe("Auth UI Pages", () => {
  // TEST 1: Login page renders form fields
  it('should render login form with email and password', async () => {
    const { default: Login } = await import('../pages/Login');
    render(<MemoryRouter><Login /></MemoryRouter>);
    expect(screen.getByLabelText(/email/i)).toBeDefined();
    expect(screen.getByLabelText(/password/i)).toBeDefined();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeDefined();
  });

  // TEST 2: Login shows validation errors on empty submit
  it('should show validation errors on empty login submit', async () => {
    const { default: Login } = await import('../pages/Login');
    render(<MemoryRouter><Login /></MemoryRouter>);
    const button = screen.getByRole('button', { name: /sign in/i });
    fireEvent.click(button);
    await waitFor(() => {
      // Should show error messages for required fields
      expect(screen.getAllByText(/required/i).length).toBeGreaterThan(0);
    });
  });

  // TEST 3: Register page renders all fields
  it('should render register form with all fields', async () => {
    const { default: Register } = await import('../pages/Register');
    render(<MemoryRouter><Register /></MemoryRouter>);
    expect(screen.getByLabelText(/full name/i)).toBeDefined();
    expect(screen.getByLabelText(/email/i)).toBeDefined();
    expect(screen.getByLabelText(/^password$/i)).toBeDefined();
    expect(screen.getByLabelText(/confirm password/i)).toBeDefined();
  });

  // TEST 4: Password visibility toggle works
  it('should toggle password visibility', async () => {
    const { default: Login } = await import('../pages/Login');
    render(<MemoryRouter><Login /></MemoryRouter>);
    const passwordInput = screen.getByLabelText(/password/i);
    expect(passwordInput.getAttribute('type')).toBe('password');
    const toggleButton = screen.getByTestId('password-toggle') || screen.getByLabelText(/show password/i);
    fireEvent.click(toggleButton);
    expect(passwordInput.getAttribute('type')).toBe('text');
  });

  // TEST 5: Password strength indicator updates
  it('should show password strength indicator on register', async () => {
    const { default: Register } = await import('../pages/Register');
    render(<MemoryRouter><Register /></MemoryRouter>);
    const passwordInput = screen.getByLabelText(/^password$/i);
    fireEvent.change(passwordInput, { target: { value: 'ab' } });
    await waitFor(() => expect(screen.getByText(/weak/i)).toBeDefined());
    fireEvent.change(passwordInput, { target: { value: 'Abcdef12' } });
    await waitFor(() => expect(screen.getByText(/medium|strong/i)).toBeDefined());
  });

  // TEST 6: Register validates password match
  it('should validate confirm password matches password', async () => {
    const { default: Register } = await import('../pages/Register');
    render(<MemoryRouter><Register /></MemoryRouter>);
    const password = screen.getByLabelText(/^password$/i);
    const confirm = screen.getByLabelText(/confirm password/i);
    fireEvent.change(password, { target: { value: 'StrongPass123!' } });
    fireEvent.change(confirm, { target: { value: 'DifferentPass!' } });
    fireEvent.blur(confirm);
    await waitFor(() => expect(screen.getByText(/match/i)).toBeDefined());
  });

  // TEST 7: Login page has link to register
  it('should have link to register page', async () => {
    const { default: Login } = await import('../pages/Login');
    render(<MemoryRouter><Login /></MemoryRouter>);
    expect(screen.getByText(/don't have an account/i)).toBeDefined();
  });

  // TEST 8: Register page has link to login
  it('should have link to login page', async () => {
    const { default: Register } = await import('../pages/Register');
    render(<MemoryRouter><Register /></MemoryRouter>);
    expect(screen.getByText(/already have an account/i)).toBeDefined();
  });

  // TEST 9: Button component renders variants
  it('should render button with loading state', async () => {
    const { default: Button } = await import('../components/ui/Button');
    render(<Button isLoading>Submit</Button>);
    expect(screen.getByText(/loading|submitting/i) || screen.getByRole('button')).toBeDefined();
  });

  // TEST 10: Input component renders with icon and error
  it('should render input with error message', async () => {
    const { default: Input } = await import('../components/ui/Input');
    render(<Input label="Email" error="Invalid email" />);
    expect(screen.getByText('Invalid email')).toBeDefined();
  });
});
