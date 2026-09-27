import styles from "./TechStackPills.module.css";

// 1. IBM official 8-bar logo (used for IBM watsonx.ai)
export function IbmLogo() {
  return (
    <svg width="20" height="9" viewBox="0 0 32 13" fill="currentColor" aria-hidden="true">
      <path d="M0 0h6v1.3H0zm0 1.9h6v1.3H0zm0 2h6v1.3H0zm0 1.9h6v1.3H0zm0 2h6v1.3H0zm0 1.9h6v1.3H0zm0 2h6v1.3H0zm0 1.9h6V13H0zM9 0h12v1.3H9zm0 1.9h12v1.3H9zm0 2h3.4c2.8 0 4.6.6 4.6 2 0 1.2-1.3 1.9-3.2 2H9zm0 5.9h3.8c2.4 0 4.2.7 4.2 2.2 0 1.5-2 2.3-4.8 2.3H9zm0-1.9h12v1.3H9zm0 5.8h12V13H9zM23 0h9v1.3h-9zm0 1.9h9v1.3h-9zm0 2h9v1.3h-9zm0 1.9h9v1.3h-9zm0 2h9v1.3h-9zm0 1.9h9v1.3h-9zm0 2h9v1.3h-9zm0 1.9h9V13h-9z" />
    </svg>
  );
}

// 2. Vertex AI / Gemini Sparkle
export function VertexAiIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12 2C12 7.52 7.52 12 2 12C7.52 12 12 16.48 12 22C12 16.48 16.48 12 22 12C16.48 12 12 7.52 12 2Z" />
    </svg>
  );
}

// 3. Google Cloud
export function GoogleCloudIcon() {
  return (
    <svg width="14" height="11" viewBox="0 0 24 16" fill="currentColor" aria-hidden="true">
      <path d="M19.35 6.04C18.67 2.59 15.64 0 12 0 9.11 0 6.6 1.64 5.35 4.04 2.34 4.36 0 6.91 0 10c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96z" />
    </svg>
  );
}

// 4. WIF (Workload Identity Federation / Key Shield)
export function WifIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      <circle cx="12" cy="10" r="2.2" fill="currentColor" />
    </svg>
  );
}

// 5. Terraform
export function TerraformIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M1.44 0v7.68l6.72 3.84V3.84L1.44 0zm8.16 4.8v7.68l6.72 3.84V8.64L9.6 4.8zm8.16 4.8v7.68l6.24 3.56V13.2L17.76 9.6zm-8.16 9.6v7.68l6.72-3.84v-7.68l-6.72 3.84z" />
    </svg>
  );
}

// 6. Docker
export function DockerIcon() {
  return (
    <svg width="14" height="11" viewBox="0 0 24 18" fill="currentColor" aria-hidden="true">
      <path d="M13 1h3v3h-3zm-4 0h3v3H9zm8 4h3v3h-3zm-4 0h3v3h-3zm-4 0h3v3H9zm-4 0h3v3H5zm12 4h3v3h-3zm-4 0h3v3h-3zm-4 0h3v3H9zm-4 0h3v3H5zm-4 0h3v3H1zm22.5 1.5c-.4-.3-1.6-.4-2.5.2-.2-1.3-1.2-2.3-2.3-2.7l-.7-.2-.4.6c-.6.9-.7 2.1-.3 3.1-1.1.7-2.6.9-4.8.9H0c.3 2.5 1.7 4.7 3.8 6 2.4 1.5 5.5 1.9 9.2 1.6 4.2-.3 7.8-2.2 9.8-5.3 1.1-.3 2.1-.8 2.7-1.7.3-.5.4-1.1.2-1.6-.2-.4-.7-.7-1.2-.9z" />
    </svg>
  );
}

// 7. FastAPI
export function FastApiIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12 2L2 7V17L12 22L22 17V7L12 2ZM11 6L6 14H12L11 18L17 10H11L11 6Z" />
    </svg>
  );
}

// 8. PostgreSQL
export function PostgresIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <ellipse cx="12" cy="5" rx="9" ry="3" />
      <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
      <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
    </svg>
  );
}

