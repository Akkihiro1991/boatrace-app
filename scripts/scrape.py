"""
boatrace.jp スクレイパー

リクエスト数: 1場あたり固定 ~14
  raceindex(1) + beforeinfo(1) + 未開始racelist(N) + 終了raceresult(M)
  N+M = 12 なので合計 14/場
14場開催でも ~196リクエスト → 約5分
"""
import json
import time
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

JST = timezone(timedelta(hours=9))
TODAY = datetime.now(JST).strftime('%Y%m%d')
DATE_LABEL = datetime.now(JST).strftime('%Y-%m-%d')

BASE = 'https://www.boatrace.jp/owpc/pc/race'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept-Language': 'ja,en;q=0.9',
}

VENUE_NAMES = {
    '01': '桐生', '02': '戸田', '03': '江戸川', '04': '平和島',
    '05': '多摩川', '06': '浜名湖', '07': '蒲郡', '08': '常滑',
    '09': '津', '10': '三国', '11': 'びわこ', '12': '住之江',
    '13': '尼崎', '14': '鳴門', '15': '丸亀', '16': '児島',
    '17': '宮島', '18': '徳山', '19': '下関', '20': '若松',
    '21': '芦屋', '22': '福岡', '23': '唐津', '24': '大村',
}

# ────────── ユーティリティ ──────────

def get(url, params=None, retries=2, wait=1.0):
    for i in range(retries):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=12)
            r.raise_for_status()
            r.encoding = 'utf-8'
            return r
        except requests.RequestException as e:
            if i < retries - 1:
                time.sleep(wait)
    return None

def ok(r):
    return r is not None and 'システムエラー' not in r.text

def pf(text, d=0.0):
    cleaned = re.sub(r'[^\d.]', '', str(text or '').strip())
    try: return float(cleaned)
    except: return d

def pi(text, d=0):
    cleaned = re.sub(r'[^\d]', '', str(text or '').strip())
    try: return int(cleaned)
    except: return d

# ────────── raceindex: スケジュール取得 ──────────

def get_race_schedule(jcd):
    """1場のレーススケジュールを取得。
    Returns: {rno: {'time': 'HH:MM', 'closed': bool}} or {}
    closed=True → 発売終了（終了 or 進行中）
    """
    r = get(f'{BASE}/raceindex', params={'jcd': jcd, 'hd': TODAY})
    if not ok(r):
        return {}
    soup = BeautifulSoup(r.text, 'lxml')

    schedule = {}
    for row in soup.select('tr'):
        a = row.select_one('a[href*="rno="]')
        if not a:
            continue
        m = re.search(r'rno=(\d+)', a.get('href', ''))
        if not m:
            continue
        rno = int(m.group(1))
        tds = row.select('td')
        race_time, closed = '--:--', False
        for td in tds:
            t = td.get_text(strip=True)
            if re.match(r'^\d{1,2}:\d{2}$', t):
                race_time = t
            if t == '発売終了':
                closed = True
        schedule[rno] = {'time': race_time, 'closed': closed}

    return schedule

# ────────── beforeinfo: 天候・展示タイム ──────────

def get_weather(jcd, rno):
    r = get(f'{BASE}/beforeinfo', params={'rno': rno, 'jcd': jcd, 'hd': TODAY})
    base = {'wind': {'speed': 0, 'direction': '不明', 'wave': 0},
            'weather': '晴', 'air_temp': None, 'water_temp': None, 'tenji': {}}
    if not ok(r):
        return base
    soup = BeautifulSoup(r.text, 'lxml')

    ws  = soup.select_one('.is-windSpeed, [class*="windSpeed"]')
    wd  = soup.select_one('.is-windDirection, [class*="windDirection"]')
    wv  = soup.select_one('.is-wave, [class*="wave"]')
    wt  = soup.select_one('.is-weather, [class*="weather"]')
    at  = soup.select_one('.is-airTemp, [class*="airTemp"]')
    wtr = soup.select_one('.is-waterTemp, [class*="waterTemp"]')

    base['wind']['speed']     = pf(ws.get_text() if ws else '0')
    base['wind']['direction'] = wd.get_text(strip=True) if wd else '不明'
    base['wind']['wave']      = pi(wv.get_text() if wv else '0')
    if wt:  base['weather']    = wt.get_text(strip=True)
    if at:  base['air_temp']   = pf(at.get_text())
    if wtr: base['water_temp'] = pf(wtr.get_text())

    tenji = {}
    for row in soup.select('table tr'):
        cols = row.select('td')
        if len(cols) < 3:
            continue
        lane = pi(cols[0].get_text())
        if not (1 <= lane <= 6):
            continue
        tt = pf(cols[1].get_text())
        ts = pf(cols[2].get_text())
        if tt > 0:
            tenji[lane] = {'tenji_time': tt, 'tenji_st': ts}
    base['tenji'] = tenji
    return base

