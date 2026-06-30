const RANK_COLOR = {
  A1: 'bg-yellow-500 text-black',
  A2: 'bg-yellow-700 text-white',
  B1: 'bg-gray-500 text-white',
  B2: 'bg-gray-700 text-gray-300',
}

export default function RankBadge({ rank }) {
  return (
    <span className={`text-xs px-1 py-0.5 rounded font-bold ${RANK_COLOR[rank] ?? 'bg-gray-700 text-gray-300'}`}>
      {rank}
    </span>
  )
}
