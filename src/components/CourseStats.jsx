const LANE_COLOR = {
  1: 'bg-white',
  2: 'bg-gray-400',
  3: 'bg-red-500',
  4: 'bg-blue-500',
  5: 'bg-yellow-400',
  6: 'bg-green-500',
}

function Bar({ rate, max = 100 }) {
  const pct = Math.min((rate / max) * 100, 100)
  const color = rate >= 60 ? 'bg-yellow-400' : rate >= 45 ? 'bg-blue-400' : rate >= 30 ? 'bg-gray-400' : 'bg-gray-600'
  return (
    <div className="flex-1 bg-navy-700 rounded-full h-2 overflow-hidden">
      <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
    </div>
  )
}

export default function CourseStats({ courseDetail, assignedLane }) {
  if (!courseDetail) return null

  const courses = Object.entries(courseDetail)
    .map(([c, v]) => ({ course: parseInt(c), win: v.win ?? 0, place2: v.place2 ?? 0 }))
    .filter(c => c.win > 0 || c.place2 > 0)
    .sort((a, b) => a.course - b.course)

  if (courses.length === 0) return null

  return (
    <div className="mt-2 space-y-1.5">
      <div className="text-xs text-gray-500 mb-2">コース別成績</div>
      {courses.map(({ course, win, place2 }) => (
        <div key={course} className={`flex items-center gap-2 ${course === assignedLane ? 'opacity-100' : 'opacity-60'}`}>
          {/* コース番号 */}
          <div className={`w-4 h-4 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold text-black ${LANE_COLOR[course] ?? 'bg-gray-600'}`}>
            {course}
          </div>

          {/* バー + 数値 */}
          <div className="flex-1 space-y-0.5">
            <div className="flex items-center gap-1.5">
              <Bar rate={win} />
              <span className="text-xs text-gray-300 w-10 text-right">{win.toFixed(1)}%</span>
            </div>
            {place2 > 0 && (
              <div className="flex items-center gap-1.5">
                <Bar rate={place2} />
                <span className="text-xs text-gray-500 w-10 text-right">{place2.toFixed(1)}%</span>
              </div>
            )}
          </div>

          {/* 今節マーク */}
          {course === assignedLane && (
            <span className="text-xs text-blue-400 flex-shrink-0">今節</span>
          )}
        </div>
      ))}
      <div className="flex gap-3 pt-1 text-xs text-gray-600">
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-gray-400 inline-block" />勝率</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-gray-600 inline-block" />2連率</span>
      </div>
    </div>
  )
}
