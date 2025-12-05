import '@testing-library/jest-dom'
import { render, screen } from '@testing-library/react'
import Page from '../app/page'

// Mock the ChatInterface component since we are only testing the Page component
jest.mock('../components/ChatInterface', () => {
  return function DummyChatInterface() {
    return <div data-testid="chat-interface">Chat Interface Mock</div>;
  };
});
 
describe('Page', () => {
  it('renders the main heading', () => {
    render(<Page />)
 
    const heading = screen.getByRole('heading', { level: 1, name: 'SoftSkill AI Coach' })
 
    expect(heading).toBeInTheDocument()
  })
})
