import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import ErrorBoundary from '../components/ErrorBoundary';

jest.mock('next-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) =>
      ({
        'errorBoundary.title': 'Localized Error Title',
        'errorBoundary.message': 'Localized Error Message',
        'errorBoundary.details': 'Localized Error Details',
        'errorBoundary.retry': 'Localized Retry',
      }[key] ?? key),
  }),
}));

const ThrowOnRender = ({ message = 'boom' }: { message?: string }) => {
  throw new Error(message);
};

describe('ErrorBoundary', () => {
  let consoleErrorSpy: jest.SpyInstance;

  beforeEach(() => {
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => undefined);
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  it('renders translated fallback content on render error', () => {
    render(
      <ErrorBoundary>
        <ThrowOnRender message="render failed" />
      </ErrorBoundary>
    );

    expect(screen.getByRole('heading', { level: 2, name: 'Localized Error Title' })).toBeInTheDocument();
    expect(screen.getByText('Localized Error Message')).toBeInTheDocument();
    expect(screen.getByText('Localized Error Details')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Localized Retry' })).toBeInTheDocument();
    expect(screen.getByText('render failed')).toBeInTheDocument();
  });

  it('retries rendering and recovers when child succeeds on next render', () => {
    const ControlledRecovery = () => {
      const [shouldThrow, setShouldThrow] = React.useState(true);

      return (
        <>
          <button type="button" onClick={() => setShouldThrow(false)}>
            Stabilize Child
          </button>
          <ErrorBoundary>{shouldThrow ? <ThrowOnRender message="first render failed" /> : <div>Recovered Content</div>}</ErrorBoundary>
        </>
      );
    };

    render(<ControlledRecovery />);

    fireEvent.click(screen.getByRole('button', { name: 'Stabilize Child' }));
    fireEvent.click(screen.getByRole('button', { name: 'Localized Retry' }));

    expect(screen.getByText('Recovered Content')).toBeInTheDocument();
  });

  it('renders custom fallback when provided', () => {
    render(
      <ErrorBoundary fallback={<div>Custom Fallback</div>}>
        <ThrowOnRender />
      </ErrorBoundary>
    );

    expect(screen.getByText('Custom Fallback')).toBeInTheDocument();
    expect(screen.queryByText('Localized Error Title')).not.toBeInTheDocument();
  });
});
