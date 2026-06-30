import MotorBadge from './MotorBadge'
import StyleBadge from './StyleBadge'
import RankBadge from './RankBadge'

const LANE_COLORS = {
  1: 'bg-white text-black',
  2: 'bg-gray-900 text-white border border-gray-600',
  3: 'bg-red-600 text-white',
  4: 'bg-blue-600 text-white',
  5: 'bg-yellow-500 text-black',
  6: 'bg-green-600 text-white',
}

export default function RacerRow({ racer }) {
  const courseRate = racer.course_stats?.[String(racer.lane)] ?? 0
  const isLocal = racer.local_rate > 50
  const hasFlying = racer.flying > 0

  return (
    <div className="flex items-start gap-3 py-3 border-b border-navy-700 last:border-0">
      {/* 枠番 */}
      <div className={`lane-dot ${LANE_COLORS[racer.lane]}`}>
        {racer.lane}
      </div>

      {/* 選手情報 */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="font-bold text-sm">{racer.name}</span>
          <RankBadge rank={racer.rank} />
          <StyleBadge style={racer.style} />
          {hasFlying && <span className="text-red-400 text-xs font-bold">F{racer.flying}</span>}
          {isLocal && <span className="text-cyan-400 text-xs">地元</span>}
        </div>
        <div className="flex items-center gap-2 mt-1 flex-wrap">
          <MotorBadge rate={racer.motor_2rate} />
          <span className="text-gray-400 text-xs">
            ST平均 <span className={racer.st_avg <= 0.15 ? 'text-green-400 font-bold' : 'text-gray-300'}>
              {racer.st_avg.toFixed(2)}
            </span>
          </span>
        </div>
      </div>

      {/* コース勝率 */}
      <div className="text-right flex-shrink-0">
        <div className="text-xs text-gray-400">{racer.lane}コース</div>
        <div className={`text-sm font-bold ${courseRate >= 60 ? 'text-yellow-400' : courseRate >= 45 ? 'text-blue-300' : 'text-gray-400'}`}>
          {courseRate.toFixed(1)}%
        </div>
        <div className="text-xs text-gray-500">当地{racer.local_rate.toFixed(0)}%</div>
      </div>
    </div>
  )
}
