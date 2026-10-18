/* KOYO LIVE: a zero-backend, source-attributed autumn foliage tracker.
 * Data is refreshed from static JSON. Camera video remains on publishers' sites.
 */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const REPO = 'Xenoah/map_autumn-leaves';
  const STATUS = {
    full: {text:'最盛期',color:'#d84c57',rank:0},
    peak: {text:'見頃',color:'#e68c4e',rank:1},
    starting: {text:'色づき始め',color:'#e5bd64',rank:2},
    green: {text:'青葉',color:'#6b9e7c',rank:3},
    past: {text:'見頃過ぎ',color:'#a39a90',rank:4},
    unknown: {text:'未確認',color:'#98a39c',rank:5}
  };
  const state = {spots:[],reports:{},data:null,query:'',pref:'',status:'all',cameraOnly:false,selectedId:null,map:null,layers:null,markers:new Map(),geopoint:null,lastDataFetch:null};
  let noticeTimeout=0;
  const safe = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const safeURL = url => {
    try {const u=new URL(url);return u.protocol==='https:' ? u.href : '#';}catch{return '#';}
  };
  function notify(message){const node=$('toast');node.textContent=message;node.classList.add('visible');clearTimeout(noticeTimeout);noticeTimeout=setTimeout(()=>node.classList.remove('visible'),2800);}
  function tokyoDate(date = new Date()) {return new Intl.DateTimeFormat('ja-JP',{timeZone:'Asia/Tokyo',year:'numeric',month:'2-digit',day:'2-digit',weekday:'short'}).format(date);}
  function fmtDate(s){if(!s)return '未確認';const d=new Date(s.length===10?s+'T00:00:00+09:00':s);return Number.isNaN(d.getTime())?'未確認':new Intl.DateTimeFormat('ja-JP',{timeZone:'Asia/Tokyo',year:'numeric',month:'2-digit',day:'2-digit'}).format(d);}
  function elapsedDays(s){if(!s)return Infinity;const d=new Date(s+'T00:00:00+09:00');return Number.isNaN(d.getTime())?Infinity:Math.max(0,Math.floor((Date.now()-d.getTime())/86400000));}
  function currentReport(spot){const report=state.reports[spot.id];if(!report)return {status:'unknown',report:null,stale:false};const age=elapsedDays(report.observedAt);return {status:age<=9 && STATUS[report.status]? report.status : 'unknown', report,stale:age>9,age};}
  function sortedSpots(){return [...state.spots].sort((a,b)=>STATUS[currentReport(a).status].rank-STATUS[currentReport(b).status].rank || a.prefecture.localeCompare(b.prefecture,'ja') || a.name.localeCompare(b.name,'ja'));}
  function visibleSpots(){const words=state.query.trim().toLocaleLowerCase('ja');return sortedSpots().filter(s=>{
    const status=currentReport(s).status;
    return (!words || `${s.name} ${s.prefecture} ${s.description}`.toLocaleLowerCase('ja').includes(words)) &&
      (!state.pref || state.pref===s.prefecture) &&
      (!state.cameraOnly || !!s.camera) &&
      (state.status==='all'||state.status===status);
  });}
  function createSelectOptions(){const prefectures=[...new Set(state.spots.map(s=>s.prefecture))];$('prefecture').innerHTML='<option value="">すべての地域</option>'+prefectures.map(p=>`<option value="${safe(p)}">${safe(p)}${p==='東京'?'都':(p==='京都'||p==='大阪')?'府':'県'}</option>`).join('');}
  function renderFilters(){const labels=[['all','すべて'],['full','最盛期'],['peak','見頃'],['starting','色づき始め'],['green','青葉'],['past','終盤'],['unknown','未確認']];
    $('status-filters').innerHTML=labels.map(([key,label])=>{
      const n=key==='all'?state.spots.length:state.spots.filter(s=>currentReport(s).status===key).length;
      const color=key==='all'?'#b6c4b5':STATUS[key].color;
      return `<button type="button" class="status-chip ${state.status===key?'active':''}" data-status="${key}" aria-pressed="${state.status===key?'true':'false'}" style="--c:${color}"><span class="dot"></span>${label}<small>${n}</small></button>`;
    }).join('');
  }
  function cameraOpen(spot){if(!spot?.camera)return;const url=safeURL(spot.camera.url);if(url==='#')return;window.open(url,'_blank','noopener,noreferrer,width=1100,height=750');}
  function renderList(){const visible=visibleSpots();$('results-count').textContent=`${visible.length} / ${state.spots.length} 地点`;
    $('results-list').innerHTML=visible.length?visible.map(s=>{
      const r=currentReport(s),meta=STATUS[r.status];
      return `<button class="place-row ${state.selectedId===s.id?'active':''}" type="button" data-id="${safe(s.id)}" style="--c:${meta.color}">
        <span class="place-icon">${r.status==='green'?'🌿':r.status==='past'?'🍂':r.status==='unknown'?'⌖':'🍁'}</span>
        <span class="place-info"><span class="place-name">${safe(s.name)}</span><span class="place-meta">${safe(s.prefecture)} ${s.elevation?`<span class="bullet">●</span> ${s.elevation}m`:''} ${s.camera?'<span class="place-cam" title="ライブカメラあり">📹</span>':''}</span></span>
        <span class="place-status"><i></i>${meta.text}</span><span class="place-arrow">›</span></button>`;
    }).join(''):'<div class="empty-results">条件に合うスポットがないみたい。<br>フィルターを解除して探し直してみて。</div>';
  }
  function updateStats(){let peak=0;for(const s of state.spots){if(['full','peak'].includes(currentReport(s).status))peak++}
    $('peak-count').textContent=peak;$('camera-count').textContent=state.spots.filter(s=>!!s.camera).length;
    $('total-count').textContent=state.spots.length+' LOCATIONS';
    const generated=state.data?.generatedAt;
    $('updated-small').textContent=generated?new Intl.DateTimeFormat('ja-JP',{timeZone:'Asia/Tokyo',hour:'2-digit',minute:'2-digit'}).format(new Date(generated)):'未取得';
    $('sync-caption').textContent=generated?'システム確認 '+fmtDate(generated)+' JST':'公開初期データを表示';
  }
  function pinIcon(spot,status){const color=STATUS[status].color;
    return L.divIcon({className:`leaflet-div-icon marker-${status} ${state.selectedId===spot.id?'marker-selected':''}`,html:`<div class="camera-pin" style="--c:${color}"><span class="marker-core"></span>${spot.camera?`<button class="marker-cam" data-camera="${safe(spot.id)}" type="button" aria-label="${safe(spot.name)}のライブカメラを別ウィンドウで開く" title="ライブカメラを別ウィンドウで開く">📹</button>`:''}</div>`,iconSize:[44,50],iconAnchor:[20,39]});
  }
  function renderMap(){if(!state.map)return;state.layers.clearLayers();state.markers.clear();const visible=visibleSpots();for(const spot of visible){
      const status=currentReport(spot).status,marker=L.marker([spot.lat,spot.lon],{icon:pinIcon(spot,status),riseOnHover:true});
      marker.on('click',()=>selectSpot(spot.id));
      marker.on('add',()=>{const btn=marker.getElement()?.querySelector('.marker-cam');if(btn){L.DomEvent.disableClickPropagation(btn);L.DomEvent.disableScrollPropagation(btn);btn.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();cameraOpen(spot)});}});
      state.layers.addLayer(marker);state.markers.set(spot.id,marker);
    }}
  function weatherText(code){if(code===0)return '快晴';if(code===1||code===2)return '晴れ';if(code===3)return '曇り';if(code>=45&&code<=48)return '霧';if(code>=51&&code<=67)return '雨';if(code>=71&&code<=86)return '雪';if(code>=95)return '雷雨';return '天気確認中'}
  const weatherCache=new Map();
  async function loadWeather(spot){const holder=$('weather-content');if(!holder)return;
    const cached=weatherCache.get(spot.id);
    if(cached && Date.now()-cached.time<600000){setWeather(cached.data,spot.id);return}
    const url=new URL('https://api.open-meteo.com/v1/forecast');
    url.search=new URLSearchParams({latitude:String(spot.lat),longitude:String(spot.lon),current:'temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m',timezone:'Asia/Tokyo',forecast_days:'1'}).toString();
    try{const response=await fetch(url.toString(),{signal:AbortSignal.timeout(9500)});if(!response.ok)throw new Error('weather HTTP '+response.status);const data=await response.json();if(!data.current||typeof data.current.temperature_2m!=='number')throw new Error('invalid');weatherCache.set(spot.id,{time:Date.now(),data});setWeather(data,spot.id)}
    catch{const h=$('weather-content');if(h&&state.selectedId===spot.id)h.textContent='現地の天気情報を取得できませんでした';}
  }
  function setWeather(data,id){if(state.selectedId!==id)return;const n=$('weather-content');if(!n)return;const w=data.current;n.innerHTML=`<strong>☀ ${safe(weatherText(w.weather_code))}　${Math.round(w.temperature_2m)}℃</strong><span>風速 ${Math.round(w.wind_speed_10m)} km/h</span>`;}
  function detailHTML(spot){const {status,report,stale,age}=currentReport(spot),meta=STATUS[status];const camera=!!spot.camera;
    const googleMaps='https://www.google.com/maps/search/?api=1&query='+encodeURIComponent(`${spot.lat},${spot.lon}`);
    const submit='https://github.com/'+REPO+'/issues/new?template=koyo-report.yml&title='+encodeURIComponent(`[紅葉レポート] ${spot.name}`);
    const source=report?.sourceUrl && safeURL(report.sourceUrl)!=='#' ? `<a href="${safeURL(report.sourceUrl)}" target="_blank" rel="noopener noreferrer">情報源 ↗</a>`:'<span>情報源なし</span>';
    const dateInfo=report?`最終報告：${fmtDate(report.observedAt)} (${age}日前)${stale?'　※更新期限超過':''}`:'現時点で確認済みの色づき報告がありません';
    const sourceType=report?.kind==='official'?'公式観測':report?.kind==='community'?'現地レポート':report?.kind==='third_party'?'公開情報':'情報待ち';
    return `<div class="detail-accent" style="--c:${meta.color}"></div><div class="detail-inner"><div class="detail-head"><span class="detail-kicker">${safe(spot.prefecture).toUpperCase()} / AUTUMN GUIDE</span><button id="detail-close" class="detail-close" type="button" aria-label="詳細を閉じる">×</button></div>
      <h3 class="detail-name">${safe(spot.name)}</h3><div class="detail-tags"><span class="detail-tag main" style="--c:${meta.color}"><i></i>${meta.text}</span><span class="detail-tag">${sourceType}</span>${camera?`<span class="detail-tag">📹 ${spot.camera.mode==='directory'?'配信元のカメラ案内':'ライブカメラあり'}</span>`:''}</div>
      <p class="detail-date ${stale?'detail-stale':''}">${dateInfo}</p><p class="detail-description">${safe(spot.description)}<br>例年の目安：${safe(spot.typicalSeason)}</p>
      <div class="detail-weather"><span id="weather-content" class="weather-loading">現地の天気を取得中...</span></div>
      <div class="detail-actions ${camera?'has-camera':''}">${camera?`<button type="button" class="detail-btn cam" id="detail-camera">📹 ${spot.camera.mode==='directory'?'カメラ案内を開く':'ライブカメラを見る'} ↗</button>`:''}<a class="detail-btn" target="_blank" rel="noopener noreferrer" href="${safeURL(googleMaps)}">⌖ 地図で開く ↗</a><a class="detail-btn secondary" target="_blank" rel="noopener noreferrer" href="${safeURL(submit)}">✎ 状況を報告 ↗</a></div>
      <div class="detail-extra"><span>${safe(report?.sourceName||'未確認')} ${stale?' / 古い報告':''}</span>${source}</div>
      <div class="detail-spot-id"><span>スポットID</span><code>${safe(spot.id)}</code><button id="copy-spot-id" type="button" title="スポットIDをコピー">コピー</button></div></div>`;
  }
  function updatePinSelection(){state.markers.forEach((marker,id)=>{marker.getElement()?.classList.toggle('marker-selected',id===state.selectedId);});}
  function bindDetailActions(spot){$('detail-close')?.addEventListener('click',closeDetail);$('detail-camera')?.addEventListener('click',()=>cameraOpen(spot));$('copy-spot-id')?.addEventListener('click',()=>{if(navigator.clipboard?.writeText){navigator.clipboard.writeText(spot.id).then(()=>notify('スポットIDをコピーしました')).catch(()=>notify('コピーできませんでした'));}else{notify('スポットIDを選択してコピーしてください');}});}
  function selectSpot(id){const spot=state.spots.find(s=>s.id===id);if(!spot)return;state.selectedId=id;
    $('detail').innerHTML=detailHTML(spot);$('detail').hidden=false;bindDetailActions(spot);
    if(state.map){state.map.flyTo([spot.lat,spot.lon],Math.max(10,state.map.getZoom()),{duration:.55});updatePinSelection();}
    $('sidebar').classList.remove('open');$('mobile-list-toggle').setAttribute('aria-expanded','false');$('mobile-list-text').textContent='一覧を表示';renderList();loadWeather(spot);
  }
  function closeDetail(){state.selectedId=null;$('detail').hidden=true;$('detail').innerHTML='';renderList();if(state.map)updatePinSelection();}
  function render(){renderFilters();renderList();updateStats();renderMap();if(state.selectedId){const s=state.spots.find(s=>s.id===state.selectedId);if(s){$('detail').innerHTML=detailHTML(s);bindDetailActions(s);loadWeather(s);}}}
  function initMap(){if(typeof L==='undefined'){$('map-fallback').innerHTML='<span class="fallback-emoji">🍁</span><span>地図ライブラリを取得できません</span><small>通信環境を確認してください。スポット一覧は利用できます。</small>';return;}
    try{state.map=L.map('map',{center:[36.17,139.30],zoom:8,zoomControl:false,minZoom:5,maxZoom:17,preferCanvas:true});
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors',crossOrigin:true}).addTo(state.map);
      state.map.attributionControl.setPrefix('');state.layers=L.layerGroup().addTo(state.map);$('map-fallback').remove();renderMap();
      L.control.zoom({position:'bottomright'}).addTo(state.map);
    }catch(e){console.warn('Map init failed',e);state.map=null;}
  }
  async function loadLive({silent=false}={}){
    const start=Date.now();$('refresh').classList.add('spin');
    try{
      if(location.protocol==='file:'){if(!silent)notify('ローカル表示です。公開後は自動でデータを更新します');return;}
      const suffix='?v='+Date.now();
      const [a,b]=await Promise.all([fetch('data/spots.json'+suffix,{cache:'no-store'}),fetch('data/live.json'+suffix,{cache:'no-store'})]);
      if(!a.ok||!b.ok)throw new Error('HTTP error');
      const [spots,data]=await Promise.all([a.json(),b.json()]);
      if(!Array.isArray(spots)||!data?.reports||typeof data.reports!=='object')throw new Error('invalid JSON');
      const old=state.data?.generatedAt;
      state.spots=spots;state.reports=data.reports;state.data=data;state.lastDataFetch=new Date();createSelectOptions();render();
      if(!silent)notify(data.generatedAt===old?'確認完了。情報は最新の取得結果です':'最新データを読み込みました');
    }catch(e){if(!silent)notify('最新データを取得できません。手元の情報を表示しています');console.warn('Could not update data',e)}
    finally{setTimeout(()=>$('refresh').classList.remove('spin'),Math.max(250,550-(Date.now()-start)))}
  }
  function wireControls(){
    $('search').addEventListener('input',e=>{state.query=e.target.value;renderFilters();renderList();renderMap()});
    $('prefecture').addEventListener('change',e=>{state.pref=e.target.value;renderList();renderMap()});
    $('camera-only').addEventListener('change',e=>{state.cameraOnly=e.target.checked;renderList();renderMap()});
    $('status-filters').addEventListener('click',e=>{const button=e.target.closest('button[data-status]');if(!button)return;state.status=button.dataset.status;renderFilters();renderList();renderMap()});
    $('clear-filters').addEventListener('click',()=>{state.status='all';state.query='';state.pref='';state.cameraOnly=false;$('search').value='';$('prefecture').value='';$('camera-only').checked=false;render()});
    $('results-list').addEventListener('click',e=>{const button=e.target.closest('button[data-id]');if(button)selectSpot(button.dataset.id)});
    $('refresh').addEventListener('click',()=>loadLive());
    $('fit').addEventListener('click',()=>{if(!state.map)return;const p=visibleSpots();if(p.length)state.map.fitBounds(L.latLngBounds(p.map(s=>[s.lat,s.lon])),{padding:[45,45],maxZoom:11})});
    $('locate').addEventListener('click',()=>{if(!navigator.geolocation){notify('位置情報に対応していません');return}navigator.geolocation.getCurrentPosition(p=>{state.map?.flyTo([p.coords.latitude,p.coords.longitude],10);notify('現在地の周辺を表示しています')},()=>notify('位置情報の利用が許可されていません'),{timeout:9000,enableHighAccuracy:false})});
    $('mobile-list-toggle').addEventListener('click',()=>{const el=$('sidebar'),open=el.classList.toggle('open');$('mobile-list-toggle').setAttribute('aria-expanded',String(open));$('mobile-list-text').textContent=open?'一覧を閉じる':'一覧を表示'});
    document.addEventListener('keydown',e=>{if(e.key==='/' && !['INPUT','TEXTAREA'].includes(document.activeElement?.tagName)){e.preventDefault();$('search').focus();}if(e.key==='Escape'){closeDetail();$('sidebar').classList.remove('open')}});
  }
  function main(){let bootstrap={spots:[],live:{reports:{},generatedAt:null}};
    try{bootstrap=JSON.parse($('bootstrap-data').textContent);}catch(e){console.warn('Missing offline data',e)}
    state.spots=bootstrap.spots||[];state.reports=bootstrap.live?.reports||{};state.data=bootstrap.live||null;
    $('today-label').textContent=tokyoDate().replace(/\//g,'.').toUpperCase();const year=new Intl.DateTimeFormat('en',{timeZone:'Asia/Tokyo',year:'numeric'}).format(new Date());$('season-year').textContent=year;$('map-kicker-year').textContent=year;
    createSelectOptions();wireControls();render();initMap();
    loadLive({silent:true});setInterval(()=>loadLive({silent:true}),5*60*1000);
    // Freshness changes at midnight, even when source data is unchanged.
    setInterval(()=>{renderFilters();renderList();updateStats();renderMap()},60*60*1000);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',main);else main();
})();
