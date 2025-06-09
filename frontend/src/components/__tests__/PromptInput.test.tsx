import { render, screen, fireEvent } from '@testing-library/react';
import PromptInput from '../PromptInput';

describe('PromptInput', () => {
  const mockOnSend = jest.fn();

  beforeEach(() => {
    mockOnSend.mockClear();
  });

  it('renders with disabled state when disabled prop is true', () => {
    render(<PromptInput onSend={mockOnSend} loading={false} disabled={true} />);
    
    const input = screen.getByTestId('message-input');
    const button = screen.getByTestId('send-button');
    
    expect(input).toBeDisabled();
    expect(button).toBeDisabled();
    expect(input).toHaveAttribute('placeholder', '세션을 선택해주세요');
  });

  it('renders with enabled state when disabled prop is false', () => {
    render(<PromptInput onSend={mockOnSend} loading={false} disabled={false} />);
    
    const input = screen.getByTestId('message-input');
    const button = screen.getByTestId('send-button');
    
    expect(input).not.toBeDisabled();
    expect(button).toBeDisabled(); // 초기에는 메시지가 없으므로 버튼은 비활성화
    expect(input).toHaveAttribute('placeholder', '메시지를 입력하세요...');
  });

  it('enables send button when text is entered', () => {
    render(<PromptInput onSend={mockOnSend} loading={false} disabled={false} />);
    
    const input = screen.getByTestId('message-input');
    const button = screen.getByTestId('send-button');
    
    fireEvent.change(input, { target: { value: '테스트 메시지' } });
    expect(button).not.toBeDisabled();
  });

  it('calls onSend when form is submitted with valid input', () => {
    render(<PromptInput onSend={mockOnSend} loading={false} disabled={false} />);
    
    const input = screen.getByTestId('message-input');
    const form = input.closest('form');
    
    fireEvent.change(input, { target: { value: '테스트 메시지' } });
    fireEvent.submit(form!);
    
    expect(mockOnSend).toHaveBeenCalledWith('테스트 메시지');
    expect(input).toHaveValue(''); // 입력 필드가 초기화되어야 함
  });

  it('does not call onSend when form is submitted with empty input', () => {
    render(<PromptInput onSend={mockOnSend} loading={false} disabled={false} />);
    
    const form = screen.getByTestId('message-input').closest('form');
    fireEvent.submit(form!);
    
    expect(mockOnSend).not.toHaveBeenCalled();
  });

  it('shows loading state correctly', () => {
    render(<PromptInput onSend={mockOnSend} loading={true} disabled={false} />);
    
    const input = screen.getByTestId('message-input');
    const button = screen.getByTestId('send-button');
    
    expect(input).toBeDisabled();
    expect(button).toBeDisabled();
    expect(button).toHaveTextContent('전송 중...');
  });
}); 