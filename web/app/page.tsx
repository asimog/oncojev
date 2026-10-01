import Link from "next/link";

import { Legend } from "@/components/Section";
import { getData } from "@/lib/snapshot";

export const dynamic = "force-dynamic";

function Metric({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="card">
      <div className="metric">{value}</div>
      <div className="label">{label}</div>
    </div>
  );
}

export default async function OverviewPage() {
  const data = await getData();
  const { overview, blocks, research_memory, conditions, generated_at, transport, data_provenance, limitations } = data;
  return (
    <>
      <h1>Mission overview</h1>
      <p className="muted">
        generated {generated_at} · transport {transport} · provenance {data_provenance} · mode {overview.latest_cycle?.mode ?? "unknown"}
        {conditions.length ? ` · evaluated conditions ${conditions.join(", ")}` : ""}
      </p>

      <p className="muted">{limitations.join(" ")}</p>
      <p>Latest cycle: {overview.latest_cycle?.status ?? "unknown"}{overview.latest_cycle?.error_type ? ` · ${overview.latest_cycle.error_type}` : ""}</p>
      {overview.source_activity ? <p>Source attempts {overview.source_activity.attempts} · successes {overview.source_activity.successes} · failures {overview.source_activity.failures} · unresolved {overview.source_activity.unresolved}</p> : null}
      <div className="grid">
        <Metric label="Blocks" value={overview.blocks} />
        <Metric label="Evidence" value={overview.evidence} />
        <Metric label="Dossiers" value={overview.dossiers} />
        <Metric label="Cycles" value={overview.cycles} />
        <Metric label="Records" value={overview.records} />
      </div>

      <h2>Blocks</h2>
      {blocks.length === 0 ? <p className="muted">No blocks recorded.</p> : null}
      {blocks.map((block) => {
        const id = block.reconstruction.block_id;
        const objective = block.reconstruction.block?.start.objective ?? "(objective unavailable)";
        const reason = block.reconstruction.block?.termination_reason ?? block.reconstruction.block?.status;
        return (
          <div className="row" key={id}>
            <div className="name">
              <Link href={`/blocks/${id}`}>{objective}</Link>
            </div>
            <div className="meta">
              {id} · lifecycle {block.reconstruction.block?.status ?? "unknown"} · run {block.reconstruction.run_outcome ?? "unknown"} · {String(reason)} · dossier {block.summary.has_dossier ? "present" : "absent"}
            </div>
          </div>
        );
      })}

      <h2>Research memory</h2>
      {research_memory.length === 0 ? <p className="muted">No research memory recorded.</p> : null}
      {research_memory.map((entry, index) => (
        <div className="row" key={index}>
          <div className="meta">{entry.provenance?.join(" · ")}</div>
          <pre>{entry.summary}</pre>
        </div>
      ))}

      <h2>Epistemic categories</h2>
      <p className="muted">
        The frontend only labels what the backend recorded. It never decides what counts as evidence.
      </p>
      <Legend />
    </>
  );
}
