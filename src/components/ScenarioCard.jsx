import { generateScenario } from '../utils/scenario'

export default function ScenarioCard({ racers, wind }) {
  const { main, risks, keyRacer } = generateScenario(racers, wind)

  return (
    <div className="card p-4 mb-4">
      <div className="text-xs text-gray-400 mb-3 font-bold tracking-wide">⚡ 展開シナリオ</div>

      {/* 有力展開 */}
      <div className="mb-3">
        <div className="text-xs text-blue-400 mb-1.5">有力展開</div>
        <ul className="space-y-1.5">
          {main.map((s, i) => (
            <li key={i} className="text-sm flex gap-2">
              <span className="text-blue-500 flex-shrink-0">▶</span>
              <span>{s}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* 波乱要素 */}
      {risks.length > 0 && (
        <div className="mb-3 pt-3 border-t border-navy-700">
          <div className="text-xs text-orange-400 mb-1.5">⚠ 波乱要素</div>
          <ul className="space-y-1.5">
            {risks.map((r, i) => (
              <li key={i} className="text-sm flex gap-2">
                <span className="text-orange-500 flex-shrink-0">!</span>
                <span className="text-gray-300">{r}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* キーマン */}
      {keyRacer && (
        <div className="pt-3 border-t border-navy-700">
          <div className="text-xs text-yellow-400 mb-1">🔑 機力キーマン</div>
          <div className="text-sm">
            {keyRacer.lane}号艇・<span className="font-bold">{keyRacer.name}</span>
            <span className="text-gray-400 ml-1">（モーター{keyRacer.motor_2rate}%）</span>
          </div>
        </div>
      )}
    </div>
  )
}
