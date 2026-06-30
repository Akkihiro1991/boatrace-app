import WindBadge from './WindBadge'

const WEATHER_ICON = { '晴': '☀️', '曇': '☁️', '雨': '🌧️', '雪': '❄️' }

export default function WeatherBar({ wind, weather, airTemp, waterTemp }) {
  return (
    <div className="flex items-center gap-3 flex-wrap text-sm">
      <WindBadge wind={wind} />
      {weather && (
        <span className="text-gray-300">
          {WEATHER_ICON[weather] ?? ''} {weather}
        </span>
      )}
      {airTemp != null && (
        <span className="text-gray-400 text-xs">気温<span className="text-white ml-0.5">{airTemp}°</span></span>
      )}
      {waterTemp != null && (
        <span className="text-gray-400 text-xs">水温<span className="text-blue-300 ml-0.5">{waterTemp}°</span></span>
      )}
    </div>
  )
}
