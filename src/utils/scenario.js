const WIND_FAVOR_IN = ['北', '北東', '北西']
const WIND_FAVOR_OUT = ['南', '南東', '南西']

function windEffect(wind) {
  if (!wind) return 'neutral'
  if (WIND_FAVOR_IN.includes(wind.direction) && wind.speed >= 3) return 'in'
  if (WIND_FAVOR_OUT.includes(wind.direction) && wind.speed >= 3) return 'out'
  return 'neutral'
}

function courseWin(racer, course) {
  return racer.course_detail?.[String(course)]?.win ?? racer.course_stats?.[String(course)] ?? 0
}

export function generateScenario(racers, wind) {
  const get = (lane) => racers.find(r => r.lane === lane)
  const r1 = get(1)
  const r2 = get(2)
  const outer = racers.filter(r => r.lane >= 3)
  const effect = windEffect(wind)

  const main = []
  const risks = []
  const keyRacer = [...racers].sort((a, b) => b.motor_2rate - a.motor_2rate)[0]

  // 1号艇分析
  if (r1) {
    const c1win = courseWin(r1, 1)
    const motorGood = r1.motor_2rate >= 50
    const stSharp = r1.st_avg <= 0.15
    if (c1win >= 65 && motorGood) {
      main.push(`1号艇・${r1.name}の逃げが最有力（1コース勝率${c1win}%・機力${r1.motor_2rate}%）`)
    } else if (c1win >= 50) {
      main.push(`1号艇・${r1.name}が逃げ狙い（1コース勝率${c1win}%）だが盤石ではない`)
    } else {
      risks.push(`1号艇・${r1.name}は1コース勝率${c1win}%と低め——外からの捲りが決まりやすい`)
    }
  }

  // 2号艇分析
  if (r2) {
    const stSharp = r2.st_avg <= 0.15
    const isDiff = r2.style?.includes('差し') || r2.style?.includes('まくり差し')
    if (stSharp && isDiff) {
      main.push(`2号艇・${r2.name}の差しに注意（ST${r2.st_avg}・${r2.style}型）`)
    }
  }

  // 外枠の脅威
  outer.forEach(r => {
    const isMakuri = r.style?.includes('まくり')
    const motorGood = r.motor_2rate >= 45
    const tSharp = r.tenji_time && r.tenji_time <= 6.80
    if (isMakuri && (motorGood || tSharp)) {
      const note = tSharp ? `展示${r.tenji_time}秒の伸び` : `機力${r.motor_2rate}%`
      risks.push(`${r.lane}号艇・${r.name}のまくり警戒（${note}）`)
    }
  })

  // 展示ST鋭い選手
  const sharpTenji = racers.filter(r => r.tenji_st !== null && r.tenji_st !== undefined && r.tenji_st <= 0.05)
  sharpTenji.forEach(r => {
    if (r.lane >= 2) {
      risks.push(`${r.lane}号艇・${r.name}の展示ST${r.tenji_st}——当日スタート要注意`)
    }
  })

  // F持ち
  racers.filter(r => r.flying > 0).forEach(r => {
    risks.push(`${r.lane}号艇・${r.name}はF${r.flying}本持ち（慎重スタートになる可能性）`)
  })

  // 前づけ
  racers.filter(r => r.mae_zuke).forEach(r => {
    risks.push(`${r.lane}号艇・${r.name}が前づけ傾向——コース変動に注意`)
  })

  // 風の影響
  if (effect === 'out' && wind.speed >= 4) {
    risks.push(`${wind.direction}${wind.speed}mの追い風でアウトコース有利——外枠の捲りが決まりやすい状況`)
  } else if (effect === 'in' && wind.speed >= 4) {
    main.push(`${wind.direction}${wind.speed}mの風でインコース有利——逃げが決まりやすい`)
  }

  return {
    main: main.length > 0 ? main : ['展開データ収集中'],
    risks,
    keyRacer,
  }
}
