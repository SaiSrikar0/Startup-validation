import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import useStartupStore from '../store/useStartupStore'
import StatusBadge from '../components/StatusBadge'
import Spinner from '../components/Spinner'
import toast from 'react-hot-toast'

export default function Startups() {
  const { startups, total, loading, error, filters, setFilters, setOffset, fetchStartups, deleteStartup } = useStartupStore()
  const [search, setSearch] = useState({ status: '', category: '', country: '' })
  const [deleting, setDeleting] = useState(null)

  useEffect(() => { fetchStartups() }, [filters])

  const applyFilters = (e) => {
    e.preventDefault()
    setFilters(search)
  }

  const clearFilters = () => {
    const empty = { status: '', category: '', country: '' }
    setSearch(empty)
    setFilters(empty)
  }

  const handleDelete = async (id, name) => {
    if (!confirm(`Delete "${name}"?`)) return
    setDeleting(id)
    try {
      await deleteStartup(id)
      toast.success(`"${name}" deleted`)
    } catch (e) {
      toast.error(e.message)
    } finally {
      setDeleting(null)
    }
  }

  const totalPages = Math.ceil(total / filters.limit)
  const currentPage = Math.floor(filters.offset / filters.limit) + 1

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Startups</h1>
          <p className="text-slate-400 text-sm mt-1">{total.toLocaleString()} total companies</p>
        </div>
        <Link to="/startups/new" className="btn-primary text-sm">+ Add Startup</Link>
      </div>

      {/* Filters */}
      <form onSubmit={applyFilters} className="card p-4 flex flex-wrap gap-3 items-end">
        <div className="flex-1 min-w-36">
          <label className="label text-xs">Status</label>
          <select className="input py-2 text-sm" value={search.status} onChange={(e) => setSearch(s => ({ ...s, status: e.target.value }))}>
            <option value="">All statuses</option>
            <option value="Operating">Operating</option>
            <option value="Exited">Exited</option>
            <option value="Dead">Dead</option>
          </select>
        </div>
        <div className="flex-1 min-w-36">
          <label className="label text-xs">Category</label>
          <input className="input py-2 text-sm" placeholder="e.g. SaaS" value={search.category}
            onChange={(e) => setSearch(s => ({ ...s, category: e.target.value }))} />
        </div>
        <div className="flex-1 min-w-36">
          <label className="label text-xs">Country</label>
          <input className="input py-2 text-sm" placeholder="e.g. USA" value={search.country}
            onChange={(e) => setSearch(s => ({ ...s, country: e.target.value }))} />
        </div>
        <div className="flex gap-2">
          <button type="submit" className="btn-primary py-2 text-sm">Search</button>
          <button type="button" onClick={clearFilters} className="btn-secondary py-2 text-sm">Clear</button>
        </div>
      </form>

      {/* Table */}
      {loading ? (
        <div className="card p-16 flex justify-center"><Spinner size="lg" /></div>
      ) : error ? (
        <div className="card p-8 text-center text-red-400">{error}</div>
      ) : startups.length === 0 ? (
        <div className="card p-12 text-center text-slate-400">No startups found.</div>
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800 text-left">
                  <th className="px-5 py-3.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">Company</th>
                  <th className="px-5 py-3.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">Status</th>
                  <th className="px-5 py-3.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">Founded</th>
                  <th className="px-5 py-3.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">Categories</th>
                  <th className="px-5 py-3.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">Location</th>
                  <th className="px-5 py-3.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {startups.map((s) => (
                  <tr key={s.startup_id} className="hover:bg-slate-800/30 transition-colors group">
                    <td className="px-5 py-4">
                      <Link to={`/startups/${s.startup_id}`} className="font-medium text-white hover:text-brand-400 transition-colors">
                        {s.company}
                      </Link>
                    </td>
                    <td className="px-5 py-4"><StatusBadge status={s.status} /></td>
                    <td className="px-5 py-4 text-slate-400">{s.year_founded}</td>
                    <td className="px-5 py-4">
                      <div className="flex flex-wrap gap-1 max-w-xs">
                        {s.categories.slice(0, 3).map(c => (
                          <span key={c} className="text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded">{c}</span>
                        ))}
                        {s.categories.length > 3 && (
                          <span className="text-xs text-slate-600">+{s.categories.length - 3}</span>
                        )}
                      </div>
                    </td>
                    <td className="px-5 py-4 text-slate-400 text-xs">
                      {[s.city, s.country].filter(Boolean).join(', ') || '—'}
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <Link to={`/startups/${s.startup_id}`} className="text-xs text-brand-400 hover:underline">View</Link>
                        <Link to={`/startups/${s.startup_id}/edit`} className="text-xs text-slate-400 hover:text-white">Edit</Link>
                        <button onClick={() => handleDelete(s.startup_id, s.company)}
                          disabled={deleting === s.startup_id}
                          className="text-xs text-red-400 hover:text-red-300 disabled:opacity-50">
                          {deleting === s.startup_id ? '...' : 'Delete'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="px-5 py-4 border-t border-slate-800 flex items-center justify-between">
              <p className="text-xs text-slate-500">
                Showing {filters.offset + 1}–{Math.min(filters.offset + filters.limit, total)} of {total}
              </p>
              <div className="flex items-center gap-2">
                <button onClick={() => setOffset(Math.max(0, filters.offset - filters.limit))}
                  disabled={currentPage === 1}
                  className="btn-secondary py-1.5 px-3 text-xs disabled:opacity-40">← Prev</button>
                <span className="text-xs text-slate-400">Page {currentPage} / {totalPages}</span>
                <button onClick={() => setOffset(filters.offset + filters.limit)}
                  disabled={currentPage === totalPages}
                  className="btn-secondary py-1.5 px-3 text-xs disabled:opacity-40">Next →</button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
