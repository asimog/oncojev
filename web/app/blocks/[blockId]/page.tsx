import Link from "next/link";
import { notFound } from "next/navigation";

import { Row, Section } from "@/components/Section";
import { categoriseEvent } from "@/lib/categories";
import { getData } from "@/lib/snapshot";

export const dynamic = "force-dynamic";

export default async function BlockPage({ params }: { params: { blockId: string } }) {
  const data = await getData();
  const view = data.blocks.find((item)=>item.reconstruction.block_id===params.blockId);
  if (!view) {
    notFound();
  }
  const reconstruction = view.reconstruction;
  const block = reconstruction.block;
  const dossier = reconstruction.dossier;
  const state = reconstruction.state_revisions.at(-1);

  return (
    <>
      <p>
        <Link href="/">← mission overview</Link>
      </p>
      <p className="muted">Transport {data.transport} · provenance {data.data_provenance}. {data.limitations.join(" ")}</p>
      <h1>{block?.start.objective ?? reconstruction.block_id}</h1>
      <p className="muted">
        {reconstruction.block_id} · status {String(block?.status)} · termination{" "}
        {String(block?.termination_reason)} · deadline {String(block?.deadline)}
      </p>

      <p>Run outcome {reconstruction.run_outcome ?? "unknown"} · objective attainment {dossier?.objective_attainment ?? "unknown"}{reconstruction.outcome_inferred ? " · historical completion claim contradicted or unverified" : ""}</p>
      <Section category="action" title="Agent actions and lifecycle" hint="append-only ledger" count={reconstruction.ledger.length}>
        {reconstruction.ledger.length === 0 ? <p className="muted">No ledger events recorded.</p> : null}
        {reconstruction.ledger.map((event) => (
          <Row
            key={event.event_id}
            name={event.event_type}
            meta={`${categoriseEvent(event.event_type)} · ${event.occurred_at}`}
            detail={event.payload}
          />
        ))}
      </Section>

      <Section category="observation" title="Observations" hint="bounded state fragments, not measurements" count={state?.observations?.length ?? 0}>
        {!state || state.observations.length === 0 ? <p className="muted">No observations recorded.</p> : null}
        {state?.observations?.map((fragment) => (
          <Row key={fragment.fragment_id} name={fragment.kind} meta={fragment.provenance.join(" · ")} detail={fragment.summary} />
        ))}
      </Section>

      <Section category="measurement" title="Deterministic measurements" hint="Science output, before admission" count={reconstruction.measurements.length}>
        {reconstruction.measurements.length === 0 ? <p className="muted">No measurements recorded.</p> : null}
        {reconstruction.measurements.map((measurement) => (
          <Row
            key={measurement.analysis_id}
            name={measurement.analysis_id}
            meta={`origin=${measurement.origin ?? "unknown"} · interpretation=${measurement.interpretation ?? "unknown"} · deterministic=${String(measurement.deterministic)}`}
            detail={{values:measurement.values,limitations:measurement.limitations,diagnostics:measurement.diagnostics,provenance:measurement.provenance}}
          />
        ))}
      </Section>

      <Section category="evidence" title="Scientific evidence" hint="admitted measurements — the only evidence" count={reconstruction.evidence.length}>
        {reconstruction.evidence.length === 0 ? <p className="muted">No admitted evidence.</p> : null}
        {reconstruction.evidence.map((item) => {
          const referenced = (dossier?.evidence_refs ?? []).includes(item.evidence_id);
          return (
            <Row
              key={item.evidence_id}
              name={`evidence ${item.evidence_id}`}
              meta={`admitted ${item.admitted_at}${referenced ? " · referenced by dossier" : ""}`}
              detail={{values:item.measurement.values,origin:item.measurement.origin,interpretation:item.measurement.interpretation,limitations:item.measurement.limitations,diagnostics:item.measurement.diagnostics}}
            />
          );
        })}
      </Section>

      <Section category="jev" title="Jev judgments" hint="semantic probability — never evidence" count={reconstruction.jev_outputs.length}>
        {reconstruction.jev_outputs.length === 0 ? <p className="muted">No Jev measurements recorded.</p> : null}
        {reconstruction.jev_outputs.map((output) => (
          <Row
            key={JSON.stringify(output).slice(0, 24)}
            name="System One decisions"
            meta="distributions retained"
            detail={output}
          />
        ))}
        {reconstruction.jev_failures.length > 0 ? (
          <Row name="Jev operational failures" meta="failure is not a judgment" detail={reconstruction.jev_failures} />
        ) : null}
      </Section>

      <Section category="hypothesis" title="Hypotheses" hint="possibilities from the Reasoner — never evidence" count={dossier?.hypotheses.length ?? 0}>
        {!dossier || dossier.hypotheses.length === 0 ? <p className="muted">No hypotheses recorded.</p> : null}
        {dossier?.hypotheses.map((hypothesis, index) => (
          <Row key={index} name={`hypothesis ${index + 1}`} detail={hypothesis} />
        ))}
      </Section>

      <Section category="action" title="Frontier decisions" hint="deterministic policy" count={dossier?.frontier_decisions.length ?? 0}>
        {dossier?.frontier_decisions.map((decision, index) => (
          <Row key={index} name={decision} />
        ))}
      </Section>

      <Section category="action" title="Dossier" hint="summary, not evidence" count={dossier ? 1 : 0}>
        {!dossier ? <p className="muted">No dossier assembled.</p> : null}
        {dossier ? (
          <>
            <Row name="operational failures" detail={dossier.operational_failures ?? []} />
            <Row name="statement-specific support" detail={dossier.statements ?? []} />
            <Row name="termination" meta={dossier.termination_reason} />
            <Row name="evidence references" meta="traceability" detail={dossier.evidence_refs} />
            <Row name="analyses performed" detail={dossier.analyses_performed} />
            <Row name="unresolved uncertainty" detail={dossier.unresolved_uncertainties} />
            <Row name="recommended next blocks" meta="proposals to the Director" detail={dossier.recommended_next_blocks} />
            <Row name="preferred continuation" meta={dossier.preferred_continuation_reason} detail={dossier.preferred_continuation} />
            <Row name="resource usage" detail={dossier.resource_usage} />
          </>
        ) : null}
      </Section>
    </>
  );
}
