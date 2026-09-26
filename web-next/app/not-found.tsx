import { ButtonLink, PageHeader, PageShell } from "./components/site/Page";

export default function NotFound() {
  return (
    <PageShell>
      <PageHeader
        eyebrow="404"
        title="This page doesn't exist."
        lead="The link may be old, or the page may not be built yet."
        actions={
          <>
            <ButtonLink href="/">Analyze a repository</ButtonLink>
            <ButtonLink href="/project" variant="secondary">
              About the project
            </ButtonLink>
          </>
        }
      />
    </PageShell>
  );
}
