import { useState, useEffect } from 'react'

const BASE = import.meta.env.BASE_URL

export function useRaceData() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)

  const fetchData = async () => {
    try {
      const res = await fetch(`${BASE}data/races.json?t=${Date.now()}`)
      if (!res.ok) throw new Error('データ取得失敗')
      const json = await res.json()
      setData(json)
      setLastUpdated(new Date())
      setError(null)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

  return { data, loading, error, lastUpdated, refetch: fetchData }
}
