const LANE_COLOR = {
  1: 'bg-white text-black',
  2: 'bg-gray-400 text-black',
  3: 'bg-red-500 text-white',
  4: 'bg-blue-500 text-white',
  5: 'bg-yellow-400 text-black',
  6: 'bg-green-500 text-white',
}

const rateColor = (rate) =>
  rate >= 60 ? 'text-yellow-400 font-bold' :
  rate >= 45 ? 'text-blue-300 font-bold' :
  rate >= 30 ? 'text-gray-300' : 'text-gray-500'

export default function CourseStats({ courseDetail, assignedLane }) {
  if (!courseDetail) return null

  const courses = Object.entries(courseDetail)
    .map(([c, v]) => ({ course: parseInt(c), win: v.win ?? 0, place2: v.place2 ?? 0, place3: v.place3 ?? 0 }))
    .filter(c => c.win > 0 || c.place2 > 0)
    .sort((a, b) => a.course - b.course)

  if (courses.length === 0) return null

  return (
    <div className="mt-2">
      <div className="text-xs text-gray-500 mb-1.5">コース別成績</div>
      <table className="w-full text-xs">
        <thead>
          <tr className="text-gray-600">
            <th className="text-left pb-1 w-12">コース</th>
            <th className="text-right pb-1">勝率</th>
            <th className="text-right pb-1">2連率</th>
            <th className="text-right pb-1">3連率</th>
          </tr>
        </thead>
        <tbody>
          {courses.map(({ course, win, place2, place3 }) => (
            <tr
              key={course}
              className={`border-t border-navy-700 ${course === assignedLane ? 'bg-navy-700/50' : ''}`}
            >
              <td className="py-1">
                <div className="flex items-center gap-1.5">
                  <span className={`w-4 h-4 rounded-full flex items-center justify-center text-xs font-bold ${LANE_COLOR[course] ?? 'bg-gray-600 text-white'}`}>
                    {course}
                  </span>
                  {course === assignedLane && (
                    <span className="text-blue-400 text-xs">今節</span>
                  )}
                </div>
              </td>
              <td className={`text-right py-1 ${rateColor(win)}`}>{win.toFixed(1)}%</td>
              <td className={`text-right py-1 ${rateColor(place2)}`}>{place2 > 0 ? `${place2.toFixed(1)}%` : '-'}</td>
              <td className={`text-right py-1 ${rateColor(place3 ?? 0)}`}>{place3 > 0 ? `${place3.toFixed(1)}%` : '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
