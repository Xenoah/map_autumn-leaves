#!/usr/bin/env python3
"""Merge source-attributed foliage facts into one static data file.

Only a short status and timestamp are extracted. No third-party photos,
site layout or descriptive text is reproduced.
"""
from __future__ import annotations
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
NIKKO='https://www.nikko-kankou.org/flowering/autumn-leaves'
UA='KoyoLiveMap/1.1 (+https://github.com/Xenoah/map_autumn-leaves; factual status only)'
MAP={'◎':'full','〇':'peak','◯':'peak','○':'peak','△':'starting','✕':'green','×':'green','▼':'past'}
ISSUE_STATUSES={'青葉':'green','色づき始め':'starting','見頃':'peak','最盛期':'full','落葉・見頃過ぎ':'past'}
DATE_RE=re.compile(r'最終更新日\s*[：:]\s*(20\d{2})年\s*(\d{1,2})月\s*(\d{1,2})日')
STATUS_RE=re.compile(r'現在の状況\s*[：:]\s*([◎〇◯○△✕×▼])')

def iso_now(): return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')

def json_read(path): return json.loads(Path(path).read_text(encoding='utf-8'))

def web_json(url, token=''):
    headers={'User-Agent':UA, 'Accept':'application/vnd.github+json'}
    if token: headers['Authorization']='Bearer '+token
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers),timeout=18) as r:
        return json.load(r)

def permitted(url):
    parsed=urllib.parse.urlparse(url)
    robots_url=f'{parsed.scheme}://{parsed.netloc}/robots.txt'
    rp=urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        # RobotFileParser.read() has no configurable network timeout and may
        # stall the scheduled Pages release. Fetch and parse with a hard timeout.
        req=urllib.request.Request(robots_url,headers={'User-Agent':UA})
        with urllib.request.urlopen(req,timeout=8) as response:
            if response.status!=200:
                return False
            body=response.read(100_000).decode('utf-8',errors='replace')
        rp.parse(body.splitlines())
        return rp.can_fetch(UA,url)
    except urllib.error.HTTPError as e:
        # RFC 9309: a missing robots.txt (404, 410 and other 4xx) places no
        # restriction. 401/403 and 429/5xx are treated as "do not crawl".
        return 400<=e.code<500 and e.code not in (401,403,429)
    except Exception:
        return False  # Fail closed: timeouts and network errors mean no crawl.

def extract_nikko(text, spots):
    """Parse status glyph + publication date from readable page text.

    Tolerates changes in HTML wrappers, spacing and Japanese bracket variants.
    Never infer status from weather; only explicit official glyphs.
    """
    compact=re.sub(r'\s+',' ',text).replace('【','〖').replace('】','〗')
    aliases={s['id']:s['nikkoAlias'] for s in spots if 'nikkoAlias' in s}
    reports={}
    previous_end=0
    for m in STATUS_RE.finditer(compact):
        preceding=compact[max(previous_end,m.start()-360):m.start()]
        matches=[(preceding.rfind(alias),id) for id,alias in aliases.items() if preceding.rfind(alias)>=0]
        if not matches:
            previous_end=m.end()
            continue
        nearest_index,id=max(matches)
        if len(preceding)-nearest_index>210:
            previous_end=m.end()
            continue
        end=compact.find('最終更新日',m.end(),m.end()+600)
        if end<0:
            previous_end=m.end()
            continue
        date_match=DATE_RE.search(compact[end:end+65])
        if not date_match:
            previous_end=m.end()
            continue
        try: day=dt.date(*map(int,date_match.groups())).isoformat()
        except ValueError:
            previous_end=m.end()
            continue
        reports[id]={'status':MAP[m.group(1)],'observedAt':day,
                     'kind':'official','sourceName':'日光市観光協会','sourceUrl':NIKKO,
                     'note':'公式サイトの色づき段階を反映（現地観測時刻とは異なる場合あり）'}
        previous_end=end+date_match.end()
    return reports

