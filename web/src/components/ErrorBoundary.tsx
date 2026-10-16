import { Component, type ReactNode, type ErrorInfo } from "react";
import { RECORDED_DEMO } from "../deployment";
import "../recovery.css";

export default class ErrorBoundary extends Component<
  { children: ReactNode },
  { failed: boolean }
> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("DecisionDebt render failed", error, info.componentStack);
  }

  render() {
    if (!this.state.failed) return this.props.children;
    return (
      <main className="recovery-screen" role="alert">
        <section>
          <p className="recovery-label">DecisionDebt</p>
          <h1>The workspace couldn't open.</h1>
          <p>Retry this page, or watch the recorded demo.</p>
          <div className="recovery-actions">
            <button onClick={() => window.location.reload()}>
              Retry loading
            </button>
            <a href={RECORDED_DEMO}>Watch the recorded demo</a>
          </div>
        </section>
      </main>
    );
  }
}
