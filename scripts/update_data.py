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
    except Exception:
        return False  # Fail closed: no official crawl without robots permission.

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
    community,diagnostic_community=community_reports(spots)
    payload={'generatedAt':iso_now(), 'schemaVersion':1,
             'sources':{'nikkoOfficial':diagnostic_official,'communityReports':diagnostic_community},
             'reports':merge(seeds,official,community)}
    (DATA/'live.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Wrote data/live.json:',len(payload['reports']),'reports',payload['sources'])

if __name__=='__main__':main()