# ────────── racelist: 出走表パース ──────────

def get_racers(jcd, rno):
    r = get(f'{BASE}/racelist', params={'rno': rno, 'jcd': jcd, 'hd': TODAY})
    if not ok(r):
        return []
    soup = BeautifulSoup(r.text, 'lxml')

    rows = soup.select('table.is-w748 tbody tr, .table1 tbody tr')
    if not rows:
        rows = soup.select('tr[class*="racer"], .contentsFrame1 tbody tr')

    racers = []
    for row in rows:
        cols = row.select('td')
        if len(cols) < 5:
            continue
        try:
            lane = pi(cols[0].get_text())
            if not (1 <= lane <= 6):
                continue
            name_el = row.select_one('.is-fs18, .racerName, td:nth-child(3)')
            name = name_el.get_text(strip=True) if name_el else ''
            if not name:
                continue

            no_el   = row.select_one('.racerNo, [class*="number"]')
            rank_el = row.select_one('.is-rank, [class*="rank"]')
            br_el   = row.select_one('[class*="branch"]')
            no     = no_el.get_text(strip=True)   if no_el   else ''
            rank   = rank_el.get_text(strip=True)  if rank_el else 'B1'
            branch = br_el.get_text(strip=True)    if br_el   else ''

            m_tds = [td.get_text(strip=True) for td in row.select('[class*="motor"]')]
            b_tds = [td.get_text(strip=True) for td in row.select('[class*="boat"]')]
            motor_no    = pi(m_tds[0]) if m_tds else 0
            motor_2rate = pf(m_tds[1]) if len(m_tds) > 1 else 0.0
            boat_no     = pi(b_tds[0]) if b_tds else 0
            boat_2rate  = pf(b_tds[1]) if len(b_tds) > 1 else 0.0

            st_el = row.select_one('[class*="st"], .is-ST')
            fl_el = row.select_one('[class*="fly"], [class*="late"]')
            st_avg = pf(st_el.get_text() if st_el else '0.18')
            flying = pi(fl_el.get_text() if fl_el else '0')

            cs = {}
            for i in range(1, 7):
                el = row.select_one(f'[class*="course{i}"], [data-course="{i}"]')
                cs[str(i)] = pf(el.get_text()) if el else 0.0

            racers.append({
                'lane': lane, 'name': name, 'no': no,
                'rank': rank if rank in ('A1','A2','B1','B2') else 'B1',
                'branch': branch,
                'motor_no': motor_no, 'motor_2rate': motor_2rate,
                'boat_no': boat_no,   'boat_2rate': boat_2rate,
                'course_stats': cs,
                'course_detail': {k: {'win': v, 'place2': 0.0, 'place3': 0.0} for k,v in cs.items()},
                'st_avg': st_avg if st_avg > 0 else 0.18,
                'tenji_time': None, 'tenji_st': None,
                'recent_results': [],
                'style': guess_style(cs),
                'local_rate': cs.get(str(lane), 0.0),
                'flying': flying, 'mae_zuke': False,
            })
        except Exception as e:
            continue

    racers.sort(key=lambda x: x['lane'])
    return racers