// 9. Next.js
export function NextJsIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12 0C5.37 0 0 5.37 0 12s5.37 12 12 12 12-5.37 12-12S18.63 0 12 0zm5.66 18.25l-6.22-8.3v8.3H9.8V6.5h1.9l6.32 8.44V6.5h1.64v11.75h-2z" />
    </svg>
  );
}

// 10. TypeScript
export function TypeScriptIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M2 2h20v20H2V2zm9.2 13.5v-1.8H9.3v-5.4H7.3v5.4H5.4v1.8h5.8zm4.3-.2c1.2 0 2.1-.6 2.1-1.7 0-1.2-.9-1.6-1.9-2-.8-.3-1.1-.6-1.1-1 0-.4.3-.7.9-.7.6 0 1 .3 1.2.7l1.5-.9c-.5-.9-1.4-1.4-2.7-1.4-1.3 0-2.3.7-2.3 1.8 0 1.1.8 1.6 1.8 2 .8.3 1.2.6 1.2 1.1 0 .5-.4.8-1 .8-.8 0-1.3-.4-1.5-1l-1.6.8c.4 1.1 1.5 1.5 2.4 1.5z" />
    </svg>
  );
}

// 11. Python 3.10+
export function PythonIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M11.91 2C6.98 2 7.3 4.14 7.3 4.14L7.31 6.36H12.02V7.08H5.24C5.24 7.08 2 6.72 2 11.87C2 17.02 4.83 16.79 4.83 16.79H6.51V14.41C6.51 14.41 6.42 11.56 9.32 11.56H14.11C14.11 11.56 16.85 11.65 16.85 8.96V4.28C16.85 4.28 17.26 2 11.91 2ZM9.12 3.48C9.64 3.48 10.06 3.9 10.06 4.42C10.06 4.94 9.64 5.36 9.12 5.36C8.6 5.36 8.18 4.94 8.18 4.42C8.18 3.9 8.6 3.48 9.12 3.48Z" />
      <path d="M12.09 22C17.02 22 16.7 19.86 16.7 19.86L16.69 17.64H11.98V16.92H18.76C18.76 16.92 22 17.28 22 12.13C22 6.98 19.17 7.21 19.17 7.21H17.49V9.59C17.49 9.59 17.58 12.44 14.68 12.44H9.89C9.89 12.44 7.15 12.35 7.15 15.04V19.72C7.15 19.72 6.74 22 12.09 22ZM14.88 20.52C14.36 20.52 13.94 20.1 13.94 19.58C13.94 19.06 14.36 18.64 14.88 18.64C15.4 18.64 15.82 19.06 15.82 19.58C15.82 20.1 15.4 20.52 14.88 20.52Z" />
    </svg>
  );
}

// 12. GitHub Actions
export function GitHubActionsIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12 2A10 10 0 0 0 8.84 21.49C9.34 21.58 9.52 21.27 9.52 21C9.52 20.77 9.51 20 9.51 19.16C6.73 19.76 6.14 17.82 6.14 17.82C5.68 16.66 5.03 16.35 5.03 16.35C4.12 15.73 5.1 15.74 5.1 15.74C6.1 15.81 6.63 16.77 6.63 16.77C7.53 18.31 8.98 17.86 9.55 17.61C9.64 16.96 9.9 16.51 10.19 16.26C7.97 16.01 5.64 15.15 5.64 11.32C5.64 10.23 6.03 9.34 6.67 8.64C6.57 8.39 6.23 7.37 6.77 6.01C6.77 6.01 7.61 5.74 9.52 7.03C10.32 6.81 11.17 6.7 12.01 6.7C12.85 6.7 13.7 6.81 14.5 7.03C16.41 5.74 17.25 6.01 17.25 6.01C17.79 7.37 17.45 8.39 17.35 8.64C17.99 9.34 18.38 10.23 18.38 11.32C18.38 15.16 16.04 16 13.81 16.25C14.17 16.56 14.49 17.17 14.49 18.11C14.49 19.46 14.48 20.55 14.48 20.88C14.48 21.15 14.66 21.47 15.17 21.37A10 10 0 0 0 12 2Z" />
    </svg>
  );
}

