"""
boatrace.jp スクレイパー（並列版）

Phase1: 全24場のスケジュールを並列取得 (~30秒)
Phase2: 開催場のレースデータを並列取得 (~3分)
合計: ~4分（従来34分）
"""
import json
import time
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

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

def get(url, params=None):
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=12)
        r.raise_for_status()
        r.encoding = 'utf-8'
        if 'システムエラー' in r.text:
            return None
        return r
    except Exception:
        return None

def pf(text, d=0.0):
    try: return float(re.sub(r'[^\d.]', '', str(text or '').strip()))
    except: return d

def pi(text, d=0):
    try: return int(re.sub(r'[^\d]', '', str(text or '').strip()))
    except: return d

# ────────── Phase1: スケジュール取得 ──────────

def fetch_schedule(jcd):
    """raceindex から1場のスケジュールを取得"""
    r = get(f'{BASE}/raceindex', params={'jcd': jcd, 'hd': TODAY})
    if not r:
        return jcd, {}
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
        race_time, closed = '--:--', False
        for td in row.select('td'):
            t = td.get_text(strip=True)
            if re.match(r'^\d{1,2}:\d{2}$', t):
                race_time = t
            if t == '発売終了':
                closed = True
        schedule[rno] = {'time': race_time, 'closed': closed}

    return jcd, schedule

# ────────── Phase2: レースデータ取得 ──────────

def fetch_weather(jcd, rno):
    """beforeinfo から風・天候・展示タイムを取得"""
    r = get(f'{BASE}/beforeinfo', params={'rno': rno, 'jcd': jcd, 'hd': TODAY})
    base = {'wind': {'speed': 0, 'direction': '不明', 'wave': 0},
            'weather': '晴', 'air_temp': None, 'water_temp': None, 'tenji': {}}
    if not r:
        return base
    soup = BeautifulSoup(r.text, 'lxml')

    # 天候テーブルから数値のみ抽出
    for label, key in [('.is-windSpeed', 'speed'), ('.is-windDirection', 'direction'),
                       ('.is-wave', 'wave')]:
        el = soup.select_one(label) or soup.select_one(f'[class*="{label[4:]}"]')
        if not el:
            continue
        t = el.get_text(strip=True)
        if key == 'direction':
            base['wind']['direction'] = t
        elif key == 'speed':
            base['wind']['speed'] = pf(t)
        else:
            base['wind']['wave'] = pi(t)

    wt  = soup.select_one('.is-weather, [class*="weather"]')
    at  = soup.select_one('.is-airTemp, [class*="airTemp"]')
    wtr = soup.select_one('.is-waterTemp, [class*="waterTemp"]')
    if wt:  base['weather']    = wt.get_text(strip=True)
    if at:  base['air_temp']   = pf(at.get_text())
    if wtr: base['water_temp'] = pf(wtr.get_text())

    # 展示タイム
    tenji = {}
    for row in soup.select('table tr'):
        cols = row.select('td')
        if len(cols) < 3:
            continue
        lane = pi(cols[0].get_text())
        if not (1 <= lane <= 6):
            continue
        tt = pf(cols[1].get_text())
        if tt > 0:
            tenji[lane] = {'tenji_time': tt, 'tenji_st': pf(cols[2].get_text())}
    base['tenji'] = tenji
    return base

def fetch_racers(jcd, rno):
    """racelist から選手リストを取得"""
    r = get(f'{BASE}/racelist', params={'rno': rno, 'jcd': jcd, 'hd': TODAY})
    if not r:
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
            no     = no_el.get_text(strip=True)  if no_el   else ''
            rank   = rank_el.get_text(strip=True) if rank_el else 'B1'
            branch = br_el.get_text(strip=True)   if br_el   else ''

            mt = [td.get_text(strip=True) for td in row.select('[class*="motor"]')]
            bt = [td.get_text(strip=True) for td in row.select('[class*="boat"]')]

            st_el = row.select_one('[class*="st"], .is-ST')
            fl_el = row.select_one('[class*="fly"], [class*="late"]')
            st_avg = pf(st_el.get_text() if st_el else '0.18')

            cs = {}
            for i in range(1, 7):
                el = row.select_one(f'[class*="course{i}"], [data-course="{i}"]')
                cs[str(i)] = pf(el.get_text()) if el else 0.0

            racers.append({
                'lane': lane, 'name': name, 'no': no,
                'rank': rank if rank in ('A1','A2','B1','B2') else 'B1',
                'branch': branch,
                'motor_no': pi(mt[0]) if mt else 0,
                'motor_2rate': pf(mt[1]) if len(mt) > 1 else 0.0,
                'boat_no':  pi(bt[0]) if bt else 0,
                'boat_2rate': pf(bt[1]) if len(bt) > 1 else 0.0,
                'course_stats': cs,
                'course_detail': {k: {'win': v, 'place2': 0.0, 'place3': 0.0} for k,v in cs.items()},
                'st_avg': st_avg if st_avg > 0 else 0.18,
                'tenji_time': None, 'tenji_st': None,
                'recent_results': [],
                'style': guess_style(cs),
                'local_rate': cs.get(str(lane), 0.0),
                'flying': pi(fl_el.get_text() if fl_el else '0'),
                'mae_zuke': False,
            })
        except Exception:
            continue

    racers.sort(key=lambda x: x['lane'])
    return racers

