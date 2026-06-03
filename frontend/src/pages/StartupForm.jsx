import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { getStartup, createStartup, updateStartup } from '../services/api'
import TagInput from '../components/TagInput'
import Spinner from '../components/Spinner'
import toast from 'react-hot-toast'

const CURRENT_YEAR = new Date().getFullYear()

const empty = {
  company: '', status: 'Operating', year_founded: CURRENT_YEAR,
  description: '', categories: [], founders: [], investors: [],
  funding_rounds: [], city: '', state: '', country: '',
}

export default function StartupForm() {
  const { id } = useParams()
  const navigate = useNavigate()
  const isEdit = Boolean(id)

  const [form, setForm]     = useState(empty)
  const [loading, setLoading] = useState(isEdit)
  const [saving, setSaving]   = useState(false)

  useEffect(() => {
    if (!isEdit) return
    getStartup(id)
      .then(({ data }) => setForm({
        ...data,
        city:  data.city  || '',
        state: data.state || '',
        country: data.country || '',
      }))
      .catch(() => toast.error('Could not load startup'))
      .finally(() => setLoading(false))
  }, [id])

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.company.trim())     return toast.error('Company name is required')
    if (!form.description.trim()) return toast.error('Description is required')
    setSaving(true)
    try {
      const payload = {
        ...form,
        year_founded: Number(form.year_founded),
        city:    form.city    || null,
        state:   form.state   || null,
        country: form.country || null,
      }
      if (isEdit) {
        await updateStartup(id, payload)
        toast.success('Startup updated')
        navigate(`/startups/${id}`)
      } else {
        const { data } = await createStartup(payload)
        toast.success('Startup created')
        navigate(`/startups/${data.startup_id}`)
      }
    } catch (err) {
      toast.error(err.message)
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="flex justify-center py-20"><Spinner size="lg" /></div>

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <Link to="/startups" className="text-xs text-slate-500 hover:text-slate-300 mb-2 inline-block">← Back</Link>
        <h1 className="text-2xl font-bold text-white">{isEdit ? 'Edit Startup' : 'Add Startup'}</h1>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="card p-6 space-y-4">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Basic Info</h2>
          <div>
            <label className="label">Company Name *</label>
            <input className="input" value={form.company} onChange={(e) => set('company', e.target.value)} placeholder="Acme Corp" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Status</label>
              <select className="input" value={form.status} onChange={(e) => set('status', e.target.value)}>
                <option>Operating</option><option>Exited</option><option>Dead</option><option>Unknown</option>
              </select>
            </div>
            <div>
              <label className="label">Year Founded</label>
              <input className="input" type="number" min="1900" max={CURRENT_YEAR}
                value={form.year_founded} onChange={(e) => set('year_founded', e.target.value)} />
            </div>
          </div>
          <div>
            <label className="label">Description *</label>
            <textarea className="input resize-none" rows={4} value={form.description}
              onChange={(e) => set('description', e.target.value)} placeholder="What does this startup do?" />
          </div>
        </div>

        <div className="card p-6 space-y-4">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Categories</h2>
          <TagInput value={form.categories} onChange={(v) => set('categories', v)} placeholder="e.g. SaaS" />
        </div>

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
          <div>
            <label className="label">Funding Rounds</label>
            <TagInput value={form.funding_rounds} onChange={(v) => set('funding_rounds', v)} placeholder="e.g. $1,000,000" />
          </div>
        </div>

        <div className="card p-6 space-y-4">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Location</h2>
          <div className="grid grid-cols-3 gap-4">
            <div><label className="label">City</label><input className="input" value={form.city} onChange={(e) => set('city', e.target.value)} placeholder="San Francisco" /></div>
            <div><label className="label">State</label><input className="input" value={form.state} onChange={(e) => set('state', e.target.value)} placeholder="California" /></div>
            <div><label className="label">Country</label><input className="input" value={form.country} onChange={(e) => set('country', e.target.value)} placeholder="USA" /></div>
          </div>
        </div>

        <div className="flex gap-3">
          <button type="submit" disabled={saving} className="btn-primary flex-1 flex items-center justify-center gap-2 py-3">
            {saving ? <><Spinner size="sm" /> Saving...</> : (isEdit ? 'Save Changes' : 'Create Startup')}
          </button>
          <Link to="/startups" className="btn-secondary text-center py-3 px-6">Cancel</Link>
        </div>
      </form>
    </div>
  )
}
