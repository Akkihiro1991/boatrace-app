const LANE_BG = {
  1: 'bg-white text-black',
  2: 'bg-gray-800 text-white border border-gray-600',
  3: 'bg-red-700 text-white',
  4: 'bg-blue-700 text-white',
  5: 'bg-yellow-600 text-black',
  6: 'bg-green-700 text-white',
}

export default function CourseStats({ courseDetail, assignedLane }) {
  if (!courseDetail) return null
  const courses = Object.entries(courseDetail)
    .map(([c, v]) => ({ course: parseInt(c), ...v }))
    .filter(c => c.win > 0 || c.place2 > 0)
    .sort((a, b) => a.course - b.course)

  if (courses.length === 0) return null

  return (
    <div className="mt-2">
      <div className="text-xs text-gray-500 mb-1">コース別成績</div>
      <div className="grid grid-cols-3 gap-1">
        {courses.map(({ course, win, place2, place3 }) => (
          <div
            key={course}
            className={`rounded p-1.5 text-center text-xs ${course === assignedLane ? 'ring-1 ring-blue-400' : 'bg-navy-700'}`}
          >
            <div className={`inline-flex w-4 h-4 rounded-full items-center justify-center text-xs font-bold mb-0.5 ${LANE_BG[course]}`}>
              {course}
            </div>
            <div className="text-yellow-400 font-bold">{win.toFixed(1)}<span className="text-gray-500 font-normal">%</span></div>
            {place2 > 0 && <div className="text-gray-400">{place2.toFixed(1)}%</div>}
          </div>
        ))}
      </div>
    </div>
  )
}
