export type ApiError = Error & { status?: number; requestId?: string };

export interface Section {
  id: string;
  title: string;
  content: string;
  updatedAt?: string;
}

export interface Comment {
  id: string;
  sectionId: string;
  text: string;
  author?: string;
  createdAt: string;
  startOffset?: number;
  endOffset?: number;
}

export type DraftStatus = 'input' | 'draft' | 'review' | 'final';

export interface Draft {
  id: string;
  status: DraftStatus;
  sections: Section[];
  comments?: Record<string, Comment[]>;
  initialInput?: Record<string, any>;
}

const BASE = process.env.NEXT_PUBLIC_API_URL!;
function assertBase() {
  if (!BASE) throw new Error("NEXT_PUBLIC_API_URL missing");
}
async function handle(res: Response) {
  const rid = res.headers.get("x-request-id") || "";
  const text = await res.text().catch(() => "");
  if (!res.ok) {
    const e: ApiError = new Error(`HTTP ${res.status} ${res.statusText} [${rid}] ${text}`);
    e.status = res.status; e.requestId = rid;
    throw e;
  }
  return text ? JSON.parse(text) : {};
}

export async function createDraft(initialInput?: any) {
  assertBase();
  const r = await fetch(`${BASE}/proposals`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "omit",
    body: JSON.stringify({ initialInput })
  });
  const data = await handle(r);
  return data.draft as Draft;
}

export async function getDraft(id: string) {
  assertBase();
  const r = await fetch(`${BASE}/proposals/${id}`, { credentials: "omit" });
  const data = await handle(r);
  return data.draft as Draft;
}

export async function addComment(draftId: string, p: { sectionId: string; text: string; startOffset?: number; endOffset?: number; author?: string; }) {
  assertBase();
  const r = await fetch(`${BASE}/proposals/${draftId}/comments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "omit",
    body: JSON.stringify(p)
  });
  const data = await handle(r);
  return data.comment as Comment;
}

export async function refine(draftId: string, sectionIds: string[]) {
  assertBase();
  const r = await fetch(`${BASE}/proposals/${draftId}/refine`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "omit",
    body: JSON.stringify({ changedSectionIds: sectionIds })
  });
  const data = await handle(r);
  return data.updatedSections as Record<string, string>;
}

export async function importDoc(file: File) {
  assertBase();
  const fd = new FormData();
  fd.append("file", file);
  const r = await fetch(`${BASE}/import/document`, {
    method: "POST",
    body: fd,
    credentials: "omit"
  });
  const data = await handle(r);
  return data as { extracted: any; suggestedSections: any[]; insightQuestions?: { key: string; label: string }[] };
} 

// Backward-compat shim for legacy components still importing grantAPI
export const grantAPI = {
  uploadDocuments: async (_files: File[]) => {
    return { success: true, upload_method: 'standard', file_urls: {} as Record<string, string> }
  },
  generateQuickProposal: async (_data: any) => ({ success: true, proposal: '', timestamp: new Date().toISOString() }),
  generateFullProposal: async (_data: any) => ({ success: true, proposal: '', timestamp: new Date().toISOString() }),
  checkHealth: async () => ({ ok: true })
}