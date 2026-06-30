const LANE_COLOR = {
  1: 'bg-white text-black',
  2: 'bg-gray-800 text-white border border-gray-500',
  3: 'bg-red-600 text-white',
  4: 'bg-blue-600 text-white',
  5: 'bg-yellow-500 text-black',
  6: 'bg-green-600 text-white',
}

const PLACE_STYLE = {
  '1': 'text-yellow-400 font-bold',
  '2': 'text-gray-300 font-bold',
  '3': 'text-orange-400 font-bold',
  'F': 'text-red-500 font-bold',
  'L': 'text-red-700 font-bold',
  'K': 'text-purple-400 font-bold',
}

function placeStyle(place) {
  return PLACE_STYLE[String(place)] ?? 'text-gray-500'
}

function placeLabel(place) {
  const s = String(place)
  if (['F','L','K'].includes(s)) return s
  return `${s}着`
}

export default function RecentResults({ results }) {
  if (!results?.length) return null

  const isNew = results[0] && typeof results[0] === 'object' && 'course' in results[0]

  return (
    <div className="flex items-center gap-1.5 flex-wrap">
      <span className="text-gray-500 text-xs">直近</span>
      {results.slice(0, 6).map((r, i) => {
        const course = isNew ? r.course : null
        const place  = isNew ? String(r.place) : String(r)
        return (
          <span key={i} className="inline-flex items-center gap-0.5">
            {course && (
              <span className={`w-4 h-4 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${LANE_COLOR[course] ?? 'bg-gray-600 text-white'}`}>
                {course}
              </span>
            )}
            <span className={`text-xs ${placeStyle(place)}`}>
              {placeLabel(place)}
            </span>
          </span>
        )
      })}
    </div>
  )
}
