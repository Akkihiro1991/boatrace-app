import { getVenueData, getInRateLabel, getSurfaceColor } from '../data/venues'

const WATER_COLOR = {
  '淡水': 'text-blue-300',
  '海水': 'text-cyan-400',
  '汽水': 'text-teal-400',
  '河川（汽水）': 'text-teal-300',
  '超静水': 'text-blue-400',
}

export default function VenueInfoCard({ venueId }) {
  const v = getVenueData(venueId)
  if (!v) return null

  const inRate = getInRateLabel(v.in_rate)
  const surfaceColor = getSurfaceColor(v.surface)

  return (
    <div className="card p-4 mb-4">
      <div className="text-xs text-gray-400 mb-3 font-bold tracking-wide">🏟 場の特徴</div>

      {/* 基本ステータス */}
      <div className="grid grid-cols-3 gap-2 mb-3">
        <div className="bg-navy-700 rounded-lg p-2 text-center">
          <div className="text-xs text-gray-500 mb-0.5">水面</div>
          <div className={`text-xs font-bold ${WATER_COLOR[v.water] ?? 'text-gray-300'}`}>{v.water}</div>
        </div>
        <div className="bg-navy-700 rounded-lg p-2 text-center">
          <div className="text-xs text-gray-500 mb-0.5">イン逃げ</div>
          <div className={`text-sm font-bold ${inRate.color}`}>{v.in_rate}%</div>
          <div className={`text-xs ${inRate.color}`}>{inRate.label}</div>
        </div>
        <div className="bg-navy-700 rounded-lg p-2 text-center">
          <div className="text-xs text-gray-500 mb-0.5">水面状況</div>
          <div className={`text-xs font-bold ${surfaceColor}`}>{v.surface}</div>
        </div>
      </div>

      {/* タグ */}
      <div className="flex flex-wrap gap-1.5 mb-3">
        {v.tags.map(tag => (
          <span key={tag} className="text-xs bg-navy-700 text-gray-300 px-2 py-0.5 rounded-full">
            {tag}
          </span>
        ))}
      </div>

      {/* 説明 */}
      <p className="text-sm text-gray-300 leading-relaxed mb-3">{v.description}</p>

      {/* 予想のコツ */}
      <div>
        <div className="text-xs text-yellow-400 mb-1.5">💡 展開予想のコツ</div>
        <ul className="space-y-1">
          {v.tips.map((tip, i) => (
            <li key={i} className="text-xs text-gray-400 flex gap-1.5">
              <span className="text-yellow-600 flex-shrink-0">・</span>
              <span>{tip}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* 万舟率 */}
      <div className="mt-3 pt-3 border-t border-navy-700 flex gap-4 text-xs text-gray-500">
        <span>万舟率 <span className={v.mansen_rate >= 10 ? 'text-orange-400 font-bold' : 'text-gray-300'}>{v.mansen_rate}%</span></span>
        <span>{v.location}</span>
      </div>
    </div>
  )
}