def guess_style(cs):
    c1 = cs.get('1', 0)
    c2 = cs.get('2', 0)
    c3 = cs.get('3', 0) + cs.get('4', 0)
    if c1 >= 60: return '逃げ'
    if c2 >= 45: return '差し'
    if c3 >= 40: return 'まくり'
    if c2 >= 35 and c3 >= 30: return 'まくり差し'
    return '差し'

# ────────── raceresult: 確定結果 ──────────

def get_result(jcd, rno):
    r = get(f'{BASE}/raceresult', params={'rno': rno, 'jcd': jcd, 'hd': TODAY})
    if not ok(r):
        return None
    soup = BeautifulSoup(r.text, 'lxml')
    if not soup.select_one('.result-pay, .is-result, [class*="result"]'):
        return None

    trifecta, payout = '', 0
    for row in soup.select('[class*="trifecta"], [class*="sanren"]'):
        c = row.select_one('[class*="combo"], [class*="num"]')
        p = row.select_one('[class*="pay"], [class*="amount"]')
        if c and p:
            trifecta = c.get_text(strip=True)
            payout   = pi(p.get_text())
            break
    if not trifecta:
        return None

    places_el = soup.select('[class*="place"] .num, [class*="arrive"] td')
    places = [pi(el.get_text()) for el in places_el if pi(el.get_text()) > 0]
    return {'places': places[:6], 'trifecta': trifecta, 'payout': payout}

# ────────── メイン: 1場スクレイプ ──────────

def scrape_venue(jcd):
    name = VENUE_NAMES.get(jcd, jcd)

    schedule = get_race_schedule(jcd)
    if not schedule:
        return None

    race_nos = sorted(schedule.keys())

    # 現在レース = 「発売終了」の最後。なければ最初のレース
    closed = [r for r in race_nos if schedule[r]['closed']]
    current_race = closed[-1] if closed else race_nos[0]

    # 天候・展示タイム（現在レースから取得）
    weather = get_weather(jcd, current_race)
    wind = weather['wind']
    print(f'[{name}] {len(race_nos)}R 現在{current_race}R | '
          f'{wind["direction"]} {wind["speed"]}m {weather["weather"]}')

    races = []
    for rno in race_nos:
        meta    = schedule[rno]
        is_closed = meta['closed']

        if is_closed:
            # 終了済み/進行中 → 結果を取得、選手情報は不要
            result  = get_result(jcd, rno)
            racers  = []
            status  = '終了' if result else '進行中'
        else:
            # 未開始 → 出走表を取得
            racers  = get_racers(jcd, rno)
            result  = None
            status  = '待機中'

        # 現在レースだけ展示タイムをマージ & 出走表も取得
        if rno == current_race and is_closed and not racers:
            racers = get_racers(jcd, rno)
            tenji  = weather.get('tenji', {})
            for racer in racers:
                t = tenji.get(racer['lane'])
                if t:
                    racer['tenji_time'] = t['tenji_time']
                    racer['tenji_st']   = t['tenji_st']

        races.append({
            'race_no': rno,
            'time':    meta['time'],
            'status':  status,
            'racers':  racers,
            'result':  result,
        })

    return {
        'id': jcd, 'name': name,
        'status': '開催中' if any(r['status'] in ('進行中','待機中') for r in races) else '終了',
        'current_race': current_race,
        'wind': wind,
        'weather': weather['weather'],
        'air_temp': weather['air_temp'],
        'water_temp': weather['water_temp'],
        'races': races,
    }

# ────────── エントリーポイント ──────────

def main():
    print(f'=== ボートレース {DATE_LABEL} ===')
    venues_data = []
    for jcd, name in VENUE_NAMES.items():
        result = scrape_venue(jcd)
        if result and result['races']:
            venues_data.append(result)
        else:
            print(f'  ─ {name}: 本日開催なし')
        time.sleep(0.3)

    output = {
        'date': DATE_LABEL,
        'generated_at': datetime.now(JST).isoformat(),
        'venues': venues_data,
    }
    out_path = Path(__file__).parent.parent / 'public' / 'data' / 'races.json'
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'\n✅ {len(venues_data)}場 / {sum(len(v["races"]) for v in venues_data)}R 保存完了')

if __name__ == '__main__':
    main()
