const STYLE_CONFIG = {
  '逃げ':      { color: 'bg-blue-600', short: '逃' },
  '差し':      { color: 'bg-green-600', short: '差' },
  'まくり':    { color: 'bg-orange-600', short: '捲' },
  'まくり差し': { color: 'bg-purple-600', short: '捲差' },
  '差し・まくり差し': { color: 'bg-teal-600', short: '差捲' },
}

export default function StyleBadge({ style }) {
  const config = STYLE_CONFIG[style] ?? { color: 'bg-gray-600', short: style?.[0] ?? '?' }
  return (
    <span className={`${config.color} text-white text-xs px-1.5 py-0.5 rounded font-bold`}>
      {config.short}
    </span>
  )
}