def fetch_result(jcd, rno):
    """raceresult から確定結果を取得"""
    r = get(f'{BASE}/raceresult', params={'rno': rno, 'jcd': jcd, 'hd': TODAY})
    if not r or not soup_has_result(r.text):
        return None
    soup = BeautifulSoup(r.text, 'lxml')

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

def soup_has_result(html):
    return bool(re.search(r'result-pay|is-result|["\']result["\']', html))

def guess_style(cs):
    c1 = cs.get('1', 0)
    c2 = cs.get('2', 0)
    c3 = cs.get('3', 0) + cs.get('4', 0)
    if c1 >= 60: return '逃げ'
    if c2 >= 45: return '差し'
    if c3 >= 40: return 'まくり'
    if c2 >= 35 and c3 >= 30: return 'まくり差し'
    return '差し'

# ────────── 1場スクレイプ ──────────

def fetch_race_data(args):
    """並列実行用: 1レース分のデータを取得"""
    jcd, rno, is_closed, is_current = args
    racers = fetch_racers(jcd, rno) if (not is_closed or is_current) else []
    result = fetch_result(jcd, rno) if is_closed else None
    return rno, racers, result

def scrape_venue(jcd, schedule):
    """1場のデータをまとめて取得（レースは並列）"""
    name = VENUE_NAMES.get(jcd, jcd)
    race_nos = sorted(schedule.keys())

    closed = [r for r in race_nos if schedule[r]['closed']]
    current_race = closed[-1] if closed else race_nos[0]

    # 天候（現在レースから）
    weather = fetch_weather(jcd, current_race)
    wind = weather['wind']

    # レースデータを並列取得（最大4並列）
    tasks = [
        (jcd, rno, schedule[rno]['closed'], rno == current_race)
        for rno in race_nos
    ]
    race_data = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        for rno, racers, result in ex.map(fetch_race_data, tasks):
            race_data[rno] = (racers, result)

    # 現在レースに展示タイムをマージ
    if current_race in race_data:
        racers, result = race_data[current_race]
        tenji = weather.get('tenji', {})
        for racer in racers:
            t = tenji.get(racer['lane'])
            if t:
                racer['tenji_time'] = t['tenji_time']
                racer['tenji_st']   = t['tenji_st']

    races = []
    for rno in race_nos:
        meta = schedule[rno]
        racers, result = race_data.get(rno, ([], None))

        if result:
            status = '終了'
        elif meta['closed']:
            status = '進行中'
        else:
            status = '待機中'

        races.append({
            'race_no': rno, 'time': meta['time'],
            'status': status, 'racers': racers, 'result': result,
        })

    print(f'  ✅ {name}: {len(races)}R (現在{current_race}R, '
          f'{sum(1 for r in races if r["status"]=="終了")}終了/'
          f'{sum(1 for r in races if r["status"]=="進行中")}進行中/'
          f'{sum(1 for r in races if r["status"]=="待機中")}待機中)')

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
    t0 = time.time()

    # Phase1: 全24場のスケジュールを並列取得
    print('Phase1: スケジュール取得中...')
    schedules = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        for jcd, schedule in ex.map(fetch_schedule, VENUE_NAMES.keys()):
            if schedule:
                schedules[jcd] = schedule
            else:
                print(f'  ─ {VENUE_NAMES[jcd]}: 本日開催なし')

    active = {jcd: s for jcd, s in schedules.items()}
    print(f'Phase1完了: {len(active)}場 ({time.time()-t0:.0f}秒)')

    # Phase2: 開催場のデータを取得（場ごとは逐次、レースは並列）
    print('Phase2: レースデータ取得中...')
    venues_data = []
    for jcd, schedule in active.items():
        result = scrape_venue(jcd, schedule)
        if result:
            venues_data.append(result)

    output = {
        'date': DATE_LABEL,
        'generated_at': datetime.now(JST).isoformat(),
        'venues': venues_data,
    }
    out_path = Path(__file__).parent.parent / 'public' / 'data' / 'races.json'
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')

    elapsed = time.time() - t0
    print(f'\n✅ {len(venues_data)}場 / {sum(len(v["races"]) for v in venues_data)}R 保存完了 '
          f'({elapsed:.0f}秒)')

if __name__ == '__main__':
    main()
