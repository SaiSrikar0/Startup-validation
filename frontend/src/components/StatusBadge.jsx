export default function StatusBadge({ status }) {
  const s = (status || '').toLowerCase()
  const cls =
    s === 'operating' ? 'badge-operating' :
    s === 'exited'    ? 'badge-exited'    :
    s === 'dead'      ? 'badge-dead'      : 'badge-unknown'
  return <span className={cls}>{status || 'Unknown'}</span>
}
