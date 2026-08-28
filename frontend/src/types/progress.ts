// Progress event types — mirrors backend ProgressEvent schema
export interface ProgressEvent {
  event_id: string;
  case_id: string | null;
  phase: string;
  component: string;
  status: "pending" | "running" | "completed" | "failed" | "skipped";
  progress: number;
  message: string;
  timestamp: string;
  metadata: Record<string, unknown>;
}
