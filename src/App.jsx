import { useState } from 'react'
import { useRaceData } from './hooks/useRaceData'
import VenueCard from './components/VenueCard'
import RaceDetail from './components/RaceDetail'

const TABS = [
  { id: 'today', label: '今日', icon: '🏁' },
  { id: 'results', label: '結果', icon: '📊' },
  { id: 'oc', label: 'OC', icon: '💬' },
]

function formatTime(date) {
  if (!date) return ''
  return date.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' })
}

export default function App() {
  const { data, loading, error, lastUpdated, refetch } = useRaceData()
  const [activeTab, setActiveTab] = useState('today')
  const [selectedRace, setSelectedRace] = useState(null)
  const [selectedVenue, setSelectedVenue] = useState(null)

  const handleSelectRace = (venue, race) => {
    setSelectedVenue(venue)
    setSelectedRace(race)
  }

  const handleCloseRace = () => {
    setSelectedRace(null)
    setSelectedVenue(null)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="text-4xl mb-4 animate-bounce">🚤</div>
          <div className="text-gray-400">データ読み込み中...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen p-8">
        <div className="text-center">
          <div className="text-red-400 mb-2">データ取得エラー</div>
          <button onClick={refetch} className="text-blue-400 text-sm">再読み込み</button>
        </div>
      </div>
    )
  }

  const resultVenues = data?.venues?.map(v => ({
    ...v,
    races: v.races.filter(r => r.result),
  })).filter(v => v.races.length > 0) ?? []

  return (
    <div className="max-w-md mx-auto min-h-screen relative">
      {/* ヘッダー */}
      <header className="sticky top-0 z-40 bg-navy-900 border-b border-navy-700 px-4 py-3">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-bold text-lg">⚡ 展開ナビ</h1>
            <div className="text-xs text-gray-500">{data?.date} 更新 {formatTime(lastUpdated)}</div>
          </div>
          <button onClick={refetch} className="text-gray-400 text-xl p-1">↻</button>
        </div>
      </header>

      {/* コンテンツ */}
      <main className="page-content">
        {activeTab === 'today' && (
          <div className="p-4 space-y-4">
            {data?.venues?.length === 0 && (
              <div className="text-center text-gray-500 py-12">本日の開催情報なし</div>
            )}
            {data?.venues?.map(venue => (
              <VenueCard
                key={venue.id}
                venue={venue}
                onSelectRace={handleSelectRace}
              />
            ))}
          </div>
        )}

        {activeTab === 'results' && (
          <div className="p-4 space-y-4">
            {resultVenues.length === 0 ? (
              <div className="text-center text-gray-500 py-12">結果はまだありません</div>
            ) : resultVenues.map(venue => (
              <div key={venue.id} className="card overflow-hidden">
                <div className="px-4 py-3 border-b border-navy-700 font-bold">{venue.name}</div>
                {venue.races.map(race => (
                  <button
                    key={race.race_no}
                    onClick={() => handleSelectRace(venue, race)}
                    className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-navy-700 border-b border-navy-700 last:border-0"
                  >
                    <span className="text-sm">{race.race_no}R {race.time}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-yellow-400 font-bold text-sm">{race.result.trifecta}</span>
                      <span className="text-gray-400 text-xs">{race.result.payout.toLocaleString()}円</span>
                    </div>
                  </button>
                ))}
              </div>
            ))}
          </div>
        )}

        {activeTab === 'oc' && (
          <div className="p-4 space-y-4">
            <div className="card p-6 text-center">
              <div className="text-4xl mb-3">💬</div>
              <h2 className="font-bold text-lg mb-1">ボートレース展開予想部</h2>
              <p className="text-gray-400 text-sm mb-4">
                風・モーター・選手傾向をもとに<br />みんなで展開を予想するLINEオープンチャット
              </p>
              <a
                href="https://line.me/ti/g2/ourboat"
                target="_blank"
                rel="noopener noreferrer"
                className="block bg-green-500 hover:bg-green-400 text-white font-bold py-3 rounded-xl transition-colors"
              >
                LINEで参加する（無料）
              </a>
            </div>

            <div className="card p-4">
              <h3 className="font-bold mb-3 text-sm text-gray-400">このアプリの使い方</h3>
              <div className="space-y-3 text-sm">
                <div className="flex gap-3">
                  <span className="text-2xl">🏁</span>
                  <div>
                    <div className="font-bold">「今日」タブ</div>
                    <div className="text-gray-400 text-xs">全国の開催場・レースを確認。風・モーター・選手傾向をチェック。</div>
                  </div>
                </div>
                <div className="flex gap-3">
                  <span className="text-2xl">📊</span>
                  <div>
                    <div className="font-bold">「結果」タブ</div>
                    <div className="text-gray-400 text-xs">確定した3連単と配当を確認。</div>
                  </div>
                </div>
                <div className="flex gap-3">
                  <span className="text-2xl">💬</span>
                  <div>
                    <div className="font-bold">OCで予想</div>
                    <div className="text-gray-400 text-xs">データを見たらOCで「今日の〇場〇Rはどう思う？」と語り合おう。</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* ボトムナビ */}
      <nav className="fixed bottom-0 left-0 right-0 max-w-md mx-auto bg-navy-800 border-t border-navy-700 flex">
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 flex flex-col items-center py-3 gap-0.5 transition-colors ${
              activeTab === tab.id ? 'text-blue-400' : 'text-gray-500'
            }`}
          >
            <span className="text-xl">{tab.icon}</span>
            <span className="text-xs">{tab.label}</span>
          </button>
        ))}
      </nav>

      {/* レース詳細（フルスクリーン） */}
      {selectedRace && selectedVenue && (
        <RaceDetail
          race={selectedRace}
          wind={selectedVenue.wind}
          onClose={handleCloseRace}
        />
      )}
    </div>
  )
}
