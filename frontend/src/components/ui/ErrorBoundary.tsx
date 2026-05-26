import React, { Component, ErrorInfo, ReactNode } from "react";
import { AlertOctagon } from "lucide-react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-[400px] flex items-center justify-center p-6 w-full text-white">
          <div className="max-w-md w-full bg-slate-800/50 backdrop-blur-md border border-white/5 p-8 rounded-2xl text-center space-y-6 shadow-2xl">
            <div className="mx-auto w-16 h-16 bg-rose-500/10 rounded-2xl flex items-center justify-center border border-rose-500/20 text-rose-500">
              <AlertOctagon size={32} />
            </div>
            
            <div className="space-y-2">
              <h2 className="text-xl font-bold">Something went wrong</h2>
              <p className="text-sm text-slate-400 leading-relaxed">
                An unexpected rendering error occurred. Please try again or return to the dashboard.
              </p>
              {this.state.error && (
                <pre className="text-left bg-slate-950/60 p-3 rounded-lg text-xs font-mono text-rose-300 overflow-x-auto max-h-32 mt-2">
                  {this.state.error.message}
                </pre>
              )}
            </div>

            <div className="flex flex-col sm:flex-row gap-3 items-center justify-center">
              <button
                onClick={this.handleReset}
                className="w-full sm:w-auto px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-blue-600/20 transition-all"
              >
                Try Again
              </button>
              <a
                href="/"
                className="w-full sm:w-auto px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold border border-white/5 text-center transition-all"
              >
                Go to Dashboard
              </a>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
