import { useState } from 'react'
import { predictSuccess } from '../services/api'
import TagInput from '../components/TagInput'
import Spinner from '../components/Spinner'
import toast from 'react-hot-toast'

const CURRENT_YEAR = new Date().getFullYear()

const initialForm = {
  company: '',
  status: 'Operating',
  year_founded: CURRENT_YEAR,
  description: '',
  categories: [],
  founders: [],
  investors: [],
  country: '',
  state: '',
  city: '',
}

function ScoreGauge({ probability }) {
  const pct = Math.round(probability * 100)
  const color = pct >= 70 ? '#22c55e' : pct >= 50 ? '#f59e0b' : '#ef4444'
  const r = 54
  const circ = 2 * Math.PI * r
  const dash = circ * (pct / 100)

  return (
    <div className="flex flex-col items-center gap-2">
      <svg width="140" height="140" viewBox="0 0 140 140">
        <circle cx="70" cy="70" r={r} fill="none" stroke="#1e293b" strokeWidth="12" />
        <circle
          cx="70" cy="70" r={r} fill="none"
          stroke={color} strokeWidth="12"
          strokeDasharray={`${dash} ${circ}`}
          strokeLinecap="round"
          transform="rotate(-90 70 70)"
          style={{ transition: 'stroke-dasharray 1s ease' }}
        />
        <text x="70" y="66" textAnchor="middle" fill="white" fontSize="26" fontWeight="700">{pct}%</text>
        <text x="70" y="86" textAnchor="middle" fill="#94a3b8" fontSize="11">probability</text>
      </svg>
    </div>
  )
}

export default function Predict() {
  const [form, setForm]   = useState(initialForm)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.company.trim()) return toast.error('Company name is required')
    setLoading(true)
    setResult(null)
    try {
      const payload = {
        company:      form.company,
        status:       form.status,
        year_founded: Number(form.year_founded),
        description:  form.description,
        categories:   form.categories,
        founders:     form.founders,
        investors:    form.investors,
        country:      form.country || undefined,
        state:        form.state   || undefined,
        city:         form.city    || undefined,
      }
      const { data } = await predictSuccess(payload)
      setResult(data)
    } catch (err) {
      toast.error(err.message)
    } finally {
      setLoading(false)
    }
  }

  const confidenceColor = (c) =>
    c === 'high' ? 'text-emerald-400' : c === 'medium' ? 'text-amber-400' : 'text-red-400'

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Success Prediction</h1>
        <p className="text-slate-400 text-sm mt-1">Fill in your startup's profile and get an AI-powered success score.</p>
      </div>

      <div className="grid lg:grid-cols-5 gap-8">
        {/* Form */}
        <form onSubmit={handleSubmit} className="lg:col-span-3 space-y-6">
          {/* Basic info */}
          <div className="card p-6 space-y-4">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Basic Info</h2>

            <div>
              <label className="label">Company Name *</label>
              <input className="input" placeholder="e.g. Acme Corp" value={form.company}
                onChange={(e) => set('company', e.target.value)} />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">Status</label>
                <select className="input" value={form.status} onChange={(e) => set('status', e.target.value)}>
                  <option>Operating</option>
                  <option>Exited</option>
                  <option>Dead</option>
                  <option>Unknown</option>
                </select>
              </div>
              <div>
                <label className="label">Year Founded</label>
                <input className="input" type="number" min="1900" max={CURRENT_YEAR}
                  value={form.year_founded} onChange={(e) => set('year_founded', e.target.value)} />
              </div>
            </div>

            <div>
              <label className="label">Description</label>
              <textarea className="input resize-none" rows={3}
                placeholder="What does your startup do?"
                value={form.description} onChange={(e) => set('description', e.target.value)} />
            </div>
          </div>

          {/* Categories */}
          <div className="card p-6 space-y-4">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Categories</h2>
            <p className="text-slate-500 text-xs">Add the markets / industries your startup operates in.</p>
            <TagInput value={form.categories} onChange={(v) => set('categories', v)} placeholder="e.g. SaaS" />
          </div>

          {/* Team */}
          <div className="card p-6 space-y-4">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Team & Investors</h2>
            <div>
              <label className="label">Founders</label>
              <TagInput value={form.founders} onChange={(v) => set('founders', v)} placeholder="e.g. Jane Doe" />
            </div>
            <div>
              <label className="label">Investors</label>
              <TagInput value={form.investors} onChange={(v) => set('investors', v)} placeholder="e.g. Y Combinator" />
            </div>
          </div>

          {/* Location */}
          <div className="card p-6 space-y-4">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Location</h2>
            <div className="grid grid-cols-3 gap-4">
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
          </div>

          <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2 py-3">
            {loading ? <><Spinner size="sm" /> Analyzing...</> : '🚀 Predict Success'}
          </button>
        </form>

        {/* Result panel */}
        <div className="lg:col-span-2 space-y-4">
          {!result && !loading && (
            <div className="card p-8 flex flex-col items-center justify-center text-center gap-3 min-h-64">
              <div className="text-5xl">🎯</div>
              <p className="text-slate-400 text-sm">Fill in the form and hit<br /><strong className="text-white">Predict Success</strong> to see your score.</p>
            </div>
          )}

          {loading && (
            <div className="card p-8 flex flex-col items-center justify-center gap-4 min-h-64">
              <Spinner size="lg" />
              <p className="text-slate-400 text-sm">Analyzing your startup...</p>
            </div>
          )}

          {result && (
            <div className="space-y-4">
              {/* Main verdict */}
              <div className={`card p-6 border-2 ${result.predicted_success ? 'border-emerald-500/40 bg-emerald-950/20' : 'border-red-500/40 bg-red-950/20'}`}>
                <div className="flex flex-col items-center text-center gap-4">
                  <ScoreGauge probability={result.probability} />
                  <div>
                    <div className={`text-2xl font-extrabold mb-1 ${result.predicted_success ? 'text-emerald-400' : 'text-red-400'}`}>
                      {result.predicted_success ? '✅ Likely to Succeed' : '⚠️ At Risk'}
                    </div>
                    <p className="text-slate-300 font-medium text-sm">{result.company}</p>
                    <p className="text-slate-500 text-xs mt-1">
                      Confidence: <span className={`font-semibold ${confidenceColor(result.confidence)}`}>{result.confidence}</span>
                      {result.model_name && (
                        <span className="block mt-1 text-slate-600">Model: {result.model_name}</span>
                      )}
                    </p>
                  </div>
                </div>
              </div>

              {/* Factors */}
              <div className="card p-5">
                <h3 className="text-sm font-semibold text-slate-300 mb-3">Key Factors</h3>
                <ul className="space-y-2">
                  {result.factors.map((f, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                      <span className="text-brand-400 mt-0.5 shrink-0">◆</span>
                      {f}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Score bar */}
              <div className="card p-5">
                <div className="flex justify-between text-xs text-slate-400 mb-2">
                  <span>Score</span>
                  <span>{Math.round(result.probability * 100)}% / 100%</span>
                </div>
                <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-1000 ${result.predicted_success ? 'bg-emerald-500' : result.probability >= 0.35 ? 'bg-amber-500' : 'bg-red-500'}`}
                    style={{ width: `${result.probability * 100}%` }}
                  />
                </div>
                <div className="flex justify-between text-xs text-slate-600 mt-1.5">
                  <span>0%</span><span>50% threshold</span><span>100%</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
