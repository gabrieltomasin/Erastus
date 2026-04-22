export interface Campaign {
  id: number;
  title: string;
  description: string;
  session_count: number;
  created_at: string;
  updated_at: string;
}

export interface CampaignDetail extends Campaign {
  general_context: string | null;
  system_prompt: string | null;
  context_updated_at: string | null;
  sessions: SessionBrief[];
}

export interface CampaignCreate {
  title: string;
  description?: string;
  system_prompt?: string;
}

export interface CampaignUpdate {
  title?: string;
  description?: string;
  system_prompt?: string;
  general_context?: string;
}

export interface SessionBrief {
  id: number;
  title: string;
  session_number: number;
  status: SessionStatus;
  created_at: string;
}

export type SessionStatus = "pending" | "transcribing" | "summarizing" | "ready" | "error";

export interface Session {
  id: number;
  campaign_id: number;
  title: string;
  session_number: number;
  status: SessionStatus;
  created_at: string;
  updated_at: string;
}

export interface SessionDetail extends Session {
  audio_files: AudioFile[] | null;
  transcription: string | null;
  raw_summary: string | null;
  final_summary: string | null;
  error_message: string | null;
  processing_logs: ProcessingLog[];
}

export interface AudioFile {
  filename: string;
  size: number;
  path: string;
  duration?: number;
}

export interface ProcessingLog {
  id: number;
  session_id: number;
  step: string;
  message: string;
  level: string;
  timestamp: string;
}

export interface SessionCreate {
  campaign_id: number;
  title: string;
}

export interface SessionUpdate {
  title?: string;
  final_summary?: string;
}
