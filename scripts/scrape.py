"""
boatrace.jp から出走表・モーター・選手情報・結果をスクレイピングして
public/data/races.json を生成する

リクエスト数の目安:
  1場あたり: raceindex(1) + beforeinfo(1) + racelist×12 + raceresult×12 = 26
  14場開催時: 約364リクエスト → 約5分
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
    cleaned = re.sub(r'[^\d.]', '', str(text).strip())
    try:
        return float(cleaned)
    except ValueError:
        return default

def parse_int(text, default=0):
    if not text:
        return default
    cleaned = re.sub(r'[^\d]', '', str(text).strip())
    try:
        return int(cleaned)
    except ValueError:
        return default

def get_race_list(jcd):
    """raceindex から本日レース番号・発走時刻・ステータスを一括取得

    Returns: (race_nos, current_race, race_meta)
      race_meta: {rno: {'time': 'HH:MM', 'closed': bool}}
        closed=True → 「発売終了」（レース終了 or 進行中）
    """
    r = get(f'{BASE}/raceindex', params={'jcd': jcd, 'hd': TODAY})
    if not r or 'システムエラー' in r.text:
        return [], 1, {}
    soup = BeautifulSoup(r.text, 'lxml')

    race_meta = {}
    for row in soup.select('tr'):
        a = row.select_one('a[href*="rno="]')
        if not a:
            continue
        m = re.search(r'rno=(\d+)', a.get('href', ''))
        if not m:
            continue
        rno = int(m.group(1))
        tds = row.select('td')
        time_text = '--:--'
        closed = False
        for td in tds:
            t = td.get_text(strip=True)
            if re.match(r'^\d{1,2}:\d{2}$', t):
                time_text = t
            if t == '発売終了':
                closed = True
        race_meta[rno] = {'time': time_text, 'closed': closed}

    race_nos = sorted(race_meta.keys())
    if not race_nos:
        return [], 1, {}

    # 「発売終了」の最後のレースを現在レースとみなす
    closed_races = [r for r in race_nos if race_meta[r]['closed']]
    current = closed_races[-1] if closed_races else race_nos[0]

    return race_nos, current, race_meta

def get_weather_and_tenji(jcd, rno):
    """beforeinfo から風・天候・気温・水温・展示タイムを取得"""
    r = get(f'{BASE}/beforeinfo', params={'rno': rno, 'jcd': jcd, 'hd': TODAY})
    base = {
        'wind': {'speed': 0, 'direction': '不明', 'wave': 0},
        'weather': '晴', 'air_temp': None, 'water_temp': None, 'tenji': {},
    }
    if not r or 'システムエラー' in r.text:
        return base

    soup = BeautifulSoup(r.text, 'lxml')

    wind_speed_el = soup.select_one('.is-windSpeed, [class*="windSpeed"]')
    wind_dir_el   = soup.select_one('.is-windDirection, [class*="windDirection"]')
    wave_el       = soup.select_one('.is-wave, [class*="wave"]')
    base['wind']['speed']     = parse_float(wind_speed_el.get_text() if wind_speed_el else '0')
    base['wind']['direction'] = wind_dir_el.get_text(strip=True) if wind_dir_el else '不明'
    base['wind']['wave']      = parse_int(wave_el.get_text() if wave_el else '0')

    weather_el = soup.select_one('.is-weather, [class*="weather"]')
    if weather_el:
        base['weather'] = weather_el.get_text(strip=True)

    air_el   = soup.select_one('.is-airTemp, [class*="airTemp"]')
    water_el = soup.select_one('.is-waterTemp, [class*="waterTemp"]')
    if air_el:   base['air_temp']   = parse_float(air_el.get_text())
    if water_el: base['water_temp'] = parse_float(water_el.get_text())

    tenji = {}
    for row in soup.select('table tr, .is-timeRow'):
        cols = row.select('td')
        if len(cols) < 3:
            continue
        lane = parse_int(cols[0].get_text())
        if lane < 1 or lane > 6:
            continue
        tenji_time = parse_float(cols[1].get_text())
        tenji_st   = parse_float(cols[2].get_text())
        if tenji_time > 0:
            tenji[lane] = {'tenji_time': tenji_time, 'tenji_st': tenji_st}
    base['tenji'] = tenji
    return base

def parse_racers_and_time(soup):
    """racelist ページの soup から選手リストと発走時刻を一括取得（追加リクエストなし）"""
    # 発走時刻
    race_time = '--:--'
    time_el = soup.select_one('.is-time, [class*="raceTime"], [class*="startTime"]')
    if time_el:
        t = time_el.get_text(strip=True)
        m = re.search(r'(\d{1,2}):(\d{2})', t)
        if m:
            race_time = f'{int(m.group(1)):02d}:{m.group(2)}'

    # 選手
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

            no_el   = row.select_one('.racerNo, [class*="number"]')
            rank_el = row.select_one('.is-rank, [class*="rank"]')
            branch_el = row.select_one('[class*="branch"]')
            no     = no_el.get_text(strip=True) if no_el else ''
            rank   = rank_el.get_text(strip=True) if rank_el else 'B1'
            branch = branch_el.get_text(strip=True) if branch_el else ''

            motor_texts = [td.get_text(strip=True) for td in row.select('[class*="motor"]')]
            boat_texts  = [td.get_text(strip=True) for td in row.select('[class*="boat"]')]
            motor_no    = parse_int(motor_texts[0]) if motor_texts else 0
            motor_2rate = parse_float(motor_texts[1]) if len(motor_texts) > 1 else 0.0
            boat_no     = parse_int(boat_texts[0]) if boat_texts else 0
            boat_2rate  = parse_float(boat_texts[1]) if len(boat_texts) > 1 else 0.0

            st_el  = row.select_one('[class*="st"], .is-ST')
            fl_el  = row.select_one('[class*="fly"], [class*="late"]')
            st_avg = parse_float(st_el.get_text() if st_el else '0.18')
            flying = parse_int(fl_el.get_text() if fl_el else '0')

            course_stats = {}
            for i in range(1, 7):
                el = row.select_one(f'[class*="course{i}"], [data-course="{i}"]')
                course_stats[str(i)] = parse_float(el.get_text()) if el else 0.0

            course_detail = {
                k: {'win': v, 'place2': 0.0, 'place3': 0.0}
                for k, v in course_stats.items()
            }

            racers.append({
                'lane': lane, 'name': name, 'no': no,
                'rank': rank if rank in ('A1', 'A2', 'B1', 'B2') else 'B1',
                'branch': branch,
                'motor_no': motor_no, 'motor_2rate': motor_2rate,
                'boat_no': boat_no,   'boat_2rate': boat_2rate,
                'course_stats': course_stats,
                'course_detail': course_detail,
                'st_avg': st_avg if st_avg > 0 else 0.18,
                'tenji_time': None, 'tenji_st': None,
                'recent_results': [],
                'style': guess_style(course_stats),
                'local_rate': course_stats.get(str(lane), 0.0),
                'flying': flying, 'mae_zuke': False,
            })
        except Exception as e:
            print(f'    racer parse error: {e}')
            continue

    racers.sort(key=lambda x: x['lane'])
    return racers, race_time

def guess_style(course_stats):
    c1 = course_stats.get('1', 0)
    c2 = course_stats.get('2', 0)
    c3 = course_stats.get('3', 0) + course_stats.get('4', 0)
    if c1 >= 60: return '逃げ'
    if c2 >= 45: return '差し'
    if c3 >= 40: return 'まくり'
    if c2 >= 35 and c3 >= 30: return 'まくり差し'
    return '差し'

def get_result(jcd, rno):
    """レース確定結果を取得"""
    r = get(f'{BASE}/raceresult', params={'rno': rno, 'jcd': jcd, 'hd': TODAY})
    if not r or 'システムエラー' in r.text:
        return None
    soup = BeautifulSoup(r.text, 'lxml')

    result_el = soup.select_one('.result-pay, .is-result, [class*="result"]')
    if not result_el:
        return None

    trifecta = ''
    payout = 0
    for row in soup.select('[class*="trifecta"], [class*="sanren"]'):
        combo_el = row.select_one('[class*="combo"], [class*="num"]')
        pay_el   = row.select_one('[class*="pay"], [class*="amount"]')
        if combo_el and pay_el:
            trifecta = combo_el.get_text(strip=True)
            payout   = parse_int(pay_el.get_text())
            break

    if not trifecta:
        return None

    places_el = soup.select('[class*="place"] .num, [class*="arrive"] td')
    places = [parse_int(el.get_text()) for el in places_el if parse_int(el.get_text()) > 0]
    return {'places': places[:6], 'trifecta': trifecta, 'payout': payout}

def scrape_venue(jcd):
    """1場のデータをまとめて取得"""
    name = VENUE_NAMES.get(jcd, jcd)
    print(f'[{name}] 取得中...')

    race_nos, current_race, race_meta = get_race_list(jcd)
    if not race_nos:
        return None

    weather_info = get_weather_and_tenji(jcd, current_race)
    wind = weather_info['wind']
    print(f'  風:{wind["direction"]} {wind["speed"]}m / {weather_info["weather"]} / {len(race_nos)}R (現在{current_race}R)')

    races = []
    for rno in race_nos:
        meta = race_meta.get(rno, {})
        race_time = meta.get('time', '--:--')
        is_closed = meta.get('closed', False)  # 発売終了 = 進行中 or 終了

        # 出走表（全レース取得）
        r = get(f'{BASE}/racelist', params={'rno': rno, 'jcd': jcd, 'hd': TODAY})
        if r and 'システムエラー' not in r.text:
            soup = BeautifulSoup(r.text, 'lxml')
            racers, _ = parse_racers_and_time(soup)
        else:
            racers = []

        # 展示タイムを現在レースにマージ
        if rno == current_race:
            tenji = weather_info.get('tenji', {})
            for racer in racers:
                t = tenji.get(racer['lane'])
                if t:
                    racer['tenji_time'] = t['tenji_time']
                    racer['tenji_st']   = t['tenji_st']

        # 結果（発売終了のレースのみ取得）
        result = None
        if is_closed:
            result = get_result(jcd, rno)

        if result:
            status = '終了'
        elif is_closed:
            status = '進行中'  # 発売終了だが結果未確定
        else:
            status = '待機中'

        races.append({
            'race_no': rno, 'time': race_time,
            'status': status, 'racers': racers, 'result': result,
        })
        time.sleep(0.5)

    return {
        'id': jcd, 'name': name,
        'status': '開催中' if any(r['status'] in ('進行中', '待機中') for r in races) else '終了',
        'current_race': current_race,
        'wind': wind,
        'weather': weather_info['weather'],
        'air_temp': weather_info['air_temp'],
        'water_temp': weather_info['water_temp'],
        'races': races,
    }

def main():
    print(f'=== ボートレースデータ取得 {DATE_LABEL} ===')

    venues_data = []
    for jcd, name in VENUE_NAMES.items():
        result = scrape_venue(jcd)
        if result and result['races']:
            venues_data.append(result)
            print(f'  ✅ {name}: {len(result["races"])}R取得')
        else:
            print(f'  ─ {name}: 本日開催なし')
        time.sleep(0.5)

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
