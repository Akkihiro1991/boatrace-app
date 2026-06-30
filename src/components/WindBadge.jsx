const DIRECTION_ARROW = {
  '北': '↓', '南': '↑', '東': '←', '西': '→',
  '北東': '↙', '北西': '↘', '南東': '↖', '南西': '↗',
}

const windColor = (speed) => {
  if (speed <= 2) return 'text-green-400'
  if (speed <= 4) return 'text-yellow-400'
  return 'text-red-400'
}

export default function WindBadge({ wind }) {
  if (!wind) return null
  const arrow = DIRECTION_ARROW[wind.direction] ?? '?'
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="text-gray-400 text-xs">風</span>
      <span className={`font-bold ${windColor(wind.speed)}`}>
        {arrow} {wind.speed}m
      </span>
      {wind.wave > 0 && (
        <span className="text-blue-300 text-xs">波{wind.wave}cm</span>
      )}
    </div>
  )
}
