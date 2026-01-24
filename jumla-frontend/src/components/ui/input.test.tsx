//src/components/ui/Input.test.tsx

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Input from './Input';

describe('Input', () => {
  it('renders with label', () => {
    render(<Input label="Email" />);
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
  });

  it('shows error message when error prop is provided', () => {
    render(<Input label="Email" error="Invalid email" />);
    expect(screen.getByText(/invalid email/i)).toBeInTheDocument();
  });

  it('shows helper text when provided', () => {
    render(<Input label="Email" helperText="We'll never share your email" />);
    expect(screen.getByText(/never share/i)).toBeInTheDocument();
  });

  it('marks field as required with asterisk', () => {
    render(<Input label="Email" required />);
    expect(screen.getByText('*')).toBeInTheDocument();
  });

  it('allows user to type', async () => {
    const user = userEvent.setup();
    render(<Input label="Email" />);
    
    const input = screen.getByLabelText(/email/i);
    await user.type(input, 'test@example.com');
    
    expect(input).toHaveValue('test@example.com');
  });
});