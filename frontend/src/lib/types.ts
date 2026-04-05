export interface LLMConfig {
  id: string;
  api_endpoint: string;
  model: string;
  created_at: string;
}

export interface Project {
  id: string;
  name: string;
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
}

export type ProjectStatus =
  | "new"
  | "clarifying"
  | "arch_pending"
  | "arch_approved"
  | "executing"
  | "done"
  | "failed";

export interface QAPair {
  question: string;
  answer: string;
}

export interface Requirement {
  id: string;
  project_id: string;
  raw_text: string;
  clarification_qa: QAPair[];
  pending_question: string | null;
  final_text: string | null;
}

export interface Architecture {
  id: string;
  project_id: string;
  content: Record<string, unknown>;
  markdown: string;
  approved: boolean;
  approved_at: string | null;
}

export interface TaskItem {
  id: string;
  title: string;
  status: "pending" | "in_progress" | "done" | "failed";
  result: string | null;
}

export interface Ticket {
  id: string;
  project_id: string;
  title: string;
  description: string;
  acceptance_criteria: string;
  status: "pending" | "in_progress" | "done" | "failed";
  tasks: TaskItem[];
}

export interface LogEntry {
  id: string;
  project_id: string;
  level: "info" | "warn" | "error";
  message: string;
  created_at: string;
}

export interface SSEEvent {
  type:
    | "log"
    | "status_change"
    | "clarification_question"
    | "architecture_ready"
    | "tickets_ready"
    | "ticket_update"
    | "task_update";
  data: Record<string, unknown>;
}
