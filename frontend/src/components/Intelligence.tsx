import { ArrowUpRight, ChartNoAxesCombined, CircleHelp, Flag, Layers3, Users } from 'lucide-react'
import type { Finding, Intelligence, Observation } from '../types'

export const number = (value: number | null | undefined) => value == null ? '—' : new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value)
export const rate = (value: number | null | undefined) => value == null ? '—' : `${value.toFixed(2)}%`

export function Summary({ data }: { data: Intelligence }) {
  const m = data.metrics
  const items = [
    { label: 'Audience size', value: number(m.audience), detail: `${m.coverage.follower_platforms} platforms · audiences may overlap`, icon: Users },
    { label: 'Engagement rate', value: rate(m.engagement_rate), detail: `Unweighted average · ${m.coverage.rate_platforms} platforms`, icon: ChartNoAxesCombined },
    { label: 'Highest engagement', value: m.best_platform ?? '—', detail: 'By available platform engagement rate', icon: Layers3 },
    { label: 'Competitive position', value: m.leading_platforms == null ? '—' : `${m.leading_platforms} of ${m.ranked_platforms}`, detail: 'Platforms ranked first · ties included', icon: Flag },
  ]
  return <div className="metric-grid">{items.map(item => <article className="metric-card" key={item.label}><div className="metric-label">{item.label}<item.icon size={17} /></div><div className="metric-value">{item.value}</div><p>{item.detail}</p></article>)}</div>
}

export function Findings({ findings, observations }: { findings: Finding[]; observations: Observation[] }) {
  return <div className="findings">{findings.length ? findings.map(f => <article className={`finding ${f.type.toLowerCase()}`} key={f.title}>
    <div className="finding-top"><span className="tag"><span />{f.type}</span><span className="confidence">{f.confidence} confidence</span></div>
    <h3>{f.title}</h3><p>{f.summary}</p>
    <details><summary>View evidence <ArrowUpRight size={14} /></summary><div className="evidence"><p>Your audience: <b>{number(f.evidence.followers)}</b><br/>Competitor average: <b>{number(f.evidence.competitor_average)}</b><br/>Your engagement: <b>{rate(f.evidence.engagement_rate)}</b><br/>Competitor engagement: <b>{rate(f.evidence.competitor_engagement_rate)}</b></p><p>Reporting dates: {f.evidence.dates.join(', ') || 'Not provided'}</p>{observations.filter(r => f.source_metrics.includes(r.id)).map(r => <p key={r.id}>#{r.id} · {r.brand} · {r.source}, row {r.source_row}</p>)}</div></details>
  </article>) : <div className="empty-inline"><CircleHelp size={22}/><p>No finding rules triggered. Add comparable observations to build a stronger picture.</p></div>}</div>
}

export function AudienceChart({ data }: { data: Intelligence }) {
  const totals = new Map<string, { total: number; count: number }>()
  data.metrics.observations.forEach(r => { if (r.followers != null) { const old = totals.get(r.brand) ?? { total: 0, count: 0 }; totals.set(r.brand, { total: old.total + r.followers, count: old.count + 1 }) } })
  const sorted = [...totals].sort((a, b) => b[1].total - a[1].total)
  const max = Math.max(...sorted.map(([, v]) => v.total), 1)
  return <section className="panel"><div className="section-heading"><div><h2>Audience landscape</h2><p>How your measured audience compares</p></div><span className="subtle">Followers</span></div><div className="bar-chart">{sorted.length ? sorted.map(([brand, value]) => <div className="bar-row" key={brand}><div className="bar-label"><span>{brand}{brand === data.primary_brand && <em>You</em>}</span><b>{number(value.total)}</b></div><div className="bar-track"><div className={brand === data.primary_brand ? 'bar primary' : 'bar'} style={{ width: `${value.total / max * 100}%` }} /></div><small>{value.count} measured platforms</small></div>) : <p>No follower data available.</p>}</div><p className="chart-note">Totals use available data. Platform coverage may differ; these are not like-for-like audience ranks.</p></section>
}
