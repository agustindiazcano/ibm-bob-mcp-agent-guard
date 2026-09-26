"use client";

import type { RepoFormValues } from "../lib/types";
import styles from "./Controls.module.css";

type Props = {
  values: RepoFormValues;
  onChange: (values: RepoFormValues) => void;
  disabled: boolean;
};

export function RepoForm({ values, onChange, disabled }: Props) {
  return (
    <fieldset className={styles.form} disabled={disabled}>
      <label className={styles.field}>
        Repo path
        <input
          className={styles.input}
          type="text"
          value={values.repoPath}
          onChange={(e) => onChange({ ...values, repoPath: e.target.value })}
          placeholder="./demo-repo"
          spellCheck={false}
        />
      </label>
      <label className={styles.check}>
        <input
          type="checkbox"
          checked={values.mutation}
          onChange={(e) => onChange({ ...values, mutation: e.target.checked })}
        />
        Run mutation testing
      </label>
      <label className={styles.field}>
        Gate threshold (%)
        <input
          className={styles.input}
          type="number"
          min={0}
          max={100}
          value={values.gateThreshold}
          onChange={(e) => onChange({ ...values, gateThreshold: Number(e.target.value) })}
        />
      </label>
    </fieldset>
  );
}
