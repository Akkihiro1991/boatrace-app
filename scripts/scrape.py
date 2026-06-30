"""
boatrace.jp から出走表・モーター・選手情報・結果をスクレイピングして
public/data/races.json を生成する
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
    'User-Agent': 'Mozilla/5.0 (compatible; BoatraceDataBot/1.0)',
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

STYLE_MAP = {
    '逃': '逃げ', '差': '差し', '捲': 'まくり',
    '捲差': 'まくり差し', '抵': 'まくり差し',
}

def get(url, params=None, retries=3, wait=1.5):
    for i in range(retries):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=15)
            r.raise_for_status()
            r.encoding = 'utf-8'
            return r
        except requests.RequestException as e:
            print(f'  retry {i+1}/{retries}: {e}')
            time.sleep(wait * (i + 1))
    return None

def parse_float(text, default=0.0):
    if not text:
        return default
    cleaned = re.sub(r'[^\d.]', '', text.strip())
    try:
        return float(cleaned)
    except ValueError:
        return default

def parse_int(text, default=0):
    if not text:
        return default
    cleaned = re.sub(r'[^\d]', '', text.strip())
    try:
        return int(cleaned)
    except ValueError:
        return default

def get_active_venues():
    """本日開催している場のリストを取得"""
    r = get(f'{BASE}/index')
    if not r:
        return []
    soup = BeautifulSoup(r.text, 'lxml')
    venues = []
    for a in soup.select('a[href*="jcd="]'):
        href = a.get('href', '')
        m = re.search(r'jcd=(\d{2})', href)
        if m:
            jcd = m.group(1)
            if jcd not in [v['id'] for v in venues]:
                venues.append({'id': jcd, 'name': VENUE_NAMES.get(jcd, jcd)})
    return venues

def get_race_list(jcd):
    """指定場の本日レース番号リストと現在レースを取得"""
    r = get(f'{BASE}/racelist', params={'jcd': jcd, 'hd': TODAY})
    if not r:
        return [], 1
    soup = BeautifulSoup(r.text, 'lxml')
    race_nos = []
    for a in soup.select('a[href*="rno="]'):
        m = re.search(r'rno=(\d+)', a.get('href', ''))
        if m:
            rno = int(m.group(1))
            if rno not in race_nos:
                race_nos.append(rno)
    race_nos.sort()

    current = 1
    for el in soup.select('.is-current, .isCurrentRace'):
        m = re.search(r'rno=(\d+)', el.get('href', ''))
        if m:
            current = int(m.group(1))
            break

    return race_nos, current

def get_wind(jcd):
    """展示・直前情報から風データを取得（最終レースのページを使用）"""
    r = get(f'{BASE}/beforeinfo', params={'rno': 1, 'jcd': jcd, 'hd': TODAY})
    if not r:
        return {'speed': 0, 'direction': '不明', 'wave': 0}
    soup = BeautifulSoup(r.text, 'lxml')

    speed = 0
    direction = '不明'
    wave = 0

    wind_el = soup.select_one('.is-windSpeed, [class*="wind"]')
    if wind_el:
        speed = parse_float(wind_el.get_text())

    dir_el = soup.select_one('.is-windDirection, [class*="direction"]')
    if dir_el:
        direction = dir_el.get_text(strip=True)

    wave_el = soup.select_one('.is-wave, [class*="wave"]')
    if wave_el:
        wave = parse_int(wave_el.get_text())

    return {'speed': speed, 'direction': direction, 'wave': wave}

def get_racers(jcd, rno):
    """出走表・モーター情報から選手データを取得"""
    r = get(f'{BASE}/racelist', params={'rno': rno, 'jcd': jcd, 'hd': TODAY})
    if not r:
        return []
    soup = BeautifulSoup(r.text, 'lxml')

    racers = []
    rows = soup.select('table.is-w748 tbody tr, .table1 tbody tr')
    if not rows:
        rows = soup.select('tr[class*="racer"], .contentsFrame1 tbody tr')

    for row in rows:
        cols = row.select('td')
        if len(cols) < 5:
            continue

        try:
            lane = parse_int(cols[0].get_text())
            if lane < 1 or lane > 6:
                continue

            name_el = row.select_one('.is-fs18, .racerName, td:nth-child(3)')
            name = name_el.get_text(strip=True) if name_el else ''
            if not name:
                continue

            no_el = row.select_one('.racerNo, [class*="number"]')
            no = no_el.get_text(strip=True) if no_el else ''

            rank_el = row.select_one('.is-rank, [class*="rank"]')
            rank = rank_el.get_text(strip=True) if rank_el else 'B1'

            branch_el = row.select_one('[class*="branch"], [class*="branch"]')
            branch = branch_el.get_text(strip=True) if branch_el else ''

            motor_texts = [td.get_text(strip=True) for td in row.select('[class*="motor"]')]
            motor_no = parse_int(motor_texts[0]) if motor_texts else 0
            motor_2rate = parse_float(motor_texts[1]) if len(motor_texts) > 1 else 0.0

            boat_texts = [td.get_text(strip=True) for td in row.select('[class*="boat"]')]
            boat_no = parse_int(boat_texts[0]) if boat_texts else 0
            boat_2rate = parse_float(boat_texts[1]) if len(boat_texts) > 1 else 0.0

            # ST平均
            st_el = row.select_one('[class*="st"], .is-ST')
            st_avg = parse_float(st_el.get_text() if st_el else '0.18')

            # F/L
            fl_el = row.select_one('[class*="fly"], [class*="late"]')
            flying = parse_int(fl_el.get_text() if fl_el else '0')

            # コース別成績
            course_stats = {}
            for i in range(1, 7):
                course_el = row.select_one(f'[class*="course{i}"], [data-course="{i}"]')
                if course_el:
                    course_stats[str(i)] = parse_float(course_el.get_text())
                else:
                    course_stats[str(i)] = 0.0

            racers.append({
                'lane': lane,
                'name': name,
                'no': no,
                'rank': rank if rank in ('A1', 'A2', 'B1', 'B2') else 'B1',
                'branch': branch,
                'motor_no': motor_no,
                'motor_2rate': motor_2rate,
                'boat_no': boat_no,
                'boat_2rate': boat_2rate,
                'course_stats': course_stats,
                'st_avg': st_avg if st_avg > 0 else 0.18,
                'style': guess_style(course_stats),
                'local_rate': course_stats.get(str(lane), 0.0),
                'flying': flying,
            })
        except Exception as e:
            print(f'    racer parse error: {e}')
            continue

    racers.sort(key=lambda x: x['lane'])
    return racers

def guess_style(course_stats):
    """コース別成績から得意な走りを推定"""
    c1 = course_stats.get('1', 0)
    c2 = course_stats.get('2', 0)
    c3 = course_stats.get('3', 0) + course_stats.get('4', 0)

    if c1 >= 60:
        return '逃げ'
    if c2 >= 45:
        return '差し'
    if c3 >= 40:
        return 'まくり'
    if c2 >= 35 and c3 >= 30:
        return 'まくり差し'
    return '差し'

def get_race_status(jcd, rno, current_race):
    """レースのステータスを判定"""
    result = get_result(jcd, rno)
    if result:
        return '終了', result
    if rno == current_race:
        return '進行中', None
    if rno < current_race:
        return '終了', None
    return '待機中', None

def get_result(jcd, rno):
    """レース結果を取得"""
    r = get(f'{BASE}/raceresult', params={'rno': rno, 'jcd': jcd, 'hd': TODAY})
    if not r:
        return None
    soup = BeautifulSoup(r.text, 'lxml')

    result_el = soup.select_one('.result-pay, .is-result, [class*="result"]')
    if not result_el:
        return None

    # 3連単
    trifecta = ''
    payout = 0
    tri_rows = soup.select('[class*="trifecta"], [class*="sanren"]')
    for row in tri_rows:
        combo_el = row.select_one('[class*="combo"], [class*="num"]')
        pay_el = row.select_one('[class*="pay"], [class*="amount"]')
        if combo_el and pay_el:
            trifecta = combo_el.get_text(strip=True)
            payout = parse_int(pay_el.get_text())
            break

    if not trifecta:
        return None

    places_el = soup.select('[class*="place"] .num, [class*="arrive"] td')
    places = [parse_int(el.get_text()) for el in places_el if parse_int(el.get_text()) > 0]

    return {
        'places': places[:6] if places else [],
        'trifecta': trifecta,
        'payout': payout,
    }

def get_race_time(jcd, rno):
    """レース発走時刻を取得"""
    r = get(f'{BASE}/racelist', params={'rno': rno, 'jcd': jcd, 'hd': TODAY})
    if not r:
        return '--:--'
    soup = BeautifulSoup(r.text, 'lxml')
    time_el = soup.select_one('.is-time, [class*="raceTime"], [class*="startTime"]')
    if time_el:
        t = time_el.get_text(strip=True)
        m = re.search(r'(\d{1,2}):(\d{2})', t)
        if m:
            return f'{int(m.group(1)):02d}:{m.group(2)}'
    return '--:--'

def scrape_venue(venue_id):
    """1場のデータをまとめて取得"""
    jcd = venue_id
    name = VENUE_NAMES.get(jcd, jcd)
    print(f'[{name}] 取得中...')

    race_nos, current_race = get_race_list(jcd)
    if not race_nos:
        print(f'  レースなし')
        return None

    wind = get_wind(jcd)
    print(f'  風: {wind["direction"]} {wind["speed"]}m 波{wind["wave"]}cm')

    races = []
    for rno in race_nos:
        print(f'  {rno}R 取得中...')
        status, result = get_race_status(jcd, rno, current_race)
        racers = get_racers(jcd, rno)
        race_time = get_race_time(jcd, rno)

        races.append({
            'race_no': rno,
            'time': race_time,
            'status': status,
            'racers': racers,
            'result': result,
        })
        time.sleep(0.8)

    return {
        'id': jcd,
        'name': name,
        'status': '開催中' if any(r['status'] in ('進行中', '待機中') for r in races) else '終了',
        'current_race': current_race,
        'wind': wind,
        'races': races,
    }

def main():
    print(f'=== ボートレースデータ取得 {DATE_LABEL} ===')
    venues_basic = get_active_venues()

    if not venues_basic:
        print('本日の開催場が見つかりません')
        venues_basic = [{'id': jcd, 'name': name} for jcd, name in VENUE_NAMES.items()]

    print(f'開催場: {[v["name"] for v in venues_basic]}')

    venues_data = []
    for v in venues_basic:
        result = scrape_venue(v['id'])
        if result:
            venues_data.append(result)
        time.sleep(1.0)

    output = {
        'date': DATE_LABEL,
        'generated_at': datetime.now(JST).isoformat(),
        'venues': venues_data,
    }

    out_path = Path(__file__).parent.parent / 'public' / 'data' / 'races.json'
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'\n✅ 保存完了: {out_path}')
    print(f'   場数: {len(venues_data)} / レース数: {sum(len(v["races"]) for v in venues_data)}')

if __name__ == '__main__':
    main()
