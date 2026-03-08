import React, { Component, ErrorInfo, ReactNode } from 'react';
import { useTranslation } from 'next-i18next';

/**
 * ErrorBoundary — catches React rendering errors and displays a user-friendly fallback.
 *
 * Owner: Frontend-Coder (per DEVELOPMENT_PLAN.md Task 2.1.5)
 * Reference: FC Error Handling patterns
 */

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryCopy {
  title: string;
  message: string;
  details: string;
  retry: string;
}

interface ErrorBoundaryInnerProps extends ErrorBoundaryProps {
  copy: ErrorBoundaryCopy;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundaryInner extends Component<ErrorBoundaryInnerProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryInnerProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('[ErrorBoundary]', error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div className="flex flex-col items-center justify-center p-8 text-center" role="alert">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
            <h2 className="text-lg font-semibold text-red-800 mb-2">{this.props.copy.title}</h2>
            <p className="text-sm text-red-600 mb-4">
              {this.props.copy.message}
            </p>
            {this.state.error && (
              <details className="text-xs text-gray-500 mb-4">
                <summary className="cursor-pointer">{this.props.copy.details}</summary>
                <pre className="mt-2 text-left bg-gray-100 p-2 rounded overflow-auto max-h-32">
                  {this.state.error.message}
                </pre>
              </details>
            )}
            <button
              onClick={this.handleRetry}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
            >
              {this.props.copy.retry}
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function ErrorBoundary(props: ErrorBoundaryProps) {
  const { t } = useTranslation('common');

  return (
    <ErrorBoundaryInner
      {...props}
      copy={{
        title: t('errorBoundary.title'),
        message: t('errorBoundary.message'),
        details: t('errorBoundary.details'),
        retry: t('errorBoundary.retry'),
      }}
    />
  );
}
