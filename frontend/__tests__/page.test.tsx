import '@testing-library/jest-dom'
import { render } from '@testing-library/react'
import Home from '../app/page'
import { redirect } from 'next/navigation'

// Mock next/navigation
jest.mock('next/navigation', () => ({
  redirect: jest.fn(),
}));

describe('Page', () => {
  it('redirects to /login', () => {
    // Render the Home component (which calls redirect)
    try {
        render(<Home />);
    } catch {
        // redirect() throws an error in Next.js, so we might catch it here if not fully mocked, 
        // but with jest.fn() it should just be called.
    }
 
    expect(redirect).toHaveBeenCalledWith('/login');
  });
})
