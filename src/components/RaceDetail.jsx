import RacerRow from './RacerRow'
import WeatherBar from './WeatherBar'
import ScenarioCard from './ScenarioCard'

const STATUS_CONFIG = {
  '終了':   { color: 'text-gray-500' },
  '進行中': { color: 'text-green-400 animate-pulse' },
  '待機中': { color: 'text-yellow-400' },
  '中止':   { color: 'text-red-400' },
}

export default function RaceDetail({ race, venue, onClose }) {
  const status = STATUS_CONFIG[race.status] ?? { color: 'text-gray-400' }

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-navy-900">
      {/* ヘッダー */}
      <div className="flex items-center gap-3 p-4 border-b border-navy-700">
        <button onClick={onClose} className="text-gray-400 text-2xl leading-none">←</button>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-bold">{venue?.name}</span>
            <span className="font-bold">{race.race_no}R</span>
            <span className="text-gray-400 text-sm">{race.time}</span>
            <span className={`text-xs font-bold ${status.color}`}>{race.status}</span>
          </div>
          <div className="mt-1">
            <WeatherBar
              wind={venue?.wind}
              weather={venue?.weather}
              airTemp={venue?.air_temp}
              waterTemp={venue?.water_temp}
            />
          </div>
        </div>
      </div>

      {/* コンテンツ */}
      <div className="flex-1 overflow-y-auto p-4">
        {/* 展開シナリオ */}
        <ScenarioCard racers={race.racers} wind={venue?.wind} />

        {/* 出走表 */}
        <div className="card p-2 mb-4">
          <div className="text-xs text-gray-500 px-2 pb-2">タップで詳細コース成績を表示</div>
          {race.racers.map(racer => (
            <RacerRow key={racer.lane} racer={racer} />
          ))}
        </div>

        {/* 結果 */}
        {race.result && (
          <div className="card p-4 mb-4">
            <div className="text-xs text-gray-400 mb-2">確定結果</div>
            <div className="text-lg font-bold text-yellow-400">{race.result.trifecta}</div>
            <div className="text-sm text-gray-300">{race.result.payout?.toLocaleString()}円</div>
          </div>
        )}

        {/* OC誘導バナー */}
        <a
          href="https://line.me/ti/g2/ourboat"
          target="_blank"
          rel="noopener noreferrer"
          className="block card p-4 border-blue-600 bg-blue-900/30 text-center"
        >
          <div className="text-lg mb-1">💬 みんなの予想はOCで</div>
          <div className="text-blue-300 text-sm">LINEオープンチャット「ボートレース展開予想部」</div>
          <div className="mt-2 bg-blue-600 text-white text-sm py-1.5 rounded-lg font-bold">
            参加する（無料）
          </div>
        </a>
      </div>
    </div>
  )
}
