const BADGE = {
  '1': { bg: 'bg-yellow-400', text: 'text-black', label: '1着' },
  '2': { bg: 'bg-gray-300',   text: 'text-black', label: '2着' },
  '3': { bg: 'bg-orange-500', text: 'text-white', label: '3着' },
  'F': { bg: 'bg-red-600',    text: 'text-white', label: 'F'   },
  'L': { bg: 'bg-red-800',    text: 'text-white', label: 'L'   },
  'K': { bg: 'bg-purple-700', text: 'text-white', label: 'K'   },
}

function getBadge(result) {
  if (BADGE[result]) return BADGE[result]
  const n = parseInt(result)
  if (!isNaN(n) && n >= 4) return { bg: 'bg-navy-700', text: 'text-gray-400', label: `${n}着` }
  return { bg: 'bg-gray-700', text: 'text-gray-400', label: result }
}

export default function RecentResults({ results }) {
  if (!results?.length) return null
  return (
    <div className="flex items-center gap-1">
      <span className="text-gray-500 text-xs mr-0.5">直近</span>
      {results.slice(0, 6).map((r, i) => {
        const b = getBadge(String(r))
        return (
          <span
            key={i}
            className={`inline-flex items-center justify-center text-xs font-bold px-1.5 py-0.5 rounded ${b.bg} ${b.text}`}
          >
            {b.label}
          </span>
        )
      })}
    </div>
  )
}
