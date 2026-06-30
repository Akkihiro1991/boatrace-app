const rateColor = (rate) => {
  if (rate >= 55) return 'bg-yellow-400 text-black'
  if (rate >= 42) return 'bg-blue-500 text-white'
  return 'bg-gray-600 text-gray-300'
}

const rateLabel = (rate) => {
  if (rate >= 55) return '上'
  if (rate >= 42) return '並'
  return '下'
}

export default function MotorBadge({ rate }) {
  return (
    <span className={`inline-flex items-center gap-1 text-xs px-1.5 py-0.5 rounded font-bold ${rateColor(rate)}`}>
      機{rateLabel(rate)} {rate.toFixed(1)}%
    </span>
  )
}
