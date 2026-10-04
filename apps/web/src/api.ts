export type Evidence = { id:string; title:string; content:string; document_title:string; verification_status:string; evidence_type:string; source_locator:Record<string,unknown> }
export type Document = { id:string; title:string; status:string; document_type:string; trust_level:string; created_at:string }
export type Questionnaire = { id:string; name:string; buyer_name:string; status:string; processing_status:string; processing_error:string; question_count:number }
export type Answer = { id:string; answer_text:string; status:string; confidence:number; grounding_score:number; citations:{evidence_id:string;title:string;document_title:string;excerpt:string;source_locator:Record<string,unknown>}[] }
export type Question = { id:string; questionnaire:string; question_number:string; question_text:string; required:boolean; sort_order:number; status:string; latest_answer:Answer|null }
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
export async function downloadFile(path:string, filename:string):Promise<void> {
  const headers = new Headers()
  const access = token()
  const organization = localStorage.getItem('proofgraph_organization')
  if (access) headers.set('Authorization', `Bearer ${access}`)
  if (organization) headers.set('X-Organization-ID', organization)
  const response = await fetch(`${API}${path}`, { headers })
  if (!response.ok) throw new Error(`Export failed (${response.status})`)
  const objectUrl = URL.createObjectURL(await response.blob())
  const anchor = document.createElement('a'); anchor.href = objectUrl; anchor.download = filename; anchor.click()
  URL.revokeObjectURL(objectUrl)
}
