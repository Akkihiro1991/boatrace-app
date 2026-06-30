import WindBadge from './WindBadge'

const STATUS_DOT = {
  '開催中': 'bg-green-400',
  '終了':   'bg-gray-500',
  '中止':   'bg-red-500',
}

export default function VenueCard({ venue, onSelectRace }) {
  const activeRaces = venue.races.filter(r => r.status !== '終了')
  const latestRace = venue.races.find(r => r.race_no === venue.current_race) ?? venue.races[0]

  return (
    <div className="card overflow-hidden">
      {/* 場ヘッダー */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-navy-700">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${STATUS_DOT[venue.status] ?? 'bg-gray-500'}`} />
          <span className="font-bold">{venue.name}</span>
          <span className="text-gray-400 text-sm">第{venue.current_race}R</span>
        </div>
        <WindBadge wind={venue.wind} />
      </div>

      {/* レース一覧 */}
      <div className="divide-y divide-navy-700">
        {venue.races.map(race => (
          <button
            key={race.race_no}
            onClick={() => onSelectRace(venue, race)}
            className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-navy-700 transition-colors text-left"
          >
            <div className="flex items-center gap-3">
              <span className="text-sm font-bold w-6">{race.race_no}R</span>
              <span className="text-gray-400 text-xs">{race.time}</span>
              {race.status === '進行中' && (
                <span className="text-xs text-green-400 font-bold animate-pulse">LIVE</span>
              )}
              {race.status === '待機中' && (
                <span className="text-xs text-yellow-400">待機</span>
              )}
            </div>
            <div className="flex items-center gap-2 text-xs text-gray-400">
              {race.result ? (
                <span className="text-yellow-400 font-bold">{race.result.trifecta}</span>
              ) : (
                <span className="text-blue-400">展開を見る →</span>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
