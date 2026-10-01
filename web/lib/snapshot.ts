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
  origin?: string;
  interpretation?: string;
  limitations?: string[];
  diagnostics?: Record<string,unknown>;
}

export interface EvidenceView {
  evidence_id: string;
  admitted_at: string;
  measurement: MeasurementView;
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
  resource_usage: Record<string, unknown>;
  objective_attainment?: string;
  operational_failures?: Record<string,unknown>[];
  statements?: Record<string,unknown>[];
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
    run_outcome?: string;
    outcome_inferred?: boolean;
  };
}

export interface SnapshotShape {
  generated_at: string;
  transport: "live_api" | "offline_snapshot";
  data_provenance: string;
  api_status?: "available" | "unavailable";
  limitations: string[];
  conditions: string[];
  overview: {
    records: number;
    blocks: number;
    cycles: number;
    dossiers: number;
    evidence: number;
    latest_cycle: { mode: string; status?:string; error_type?:string|null } | null;
    data_provenance?: string;
    source_activity?: {attempts:number;successes:number;failures:number;unresolved:number};
  };
  research_memory: { summary: string; provenance: string[] }[];
  blocks: BlockView[];
}

const fallback = snapshot as unknown as SnapshotShape;
const apiBase = process.env.ONCOJEV_API_URL ?? "http://127.0.0.1:8080";

async function api<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, { cache: "no-store", signal: AbortSignal.timeout(5000) });
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
      conditions: [],
      transport: "live_api",
      api_status: "available",
      data_provenance: overview.data_provenance ?? "unknown",
      limitations: ["API connectivity does not establish successful research or scientific utility."],
      overview,
      research_memory: memory.research_memory,
      blocks,
    };
  } catch {
    return { ...fallback, transport: "offline_snapshot", api_status: "unavailable",
      data_provenance: fallback.data_provenance ?? "unknown",
      limitations: [...(fallback.limitations ?? []), "Live API unavailable; displaying committed offline snapshot."] };
  }
}
