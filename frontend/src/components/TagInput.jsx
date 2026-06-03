import { useState } from 'react'

export default function TagInput({ value = [], onChange, placeholder }) {
  const [input, setInput] = useState('')

  const add = () => {
    const trimmed = input.trim()
    if (trimmed && !value.includes(trimmed)) {
      onChange([...value, trimmed])
    }
    setInput('')
  }

  const remove = (tag) => onChange(value.filter((t) => t !== tag))

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <input
          className="input flex-1"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); add() } }}
          placeholder={placeholder || 'Type and press Enter'}
        />
        <button type="button" onClick={add} className="btn-secondary px-4 py-2 text-sm">
          Add
        </button>
      </div>
      {value.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {value.map((tag) => (
            <span key={tag} className="inline-flex items-center gap-1.5 bg-brand-500/20 text-brand-300 border border-brand-500/30 text-xs font-medium px-3 py-1 rounded-full">
              {tag}
              <button type="button" onClick={() => remove(tag)} className="hover:text-white transition-colors">×</button>
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
