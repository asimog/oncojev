import snapshot from "@/data/snapshot.json";

/**
 * Generated snapshot of application read models. This module performs no
 * research logic; it only narrows committed JSON for presentation components.
 */

export interface StateFragment {
  fragment_id: string;
  kind: string;
  summary: string;
  provenance: string[];
}

export interface ResearchStateView {
  observations: StateFragment[];
  uncertainties: StateFragment[];
  candidates: StateFragment[];
}

export interface MeasurementView {
  analysis_id: string;
  deterministic: boolean;
  provenance: string[];
  values: Record<string, unknown>;
}

export interface EvidenceView {
  evidence_id: string;
  admitted_at: string;
  measurement: { analysis_id: string; values: Record<string, unknown> };
}

export interface LedgerEventView {
  event_id: string;
  event_type: string;
  occurred_at: string;
  payload: Record<string, unknown>;
}

export interface DossierView {
  block_id: string;
  termination_reason: string;
  evidence_refs: string[];
  hypotheses: string[];
  analyses_performed: string[];
  unresolved_uncertainties: string[];
  recommended_next_blocks: string[];
  preferred_continuation: string;
  preferred_continuation_reason: string;
  frontier_decisions: string[];
  resource_usage: Record<string, number>;
}

export interface BlockView {
  summary: { block_id: string; has_dossier: boolean };
  reconstruction: {
    block_id: string;
    block: {
      start: { objective: string };
      status: string;
      termination_reason: string | null;
      deadline: string;
    } | null;
    state_revisions: ResearchStateView[];
    measurements: MeasurementView[];
    evidence: EvidenceView[];
    jev_outputs: Record<string, unknown>[];
    jev_failures: Record<string, unknown>[];
    artifacts: Record<string, unknown>[];
    ledger: LedgerEventView[];
    dossier: DossierView | null;
    capability_invocations: Record<string, unknown>[];
    complete: boolean;
  };
}

export interface SnapshotShape {
  generated_at: string;
  conditions: string[];
  overview: {
    records: number;
    blocks: number;
    cycles: number;
    dossiers: number;
    evidence: number;
    latest_cycle: { mode: string } | null;
  };
  research_memory: { summary: string; provenance: string[] }[];
  blocks: BlockView[];
}

const fallback = snapshot as unknown as SnapshotShape;
const apiBase = process.env.ONCOJEV_API_URL ?? "http://127.0.0.1:8080";

async function api<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`OncoJev API ${path} returned ${response.status}`);
  return response.json() as Promise<T>;
}

export async function getData(): Promise<SnapshotShape> {
  try {
    const [overview, blockList, memory] = await Promise.all([
      api<SnapshotShape["overview"]>("/api/overview"),
      api<{ blocks: BlockView["summary"][] }>("/api/blocks"),
      api<{ research_memory: SnapshotShape["research_memory"] }>("/api/research-memory"),
    ]);
    const blocks = await Promise.all(
      blockList.blocks.map(async (summary) => ({
        summary,
        reconstruction: await api<BlockView["reconstruction"]>(`/api/blocks/${encodeURIComponent(summary.block_id)}/reconstruction`),
      })),
    );
    return {
      generated_at: new Date().toISOString(),
      conditions: fallback.conditions,
      overview,
      research_memory: memory.research_memory,
      blocks,
    };
  } catch {
    return fallback;
  }
}

export async function findBlock(blockId: string): Promise<BlockView | undefined> {
  const data = await getData();
  return data.blocks.find((block) => block.reconstruction.block_id === blockId);
}
