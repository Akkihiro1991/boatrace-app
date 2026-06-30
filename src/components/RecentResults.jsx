const DOT = {
  '1': { bg: 'bg-yellow-400', text: 'text-black', label: '1' },
  '2': { bg: 'bg-gray-300', text: 'text-black', label: '2' },
  '3': { bg: 'bg-orange-600', text: 'text-white', label: '3' },
  'F': { bg: 'bg-red-600', text: 'text-white', label: 'F' },
  'L': { bg: 'bg-red-800', text: 'text-white', label: 'L' },
  'K': { bg: 'bg-purple-700', text: 'text-white', label: 'K' },
}

function getDot(result) {
  if (DOT[result]) return DOT[result]
  const n = parseInt(result)
  if (!isNaN(n) && n >= 4) return { bg: 'bg-navy-700', text: 'text-gray-400', label: result }
  return { bg: 'bg-gray-700', text: 'text-gray-400', label: result }
}

export default function RecentResults({ results }) {
  if (!results?.length) return null
  return (
    <div className="flex items-center gap-1">
      <span className="text-gray-500 text-xs mr-0.5">直近</span>
      {results.slice(0, 6).map((r, i) => {
        const dot = getDot(String(r))
        return (
          <span
            key={i}
            className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${dot.bg} ${dot.text}`}
          >
            {dot.label}
          </span>
        )
      })}
    </div>
  )
}