// 13. Cloud Run
export function CloudRunIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M19.35 10.04C18.67 6.59 15.64 4 12 4C9.11 4 6.6 5.64 5.35 8.04C2.34 8.36 0 10.91 0 14C0 17.31 2.69 20 6 20H19C21.76 20 24 17.76 24 15C24 12.36 21.95 10.22 19.35 10.04Z" />
    </svg>
  );
}

// 14. Claude Code
export function ClaudeIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M13.5 2h-3v7.2L5.4 4.1 3.3 6.2l5.1 5.1H2v3h6.4l-5.1 5.1 2.1 2.1 5.1-5.1V22h3v-6.4l5.1 5.1 2.1-2.1-5.1-5.1H22v-3h-6.4l5.1-5.1-2.1-2.1-5.1 5.1V2z" />
    </svg>
  );
}

// 15. Antigravity
export function AntigravityIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden="true">
      <circle cx="12" cy="12" r="3" fill="currentColor" />
      <path d="M12 2v4m0 12v4M2 12h4m12 0h4m-3.07-6.93l-2.83 2.83m-8.2 8.2l-2.83 2.83m0-13.86l2.83 2.83m8.2 8.2l2.83 2.83" />
    </svg>
  );
}

// 16. Vercel
export function VercelIcon() {
  return (
    <svg width="11" height="10" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12 1L24 22H0L12 1Z" />
    </svg>
  );
}

export function TechStackPills() {
  return (
    <div className={styles.stackSection}>
      <span className={styles.stackTitle}>Built with:</span>
      
      <span className={styles.pill} title="IBM Bob IDE">
        <span>IBM Bob IDE</span>
      </span>

      <span className={styles.pill} title="IBM watsonx.ai Provider">
        <IbmLogo />
        <span>IBM watsonx.ai</span>
      </span>

      <span className={styles.pill} title="Claude Code Agent">
        <ClaudeIcon />
        <span>Claude Code</span>
      </span>

      <span className={styles.pill} title="Google Antigravity">
        <AntigravityIcon />
        <span>Antigravity</span>
      </span>

      <span className={styles.pill} title="Vercel Platform">
        <VercelIcon />
        <span>Vercel</span>
      </span>

      <span className={styles.pill} title="Google Vertex AI (Gemini)">
        <VertexAiIcon />
        <span>Vertex AI</span>
      </span>

      <span className={styles.pill} title="Google Cloud Platform">
        <GoogleCloudIcon />
        <span>Google Cloud</span>
      </span>

      <span className={styles.pill} title="Workload Identity Federation">
        <WifIcon />
        <span>WIF</span>
      </span>

      <span className={styles.pill} title="Terraform Infrastructure as Code">
        <TerraformIcon />
        <span>Terraform</span>
      </span>

      <span className={styles.pill} title="Docker Containers">
        <DockerIcon />
        <span>Docker</span>
      </span>

      <span className={styles.pill} title="FastAPI Backend">
        <FastApiIcon />
        <span>FastAPI</span>
      </span>

      <span className={styles.pill} title="PostgreSQL Database">
        <PostgresIcon />
        <span>PostgreSQL</span>
      </span>

      <span className={styles.pill} title="Next.js Frontend">
        <NextJsIcon />
        <span>Next.js</span>
      </span>

      <span className={styles.pill} title="TypeScript">
        <TypeScriptIcon />
        <span>TypeScript</span>
      </span>

      <span className={styles.pill} title="Python 3.10+ Runtime">
        <PythonIcon />
        <span>Python 3.10+</span>
      </span>

      <span className={styles.pill} title="GitHub Actions CI & Google Cloud Run CD">
        <GitHubActionsIcon />
        <span className={styles.ciDivider}>+</span>
        <CloudRunIcon />
        <span>Full CI/CD (GitHub Actions & Cloud Run)</span>
      </span>
    </div>
  );
}
