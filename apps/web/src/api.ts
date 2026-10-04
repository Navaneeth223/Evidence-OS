export type Evidence = { id:string; title:string; content:string; document_title:string; verification_status:string; evidence_type:string; source_locator:Record<string,unknown> }
export type Document = { id:string; title:string; status:string; document_type:string; trust_level:string; created_at:string }
export type Questionnaire = { id:string; name:string; buyer_name:string; status:string; question_count:number }
const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
const token = () => localStorage.getItem('proofgraph_access')
export async function api<T>(path:string, init:RequestInit = {}):Promise<T> {
  const headers = new Headers(init.headers)
  if (token()) headers.set('Authorization', `Bearer ${token()}`)
  const organization = localStorage.getItem('proofgraph_organization')
  if (organization) headers.set('X-Organization-ID', organization)
  if (init.body && !(init.body instanceof FormData)) headers.set('Content-Type','application/json')
  const response = await fetch(`${API}${path}`, { ...init, headers })
  if (!response.ok) { const body = await response.json().catch(() => ({})); throw new Error(body.detail ?? `Request failed (${response.status})`) }
  return response.status === 204 ? undefined as T : response.json()
}
