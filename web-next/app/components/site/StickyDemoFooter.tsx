"use client";

import { useDemoMode } from "../../context/DemoModeContext";
import styles from "./StickyDemoFooter.module.css";

function PythonIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M11.91 2C6.98 2 7.3 4.14 7.3 4.14L7.31 6.36H12.02V7.08H5.24C5.24 7.08 2 6.72 2 11.87C2 17.02 4.83 16.79 4.83 16.79H6.51V14.41C6.51 14.41 6.42 11.56 9.32 11.56H14.11C14.11 11.56 16.85 11.65 16.85 8.96V4.28C16.85 4.28 17.26 2 11.91 2ZM9.12 3.48C9.64 3.48 10.06 3.9 10.06 4.42C10.06 4.94 9.64 5.36 9.12 5.36C8.6 5.36 8.18 4.94 8.18 4.42C8.18 3.9 8.6 3.48 9.12 3.48Z" fill="#387EB8" />
      <path d="M12.09 22C17.02 22 16.7 19.86 16.7 19.86L16.69 17.64H11.98V16.92H18.76C18.76 16.92 22 17.28 22 12.13C22 6.98 19.17 7.21 19.17 7.21H17.49V9.59C17.49 9.59 17.58 12.44 14.68 12.44H9.89C9.89 12.44 7.15 12.35 7.15 15.04V19.72C7.15 19.72 6.74 22 12.09 22ZM14.88 20.52C14.36 20.52 13.94 20.1 13.94 19.58C13.94 19.06 14.36 18.64 14.88 18.64C15.4 18.64 15.82 19.06 15.82 19.58C15.82 20.1 15.4 20.52 14.88 20.52Z" fill="#FFE052" />
    </svg>
  );
}

function FastApiIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 2L2 7V17L12 22L22 17V7L12 2Z" fill="#059669" />
      <path d="M11 6L6 14H12L11 18L17 10H11L11 6Z" fill="#FFFFFF" />
    </svg>
  );
}

function GoogleCloudIcon() {
  return (
    <svg width="16" height="13" viewBox="0 0 193 156" fill="none" aria-hidden="true">
      <path fillRule="evenodd" clipRule="evenodd" d="M152.6 62.4C149.2 27.2 119.3 0 83.2 0 54.4 0 29.5 17.4 18.7 42.6 8.2 46.1 0 56.1 0 68c0 14.9 12.1 27 27 27h124.6c22.6 0 41-18.4 41-41 0-21.5-16.7-39.2-37.8-40.8l-2.2-.8z" fill="#4285F4" />
      <path d="M83.2 0C54.4 0 29.5 17.4 18.7 42.6c3.2-.8 6.6-1.3 10.1-1.3 20.1 0 37.3 12.5 44.2 30.1 7.2-4.9 16-7.8 25.5-7.8 21.6 0 39.5 15.8 42.9 36.6 3.6.8 6.9 2.2 9.9 4 1.1-2.9 1.7-6 1.7-9.2C153 42.3 121.7 0 83.2 0z" fill="#EA4335" />
      <path d="M151.6 95H27C12.1 95 0 82.9 0 68c0-8.9 4.3-16.8 11-21.7C9.3 47.9 8.2 49.9 8.2 52c0 14.9 12.1 27 27 27h116.4c17.5 0 32.3-11 38-26.6-4.6 24.8-26.2 42.6-38 42.6z" fill="#34A853" />
      <path d="M151.6 95h-23.7c17.5 0 32.3-11 38-26.6 4.3 8.3 4.7 18.2.7 26.6z" fill="#FBBC05" />
    </svg>
  );
}

function VertexAiIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <defs>
        <linearGradient id="vertexGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#4285F4" />
          <stop offset="50%" stopColor="#9B72CF" />
          <stop offset="100%" stopColor="#D96570" />
        </linearGradient>
      </defs>
      <path d="M12 2C12 7.52 7.52 12 2 12C7.52 12 12 16.48 12 22C12 16.48 16.48 12 22 12C16.48 12 12 7.52 12 2Z" fill="url(#vertexGrad)" />
    </svg>
  );
}

function WatsonxIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <defs>
        <linearGradient id="watsonxGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#0f62fe" />
          <stop offset="100%" stopColor="#8a3ffc" />
        </linearGradient>
      </defs>
      <circle cx="12" cy="12" r="9" stroke="url(#watsonxGrad)" strokeWidth="2" strokeDasharray="3 2" />
      <circle cx="12" cy="12" r="4.5" fill="url(#watsonxGrad)" />
    </svg>
  );
}

function IbmBobIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect width="24" height="24" rx="6" fill="#0f62fe" />
      <path d="M6 7H14C15.66 7 17 8.34 17 10C17 10.9 16.6 11.7 16 12.2C16.8 12.7 17.3 13.6 17.3 14.6C17.3 16.48 15.78 18 13.9 18H6V7ZM9 9.5V11.3H13.5C14.1 11.3 14.6 10.8 14.6 10.2C14.6 9.6 14.1 9.1 13.5 9.1H9V9.5ZM9 13.3V15.7H14C14.7 15.7 15.2 15.2 15.2 14.5C15.2 13.8 14.7 13.3 14 13.3H9Z" fill="#FFFFFF" />
    </svg>
  );
}

function GitHubActionsIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 2A10 10 0 0 0 8.84 21.49C9.34 21.58 9.52 21.27 9.52 21C9.52 20.77 9.51 20 9.51 19.16C6.73 19.76 6.14 17.82 6.14 17.82C5.68 16.66 5.03 16.35 5.03 16.35C4.12 15.73 5.1 15.74 5.1 15.74C6.1 15.81 6.63 16.77 6.63 16.77C7.53 18.31 8.98 17.86 9.55 17.61C9.64 16.96 9.9 16.51 10.19 16.26C7.97 16.01 5.64 15.15 5.64 11.32C5.64 10.23 6.03 9.34 6.67 8.64C6.57 8.39 6.23 7.37 6.77 6.01C6.77 6.01 7.61 5.74 9.52 7.03C10.32 6.81 11.17 6.7 12.01 6.7C12.85 6.7 13.7 6.81 14.5 7.03C16.41 5.74 17.25 6.01 17.25 6.01C17.79 7.37 17.45 8.39 17.35 8.64C17.99 9.34 18.38 10.23 18.38 11.32C18.38 15.16 16.04 16 13.81 16.25C14.17 16.56 14.49 17.17 14.49 18.11C14.49 19.46 14.48 20.55 14.48 20.88C14.48 21.15 14.66 21.47 15.17 21.37A10 10 0 0 0 12 2Z" fill="currentColor" />
    </svg>
  );
}

function CloudRunIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M19.35 10.04C18.67 6.59 15.64 4 12 4C9.11 4 6.6 5.64 5.35 8.04C2.34 8.36 0 10.91 0 14C0 17.31 2.69 20 6 20H19C21.76 20 24 17.76 24 15C24 12.36 21.95 10.22 19.35 10.04Z" fill="#1A73E8" />
      <path d="M9.5 10.5L14.5 13.5L9.5 16.5V10.5Z" fill="#FFFFFF" />
    </svg>
  );
}

export function StickyDemoFooter() {
  const { demoMode } = useDemoMode();

  // Show only in Demo OFF mode as requested
  if (demoMode) {
    return null;
  }

  return (
    <div className={styles.footer} role="contentinfo" aria-label="Demo Tech Stack & Team">
      <div className={styles.inner}>
        <div className={styles.stackSection}>
          <span className={styles.stackTitle}>Tech Stack:</span>
          
          <span className={`${styles.pill} ${styles.pillBob}`} title="IBM Bob Agent Architecture">
            <IbmBobIcon />
            <span>IBM Bob</span>
          </span>

          <span className={`${styles.pill} ${styles.pillWatson}`} title="IBM watsonx.ai Provider">
            <WatsonxIcon />
            <span>watsonx.ai</span>
          </span>

          <span className={`${styles.pill} ${styles.pillVertex}`} title="Google Vertex AI (Gemini)">
            <VertexAiIcon />
            <span>Vertex AI</span>
          </span>

          <span className={styles.pill} title="Google Cloud Platform">
            <GoogleCloudIcon />
            <span>Google Cloud</span>
          </span>

          <span className={styles.pill} title="FastAPI Framework">
            <FastApiIcon />
            <span>FastAPI</span>
          </span>

          <span className={styles.pill} title="Python 3.10+ Runtime">
            <PythonIcon />
            <span>Python 3.10+</span>
          </span>

          <span className={`${styles.pill} ${styles.pillCiCd}`} title="Full CI/CD Pipeline">
            <GitHubActionsIcon />
            <span className={styles.ciDivider}>+</span>
            <CloudRunIcon />
            <span>Full CI/CD (GitHub Actions & Cloud Run)</span>
          </span>
        </div>

        <div className={styles.teamLine}>
          <span className={styles.teamFlag} aria-hidden="true">🇦🇷</span>
          <span>Team Argentina &middot; Agustin-Diaz-Cano</span>
        </div>
      </div>
    </div>
  );
}