def official_reports(spots):
    if os.getenv('SKIP_OFFICIAL')=='1': return {}, 'skipped'
    if not permitted(NIKKO): return {}, 'robots-denied-or-unavailable'
    try:
        req=urllib.request.Request(NIKKO,headers={'User-Agent':UA,'Accept':'text/html; charset=utf-8'})
        with urllib.request.urlopen(req,timeout=22) as r:
            if r.status!=200: return {},'http-'+str(r.status)
            content=r.read(1_500_000)
            html=content.decode('utf-8',errors='replace')
        from bs4 import BeautifulSoup
        soup=BeautifulSoup(html,'html.parser')
        for tag in soup(['script','style','noscript']):tag.decompose()
        found=extract_nikko(soup.get_text(' ',strip=True),spots)
        if len(found)<3:
            return {},'parser-no-match'
        return found,'ok ('+str(len(found))+')'
    except Exception as e:
        return {},'fetch-failed:'+type(e).__name__

# ---------------------------------------------------------------------------
# Generic official pages: tourism associations that publish a stage word per
# spot. Each source is checked against robots.txt on every run (fail closed),
# only the stage + date are kept, and the original page is linked.
# Sites whose terms forbid non-browser access or reproduction (e.g. tenki.jp,
# 京都観光Navi) are intentionally absent.
# ---------------------------------------------------------------------------
STAGE_RE=re.compile(
    r'(?P<past>見ごろ終了|見頃終了|見ごろ過ぎ|見頃過ぎ|見ごろ終盤|見頃終盤|散り始め|落葉|終盤)'
    r'|(?P<starting>見ごろ間近|見頃間近|見ごろ近し|見頃近し|色づき始め|色付き始め|色づきはじめ|色付きはじめ)'
    r'|(?P<full>最盛期)'
    r'|(?P<peak>見ごろ|見頃)'
    r'|(?P<green>青葉)')
REPORT_MAX_AGE_DAYS=30  # Last season's entries stay off the map.

OFFICIAL_SOURCES=[
    {'key':'iwateTourism','name':'岩手県観光協会（いわての旅）',
     'url':'https://iwatetabi.jp/flower/autumnleaves/','prefecture':'岩手',
     # Table rows: 市町村 / スポット / 色づき状況 / 例年の見頃; one page-wide date.
     'mode':'adjacent','window':30,
     'pageDate':r'最終更新\s*[：:]\s*(20\d{2})年\s*(\d{1,2})月\s*(\d{1,2})日'},
    {'key':'fukuokaTourism','name':'福岡県観光連盟（クロスロードふくおか）',
     'url':'https://www.crossroadfukuoka.jp/feature/autumn','prefecture':'福岡',
     # 「色づき状況：黒門周辺は青葉（2026/10/29）」 per spot.
     'mode':'labelled','window':220,
     'label':r'色づき状況\s*[：:]\s*([^（(]{0,80})[（(]\s*(20\d{2})\s*[/／.]\s*(\d{1,2})\s*[/／.]\s*(\d{1,2})\s*[）)]'},
]

def stage_of(text):
    m=STAGE_RE.search(text or '')
    return m.lastgroup if m else None

def spot_aliases(spot):
    """Distinctive name parts. Short pieces (<3 chars) are too ambiguous."""
    parts=re.split(r'[・･（）()\s]+',spot['name'])
    # 「東公園 (福岡市)」「中津川 (岩手県)」: place qualifiers are not spot names.
    aliases={p for p in parts if len(p)>=3 and not re.search(r'[市町村区郡県府国]$',p)}
    aliases.update(spot.get('aliases',[]))
    return sorted(aliases,key=len,reverse=True)

def alias_pattern(alias):
    # 「八幡平市」 is a municipality, not the 八幡平 spot.
    return re.compile(re.escape(alias)+r'(?![市町村区郡])')

def valid_day(y,m,d,today):
    try: day=dt.date(int(y),int(m),int(d))
    except ValueError: return None
    if day>today or (today-day).days>REPORT_MAX_AGE_DAYS: return None
    return day

