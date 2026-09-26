import type { Metadata } from "next";
import { PageHeader } from "../components/site/Page";
import { ResultsDashboard } from "./ResultsDashboard";
import styles from "./results.module.css";

export const metadata: Metadata = {
  title: "Results",
  description: "Measurement history per project: coverage vs. mutation score, surviving bug kinds, fix-loop effect.",
};

export default function ResultsPage() {
  return (
    <main className={styles.main}>
      <PageHeader
        eyebrow="Results"
        title="Results dashboard"
        lead="Stored runs per project, over time: whether the suite is getting better at catching bugs or just running more lines, which kinds of bugs survive, and what each fix run changed. Every value is read from the backend as measured."
      />
      <ResultsDashboard />
    </main>
  );
}
