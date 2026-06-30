import { useState } from 'react'
import MotorBadge from './MotorBadge'
import StyleBadge from './StyleBadge'
import RankBadge from './RankBadge'
import RecentResults from './RecentResults'
import CourseStats from './CourseStats'

const LANE_COLORS = {
  1: 'bg-white text-black',
  2: 'bg-gray-900 text-white border border-gray-600',
  3: 'bg-red-600 text-white',
  4: 'bg-blue-600 text-white',
  5: 'bg-yellow-500 text-black',
  6: 'bg-green-600 text-white',
}

export default function RacerRow({ racer }) {
  const [expanded, setExpanded] = useState(false)
  const isLocal = racer.local_rate > 50
  const hasFlying = racer.flying > 0
  const tSharp = racer.tenji_st !== undefined && racer.tenji_st !== null && racer.tenji_st <= 0.05
  const tFast = racer.tenji_time && racer.tenji_time <= 6.80

  return (
    <div className="border-b border-navy-700 last:border-0">
      <button
        className="w-full flex items-start gap-3 py-3 text-left"
        onClick={() => setExpanded(e => !e)}
      >
        {/* 枠番 */}
        <div className={`lane-dot mt-0.5 ${LANE_COLORS[racer.lane]}`}>{racer.lane}</div>

        {/* メイン情報 */}
        <div className="flex-1 min-w-0">
          {/* 1行目: 名前・ランク・スタイル・フラグ */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="font-bold text-sm">{racer.name}</span>
            <RankBadge rank={racer.rank} />
            <StyleBadge style={racer.style} />
            {racer.mae_zuke && <span className="text-pink-400 text-xs font-bold">前付</span>}
            {hasFlying && <span className="text-red-400 text-xs font-bold">F{racer.flying}</span>}
            {isLocal && <span className="text-cyan-400 text-xs">地元</span>}
          </div>

          {/* 2行目: モーター・ST */}
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            <MotorBadge rate={racer.motor_2rate} />
            <span className="text-gray-400 text-xs">
              ST <span className={racer.st_avg <= 0.15 ? 'text-green-400 font-bold' : 'text-gray-300'}>
                {racer.st_avg?.toFixed(2)}
              </span>
            </span>
            {racer.tenji_time && (
              <span className={`text-xs ${tFast ? 'text-yellow-400 font-bold' : 'text-gray-400'}`}>
                展示{racer.tenji_time}秒
              </span>
            )}
            {racer.tenji_st !== undefined && racer.tenji_st !== null && (
              <span className={`text-xs ${tSharp ? 'text-green-400 font-bold' : 'text-gray-400'}`}>
                展ST{racer.tenji_st?.toFixed(2)}
              </span>
            )}
          </div>

          {/* 3行目: 直近成績 */}
          <div className="mt-1.5">
            <RecentResults results={racer.recent_results} />
          </div>
        </div>

        {/* 右: 今節コース勝率 */}
        <div className="text-right flex-shrink-0">
          <div className="text-xs text-gray-400">{racer.lane}コース</div>
          <div className={`text-sm font-bold ${
            (racer.course_detail?.[racer.lane]?.win ?? racer.course_stats?.[racer.lane] ?? 0) >= 60
              ? 'text-yellow-400'
              : (racer.course_detail?.[racer.lane]?.win ?? racer.course_stats?.[racer.lane] ?? 0) >= 45
              ? 'text-blue-300'
              : 'text-gray-400'
          }`}>
            {(racer.course_detail?.[String(racer.lane)]?.win ?? racer.course_stats?.[String(racer.lane)] ?? 0).toFixed(1)}%
          </div>
          <div className="text-gray-500 text-xs">当地{racer.local_rate?.toFixed(0)}%</div>
          <div className="text-gray-600 text-xs mt-1">{expanded ? '▲' : '▼'}</div>
        </div>
      </button>

      {/* 展開: コース詳細 */}
      {expanded && (
        <div className="pb-3 pl-8 pr-2">
          <CourseStats courseDetail={racer.course_detail} assignedLane={racer.lane} />
        </div>
      )}
    </div>
  )
}