def extract_adjacent(text,spots,source,today):
    """Stage word must follow the spot name closely (table-like layout)."""
    date=re.search(source['pageDate'],text)
    if not date: return {},'no-page-date'
    day=valid_day(*date.groups(),today)
    if not day: return {},'page-date-out-of-range'
    found={}
    for spot in spots:
        stages=set()
        for alias in spot_aliases(spot):
            for m in alias_pattern(alias).finditer(text):
                after=text[m.end():m.end()+source['window']]
                hit=STAGE_RE.search(after)
                # 「10月下旬～」 is the next column/row: this row had no stage word.
                if hit and not re.search(r'[月～〜]',after[:hit.start()]): stages.add(hit.lastgroup)
        if len(stages)==1:  # Conflicting mentions are skipped, never guessed.
            found[spot['id']]=(stages.pop(),day)
    return found,None

def extract_labelled(text,spots,source,today):
    """「色づき状況：…（日付）」 labels.

    Each entry starts with its heading (the spot name) and may mention other
    places in its description, so the first spot name after the previous
    label owns the status.
    """
    patterns=[(spot['id'],alias_pattern(a)) for spot in spots for a in spot_aliases(spot)]
    found={}
    previous_end=0
    for m in re.finditer(source['label'],text):
        start=max(previous_end,m.start()-source['window'])
        segment=text[start:m.start()]
        best=None
        for spot_id,pattern in patterns:
            hit=pattern.search(segment)
            if hit and (best is None or hit.start()<best[0]): best=(hit.start(),spot_id)
        previous_end=m.end()
        stage=stage_of(m.group(1))
        day=valid_day(m.group(2),m.group(3),m.group(4),today)
        if best and stage and day:
            current=found.get(best[1])
            if current is None or day>current[1]: found[best[1]]=(stage,day)
    return found,None

