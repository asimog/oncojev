/**
 * Presentation-only mapping from recorded event kinds to epistemic categories.
 * The frontend never decides what counts as evidence or a judgment; it only
 * labels what the backend already recorded.
 */
export type EpistemicCategory =
  | "observation"
  | "measurement"
  | "evidence"
  | "jev"
  | "hypothesis"
  | "action";

export interface CategoryMeta {
  id: EpistemicCategory;
  label: string;
  description: string;
}

export const CATEGORIES: Record<EpistemicCategory, CategoryMeta> = {
  observation: {
    id: "observation",
    label: "Observation",
    description: "Bounded state the Researcher recorded. Not a measurement.",
  },
  measurement: {
    id: "measurement",
    label: "Measurement",
    description: "Deterministic result produced by Science. Not yet admitted.",
  },
  evidence: {
    id: "evidence",
    label: "Scientific evidence",
    description: "Admitted deterministic measurement. The only evidence source.",
  },
  jev: {
    id: "jev",
    label: "Jev judgment",
    description: "Semantic probability about bounded structured state. Never evidence.",
  },
  hypothesis: {
    id: "hypothesis",
    label: "Hypothesis",
    description: "A possibility from the Reasoner. Never evidence.",
  },
  action: {
    id: "action",
    label: "Agent action",
    description: "A Director or Researcher lifecycle action from the ledger.",
  },
};

const EVENT_CATEGORY: Record<string, EpistemicCategory> = {
  ScienceMeasurement: "measurement",
  EvidenceAdmission: "evidence",
  JevExecution: "jev",
  JevExecutionFailure: "jev",
  ReasonerOutput: "hypothesis",
  ReasonerFailure: "hypothesis",
  ScopeEscalationRequested: "hypothesis",
};

export function categoriseEvent(eventType: string): EpistemicCategory {
  return EVENT_CATEGORY[eventType] ?? "action";
}
