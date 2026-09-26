"use client";

import type { RepoFormValues } from "../lib/types";

type Props = {
  values: RepoFormValues;
  onChange: (values: RepoFormValues) => void;
  disabled: boolean;
};

export function RepoForm({ values, onChange, disabled }: Props) {
  return (
    <fieldset disabled={disabled}>
      <label>
        Repo path
        <input
          type="text"
          value={values.repoPath}
          onChange={(e) => onChange({ ...values, repoPath: e.target.value })}
          placeholder="./demo-repo"
        />
      </label>
      <label>
        <input
          type="checkbox"
          checked={values.mutation}
          onChange={(e) => onChange({ ...values, mutation: e.target.checked })}
        />
        Run mutation testing
      </label>
      <label>
        Gate threshold (%)
        <input
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