def page_text(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html'})
    with urllib.request.urlopen(req,timeout=22) as r:
        if r.status!=200: raise urllib.error.HTTPError(url,r.status,'status',r.headers,None)
        content=r.read(2_000_000)
    from bs4 import BeautifulSoup
    soup=BeautifulSoup(content,'html.parser')  # Bytes: honours the page's charset.
    for tag in soup(['script','style','noscript']):tag.decompose()
    return soup

def extract_source(text,spots,source,today):
    local=[s for s in spots if s['prefecture']==source['prefecture']]
    if source['mode']=='adjacent': rows,error=extract_adjacent(text,local,source,today)
    else: rows,error=extract_labelled(text,local,source,today)
    if error: return {},error
    reports={spot_id:{'status':stage,'observedAt':day.isoformat(),'kind':'official',
                      'sourceName':source['name'],'sourceUrl':source['url'],
                      'note':'公式サイトの色づき表記を反映（掲載日）'}
             for spot_id,(stage,day) in rows.items()}
    return reports,None

def regional_reports(spots,today=None):
    today=today or dt.datetime.now(ZoneInfo('Asia/Tokyo')).date()
    reports,diagnostics={},{}
    for source in OFFICIAL_SOURCES:
        if os.getenv('SKIP_OFFICIAL')=='1':
            diagnostics[source['key']]='skipped';continue
        if not permitted(source['url']):
            diagnostics[source['key']]='robots-denied-or-unavailable';continue
        try:
            text=re.sub(r'\s+',' ',page_text(source['url']).get_text(' ',strip=True))
            found,error=extract_source(text,spots,source,today)
            diagnostics[source['key']]=error or ('ok ('+str(len(found))+')' if found else 'parser-no-match')
            reports.update(found)
        except Exception as e:
            diagnostics[source['key']]='fetch-failed:'+type(e).__name__
    return reports,diagnostics

# ---------------------------------------------------------------------------
# JMA phenology (生物季節観測): one reference tree per weather office. These
# are dated events at the office, shown as their own layer. They are never
# copied onto nearby tourist spots.
# ---------------------------------------------------------------------------
JMA_BASE='https://www.data.jma.go.jp/sakura/data/'
JMA_EVENTS=[('kaedeKoyo','phn_014.html'),('ichouKoyo','phn_012.html'),
            ('kaedeRakuyo','phn_015.html'),('ichouRakuyo','phn_013.html')]
AMEDAS_TABLE='https://www.jma.go.jp/bosai/amedas/const/amedastable.json'
JMA_DATE_RE=re.compile(r'(\d{1,2})\s*月\s*(\d{1,2})\s*日')

def parse_jma_table(soup,year):
    """Return {station: date or None} for `year` from a phn_*.html table.

    Header lists years in column order; each year spans 観測日/平年差/昨年差.
    """
    table=soup.find('table')
    if table is None: return None
    rows=table.find_all('tr')
    years=[]
    for row in rows[:3]:
        years+= [int(y) for y in re.findall(r'(20\d{2})年',row.get_text(' '))]
    if year not in years: return None
    column=1+3*years.index(year)
    out={}
    for row in rows:
        cells=[c.get_text(' ',strip=True) for c in row.find_all(['td','th'])]
        if len(cells)<=column or not cells[0] or re.search(r'地点|20\d{2}年|観測日',cells[0]): continue
        m=JMA_DATE_RE.search(cells[column])
        day=None
        if m:
            try: day=dt.date(year,int(m.group(1)),int(m.group(2))).isoformat()
            except ValueError: day=None
        out[cells[0].replace(' ','').replace('　','')]=day
    return out

def amedas_positions():
    if not permitted(AMEDAS_TABLE): return {}
    table=web_json(AMEDAS_TABLE)
    positions={}
    for code,info in sorted(table.items()):
        name=info.get('kjName');lat=info.get('lat');lon=info.get('lon')
        if not name or not isinstance(lat,list) or not isinstance(lon,list) or len(lat)<2 or len(lon)<2: continue
        point=[round(lat[0]+lat[1]/60,4),round(lon[0]+lon[1]/60,4)]
        # Weather offices (type A) win when a name is shared with another site.
        if name not in positions or info.get('type')=='A': positions[name]=point
    return positions

def jma_phenology(previous=None,today=None):
    today=today or dt.datetime.now(ZoneInfo('Asia/Tokyo')).date()
    previous=previous or {}
    if os.getenv('SKIP_OFFICIAL')=='1': return previous or None,'skipped'
    events={}
    status=[]
    failed=set()
    for key,page in JMA_EVENTS:
        url=JMA_BASE+page
        if not permitted(url): status.append(key+':robots');failed.add(key);continue
        try:
            parsed=parse_jma_table(page_text(url),today.year)
            if parsed is None: status.append(key+':no-table');failed.add(key);continue
            for name,day in parsed.items(): events.setdefault(name,{})[key]=day
            status.append(key+':ok')
        except Exception as e:
            status.append(key+':'+type(e).__name__);failed.add(key)
    if not events: return previous or None,'unavailable ('+', '.join(status)+')'
    known={s['name']:[s['lat'],s['lon']] for s in previous.get('stations',[])}
    # A page that failed this run keeps this season's earlier dates.
    carried={s['name']:s.get('events',{}) for s in previous.get('stations',[])} if previous.get('year')==today.year else {}
    try: positions=amedas_positions()
    except Exception: positions={}
    stations=[]
    unplaced=[]
    for name,record in events.items():
        point=positions.get(name) or known.get(name)
        if not point: unplaced.append(name);continue
        observed={k:v for k,v in record.items() if v}
        observed.update({k:v for k,v in carried.get(name,{}).items() if k in failed and v})
        stations.append({'name':name,'lat':point[0],'lon':point[1],'events':observed})
    payload={'year':today.year,'sourceName':'気象庁 生物季節観測',
             'sourceUrl':JMA_BASE+'index.html',
             'note':'各気象台の標本木1本の観測日。周辺の観光地の状況を示すものではありません。',
             'stations':stations}
    if unplaced: status.append('no-position:'+'/'.join(unplaced))
    return payload,'ok ('+str(len(stations))+' stations, '+', '.join(status)+')'

def fields_from_issue(body):
    # GitHub issue form generated Markdown with headings.
    sections={}
    for section in re.split(r'(?m)^###\s+',body or ''):
        bits=section.split('\n',1)
        if len(bits)>1:
            sections[bits[0].strip()]=bits[1].split('\n###',1)[0].strip()
    return sections

def parse_verified_issue(issue, known_ids, today):
    if 'pull_request' in issue: return None
    labels={l.get('name','').lower() for l in issue.get('labels',[]) if isinstance(l,dict)}
    if 'verified' not in labels: return None
    if 'koyo-report' not in labels and not str(issue.get('title','')).startswith('[紅葉レポート]'): return None
    fields=fields_from_issue(issue.get('body') or '')
    spot_id=fields.get('スポットID','').splitlines()[0].strip().strip('`')
    if spot_id not in known_ids: return None
    status=ISSUE_STATUSES.get(fields.get('紅葉状況','').splitlines()[0].strip())
    if not status: return None
    date_string=fields.get('観測日（YYYY-MM-DD）','').splitlines()[0].strip()
    try: observed=dt.date.fromisoformat(date_string)
    except ValueError: return None
    if observed>today or observed<today-dt.timedelta(days=365): return None
    url=issue.get('html_url','')
    if not re.fullmatch(r'https://github\.com/[^/]+/[^/]+/issues/\d+',url):return None
    return spot_id, {'status':status,'observedAt':observed.isoformat(),
                     'kind':'community','sourceName':'承認済み現地レポート','sourceUrl':url,
                     'note':'現地報告（運営者が確認済み）','issueNumber':issue['number']}

def community_reports(spots):
    repository=os.getenv('GITHUB_REPOSITORY','')
    token=os.getenv('GITHUB_TOKEN','')
    if not repository:return {},'not-configured'
    today=dt.datetime.now(ZoneInfo('Asia/Tokyo')).date()
    ids={s['id'] for s in spots}
    newest={}
    try:
        for page in range(1,6):
            path=f'https://api.github.com/repos/{repository}/issues?state=open&labels=verified&per_page=100&page={page}'
            issues=web_json(path,token)
            if not isinstance(issues,list): break
            for issue in issues:
                parsed=parse_verified_issue(issue,ids,today)
                if not parsed: continue
                id,report=parsed
                current=newest.get(id)
                if current is None or (report['observedAt'],report['issueNumber'])>(current['observedAt'],current['issueNumber']):
                    newest[id]=report
            if len(issues)<100:break
        return newest,'ok ('+str(len(newest))+')'
    except Exception as e:return {},'api-failed:'+type(e).__name__

def merge(seeds, official, community):
    out=dict(seeds)
    # Source reports are only applied when strictly newer than existing data.
    # On equal-day reports official data wins over manually seeded data;
    # verified community is preferred on equal date as a newer corroboration.
    for candidate in (official,community):
        for id, report in candidate.items():
            previous=out.get(id)
            if not previous or report['observedAt']>=previous['observedAt']:
                out[id]=report
    return out

def main():
    spots=json_read(DATA/'spots.json')
    seeds=json_read(DATA/'seed-observations.json')
    official,diagnostic_official=official_reports(spots)
    regional,diagnostic_regional=regional_reports(spots)
    official={**regional,**official}  # Nikko keeps its dedicated parser.
    community,diagnostic_community=community_reports(spots)
    try: previous=json_read(DATA/'live.json').get('phenology') or {}
    except (OSError,ValueError): previous={}
    phenology,diagnostic_jma=jma_phenology(previous)
    payload={'generatedAt':iso_now(), 'schemaVersion':1,
             'sources':{'nikkoOfficial':diagnostic_official,**diagnostic_regional,
                        'jmaPhenology':diagnostic_jma,'communityReports':diagnostic_community},
             'reports':merge(seeds,official,community)}
    if phenology: payload['phenology']=phenology
    (DATA/'live.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Wrote data/live.json:',len(payload['reports']),'reports',payload['sources'])

if __name__=='__main__':main()
