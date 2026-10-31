import { useEffect, useState } from 'react'
import { ArrowDownToLine, ArrowRight, ChartNoAxesCombined, ChevronRight, Database, FileText, LayoutDashboard, Plus, Sprout } from 'lucide-react'
import { api } from './services/api'
import type { DataSet, Intelligence, Report, Workspace } from './types'
import { AudienceChart, Findings, Summary } from './components/Intelligence'
import DataPage from './pages/DataPage'
import AnalysisPage from './pages/AnalysisPage'
import ReportsPage from './pages/ReportsPage'

const navigation = [{ name: 'Dashboard', icon: LayoutDashboard }, { name: 'Analysis', icon: ChartNoAxesCombined }, { name: 'Reports', icon: FileText }, { name: 'Data', icon: Database }]
const empty: DataSet = { rows: [], brands: [], imports: [] }

export default function App() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([])
  const [id, setId] = useState<number | null>(null)
  const [page, setPage] = useState('Data')
  const [dataset, setDataset] = useState<DataSet>(empty)
  const [analysis, setAnalysis] = useState<Intelligence | null>(null)
  const [report, setReport] = useState<Report | null>(null)
  const [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [creating, setCreating] = useState(false)
  const [name, setName] = useState('')
  const workspace = workspaces.find(w => w.id === id)
  useEffect(() => { api<Workspace[]>('/workspaces').then(ws => { setWorkspaces(ws); setId(ws[0]?.id ?? null) }).catch(e => setError(`Could not reach the backend. Start FastAPI on port 8000. ${e.message}`)).finally(() => setLoading(false)) }, [])
  useEffect(() => {
    let current = true
    setDataset(empty); setAnalysis(null); setReport(null); setError(''); setMessage('')
    if (id == null) return
    setLoading(true)
    const selected = workspaces.find(w => w.id === id)
    Promise.all([api<DataSet>(`/workspaces/${id}/data`), selected?.primary_brand ? api<Intelligence>(`/workspaces/${id}/analysis`) : Promise.resolve(null)]).then(([d, a]) => { if (current) { setDataset(d); setAnalysis(a) } }).catch(e => { if (current) setError(e.message) }).finally(() => { if (current) setLoading(false) })
    return () => { current = false }
  // Workspace changes reload all workspace-bound views. Mutations use refresh below.
  }, [id])
  async function refresh() {
    const ws = await api<Workspace[]>('/workspaces')
    const selected = ws.find(w => w.id === id)
    const [d, a] = await Promise.all([api<DataSet>(`/workspaces/${id}/data`), selected?.primary_brand ? api<Intelligence>(`/workspaces/${id}/analysis`) : Promise.resolve(null)])
    setWorkspaces(ws); setDataset(d); setAnalysis(a); setReport(null)
  }
  async function run(task: () => Promise<void>) {
    setBusy(true); setError(''); setMessage('')
    try { await task(); setMessage('All set. Your workspace is up to date.') } catch (e) { setError(e instanceof Error ? e.message : 'Unable to complete this action.') } finally { setBusy(false) }
  }
  return <div className="app-shell"><aside className="sidebar"><a className="brand" href="#" onClick={e => { e.preventDefault(); setPage('Dashboard') }}><span className="brand-icon"><ChartNoAxesCombined size={23}/></span><span>marketing<span className="brand-second">intelligence<span className="version">V0.1</span></span></span></a><div className="workspace-picker"><label htmlFor="workspace">WORKSPACE</label><select id="workspace" value={id ?? ''} disabled={busy || loading} onChange={e => { setId(Number(e.target.value)); setCreating(false) }}><option value="" disabled>Select workspace</option>{workspaces.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}</select><button className="text-button" disabled={busy || loading} onClick={() => setCreating(!creating)}><Plus size={14}/>New workspace</button>{creating && <form className="create-workspace" onSubmit={e => { e.preventDefault(); run(async () => { const w = await api<Workspace>('/workspaces', 'POST', { name }); setWorkspaces([...workspaces, w]); setId(w.id); setName(''); setCreating(false); setPage('Data') }) }}><input aria-label="Workspace name" autoFocus required maxLength={120} placeholder="Workspace name" value={name} onChange={e => setName(e.target.value)}/><button className="button primary" disabled={busy || !name.trim()}>Create</button></form>}</div><nav aria-label="Main navigation">{navigation.map(n => <button disabled={busy} className={page === n.name ? 'active' : ''} key={n.name} onClick={() => setPage(n.name)}><n.icon size={19}/>{n.name}{page === n.name && <span className="nav-dot"/>}</button>)}</nav><div className="sidebar-bottom"><div className="quiet-card"><Sprout size={22}/><h3>Clarity over complexity.</h3><p>Your data. A little perspective. Better marketing decisions.</p></div><span className="local-status"><span/>Local workspace · no AI required</span></div></aside>
    <div className="main-shell"><header className="topbar"><div className="breadcrumb">Workspace <ChevronRight size={14}/><span>{page}</span></div><span className="version-pill">FOUNDATION / V0.1</span></header><main aria-busy={busy || loading}>{error && <div className="notice error" role="alert">{error}<button onClick={() => setError('')} aria-label="Dismiss error">×</button></div>}{message && <div className="notice" role="status">{message}<button onClick={() => setMessage('')} aria-label="Dismiss message">×</button></div>}{busy && <div className="working" role="status">Updating your workspace…</div>}
      {loading ? <div className="panel welcome"><span className="eyebrow">MARKETING INTELLIGENCE</span><h1>Opening your workspace…</h1></div> : !workspace ? <div className="welcome panel"><span className="eyebrow">LESS NOISE. MORE UNDERSTANDING.</span><h1>A clearer view of your marketing.</h1><p>Turn simple spreadsheets into a useful picture of your brand and its competitive landscape.</p><div className="workflow"><span>01 Add data</span><ArrowRight/><span>02 Understand</span><ArrowRight/><span>03 Report</span></div><form onSubmit={e => { e.preventDefault(); run(async () => { const w = await api<Workspace>('/workspaces', 'POST', { name }); setWorkspaces([...workspaces, w]); setId(w.id); setName(''); setPage('Data') }) }}><label>Your first workspace<input required maxLength={120} placeholder="e.g. Symphony brand research" value={name} onChange={e => setName(e.target.value)}/></label><button className="button primary" disabled={busy || !name.trim()}>Create workspace <ArrowRight size={16}/></button></form><small>Private to this local installation. Start with your own data or try the demo.</small></div> : page === 'Data' ? <DataPage key={`${id}-${workspace.primary_brand ?? ''}-${dataset.imports.length}`} workspace={workspace} data={dataset} busy={busy} run={run} refresh={refresh} navigate={() => setPage('Dashboard')}/> : !analysis ? <div className="panel welcome"><span className="eyebrow">LET’S BUILD YOUR PICTURE</span><h1>Your next insight starts here.</h1><p>Add a spreadsheet or explore the demo, then select a primary brand to unlock your dashboard, analysis, and reports.</p><button className="button primary" onClick={() => setPage('Data')}>Add your data <ArrowRight size={16}/></button></div> : page === 'Dashboard' ? <><div className="section-heading page-intro"><div><span className="eyebrow">THE BIG PICTURE</span><h1>A little data. A clearer direction.</h1><p>{analysis.primary_brand} <span className="dot-separator">·</span> {workspace.competitors?.length ?? 0} selected competitors</p></div><button className="button" onClick={() => setPage('Data')}><ArrowDownToLine size={16}/>Add data</button></div><div className="context-strip"><span><span className="status-dot"/>Latest available snapshot</span><span>{analysis.metrics.dates.length === 1 ? analysis.metrics.dates[0] : `${analysis.metrics.dates.length} reporting dates`} · {analysis.metrics.observations.length} observations</span>{dataset.imports.some(i => i.filename === 'DEMO_fictional_social.csv') && <b>INCLUDES FICTIONAL DEMO DATA</b>}</div><Summary data={analysis}/><div className="section-heading"><div><span className="eyebrow">BEYOND THE NUMBERS</span><h2>Key findings <span className="count">{analysis.findings.length}</span></h2><p>The signals worth your attention, backed by your data.</p></div><button className="text-button" onClick={() => setPage('Analysis')}>Explore analysis <ArrowRight size={15}/></button></div><Findings findings={analysis.findings} observations={analysis.metrics.observations}/><AudienceChart data={analysis}/><div className="report-cta"><div><span className="eyebrow">TAKE THE NEXT STEP</span><h2>Turn perspective into a plan.</h2><p>Bring your findings together in a concise, readable report.</p></div><button className="button primary" onClick={() => setPage('Reports')}>Create a report <ArrowRight size={16}/></button></div><details className="methodology"><summary>How these numbers are calculated</summary><p>{analysis.metrics.methodology}</p></details></> : page === 'Analysis' ? <AnalysisPage data={analysis}/> : <ReportsPage report={report} busy={busy} generate={() => run(async () => setReport(await api<Report>(`/workspaces/${id}/report`, 'POST')))}/>}
      <footer><span>MARKETING INTELLIGENCE</span><span>Evidence first. Better decisions follow.</span></footer>
    </main></div></div>
}
