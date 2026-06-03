import { useState } from 'react'
import { analyzeCompetition } from '../services/api'
import TagInput from '../components/TagInput'
import Spinner from '../components/Spinner'
import StatusBadge from '../components/StatusBadge'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'

const initialForm = {
  company: '',
  categories: [],
  city: '',
  state: '',
  country: '',
  top_n: 5,
}

function ScoreBar({ score }) {
  const pct = Math.round(score * 100)
  const color = pct >= 70 ? 'bg-red-500' : pct >= 40 ? 'bg-amber-500' : 'bg-emerald-500'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-400 w-8 text-right">{pct}%</span>
    </div>
  )
}

export default function Compete() {
  const [form, setForm]     = useState(initialForm)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.company.trim())     return toast.error('Company name is required')
    if (!form.categories.length)  return toast.error('Add at least one category')
    setLoading(true); setResult(null)
    try {
      const { data } = await analyzeCompetition({
        company:    form.company,
        categories: form.categories,
        city:       form.city    || undefined,
        state:      form.state   || undefined,
        country:    form.country || undefined,
        top_n:      Number(form.top_n),
      })
      setResult(data)
    } catch (err) {
      toast.error(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Competition Analysis</h1>
        <p className="text-slate-400 text-sm mt-1">Find your closest competitors using ML clustering & cosine similarity on 600+ real startups.</p>
      </div>

      <div className="grid lg:grid-cols-5 gap-8">
        {/* Form */}
        <form onSubmit={handleSubmit} className="lg:col-span-2 space-y-5">
          <div className="card p-6 space-y-4">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Your Startup</h2>
            <div>
              <label className="label">Company Name *</label>
              <input className="input" placeholder="e.g. Acme Corp" value={form.company}
                onChange={(e) => set('company', e.target.value)} />
            </div>
            <div>
              <label className="label">Categories *</label>
              <TagInput value={form.categories} onChange={(v) => set('categories', v)} placeholder="e.g. SaaS" />
            </div>
          </div>

          <div className="card p-6 space-y-4">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Location (optional)</h2>
            <div>
              <label className="label">City</label>
              <input className="input" placeholder="San Francisco" value={form.city} onChange={(e) => set('city', e.target.value)} />
            </div>
            <div>
              <label className="label">State</label>
              <input className="input" placeholder="California" value={form.state} onChange={(e) => set('state', e.target.value)} />
            </div>
            <div>
              <label className="label">Country</label>
              <input className="input" placeholder="USA" value={form.country} onChange={(e) => set('country', e.target.value)} />
            </div>
          </div>

          <div className="card p-6 space-y-4">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Options</h2>
            <div>
              <label className="label">Top N results</label>
              <select className="input" value={form.top_n} onChange={(e) => set('top_n', e.target.value)}>
                {[3,5,8,10].map(n => <option key={n} value={n}>{n} competitors</option>)}
              </select>
            </div>
          </div>

          <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2 py-3">
            {loading ? <><Spinner size="sm" /> Searching...</> : '⚔️ Find Competitors'}
          </button>
        </form>

        {/* Results */}
        <div className="lg:col-span-3">
          {!result && !loading && (
            <div className="card p-10 flex flex-col items-center justify-center text-center gap-3 min-h-72">
              <div className="text-5xl">⚔️</div>
              <p className="text-slate-400 text-sm">Enter your company's info to discover who you're competing with.</p>
            </div>
          )}

          {loading && (
            <div className="card p-10 flex flex-col items-center justify-center gap-4 min-h-72">
              <Spinner size="lg" />
              <p className="text-slate-400 text-sm">Searching the database...</p>
            </div>
          )}

          {result && (
            <div className="space-y-4">
              <div className="card p-4 flex items-center justify-between">
                <div>
                  <p className="text-white font-semibold">{result.company}</p>
                  <p className="text-slate-400 text-xs mt-0.5">{result.total_candidates} total candidates found</p>
                </div>
                <span className="text-2xl">⚔️</span>
              </div>

              {result.top_matches.length === 0 ? (
                <div className="card p-8 text-center text-slate-400">
                  No competitors found. Try adding more categories or broadening your search.
                </div>
              ) : (
                result.top_matches.map((match, i) => (
                  <div key={match.startup_id} className="card p-5 hover:border-slate-700 transition-colors">
                    <div className="flex items-start justify-between gap-4 mb-3">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-bold text-slate-400">
                          #{i + 1}
                        </div>
                        <div>
                          <Link to={`/startups/${match.startup_id}`} className="font-semibold text-white hover:text-brand-400 transition-colors">
                            {match.company}
                          </Link>
                        </div>
                      </div>
                    </div>

                    <div className="mb-3">
                      <p className="text-xs text-slate-500 mb-1">Similarity score</p>
                      <ScoreBar score={match.score} />
                    </div>

                    {match.shared_categories.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mb-3">
                        {match.shared_categories.map(c => (
                          <span key={c} className="text-xs bg-brand-500/10 text-brand-400 border border-brand-500/20 px-2 py-0.5 rounded-full">{c}</span>
                        ))}
                      </div>
                    )}

                    <ul className="space-y-1">
                      {match.reasoning.map((r, j) => (
                        <li key={j} className="text-xs text-slate-400 flex items-center gap-1.5">
                          <span className="text-slate-600">—</span> {r}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
