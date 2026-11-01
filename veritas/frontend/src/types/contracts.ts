export interface QuestionRequest {
  question: string;
  top_k: number; // 1..10
  threshold: number; // 0.20..0.95
}

export interface Citation {
  chunk_id: number;
  source: string;
  page: number;
  score: number;
  text: string;
}

export interface QuestionResponse {
  status: "answered" | "refused";
  answer: string;
  max_score: number;
  threshold: number;
  citations: Citation[];
  latency_ms: number;
}

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
}