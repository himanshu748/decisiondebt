import React from "react";
import ReactDOM from "react-dom/client";
import { MotionConfig } from "motion/react";
import App from "./App";
import Landing from "./Landing";
import ErrorBoundary from "./components/ErrorBoundary";
import "./style.css";
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <MotionConfig reducedMotion="user">
        {window.location.pathname.startsWith("/studio") ? <App /> : <Landing />}
      </MotionConfig>
    </ErrorBoundary>
  </React.StrictMode>,
);
