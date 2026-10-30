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
  const STATUS_EMOJI = Object.freeze({full:'🍁',peak:'🍁',starting:'🍂',green:'🌿',past:'🍂',unknown:'❔'});
  const REGIONS = [
    ['北海道', '北海道'],
    ['東北', '青森 岩手 宮城 秋田 山形 福島'],
    ['関東', '茨城 栃木 群馬 埼玉 千葉 東京 神奈川'],
    ['甲信越', '新潟 山梨 長野'],
    ['北陸', '富山 石川 福井'],
    ['東海', '岐阜 静岡 愛知 三重'],
    ['近畿', '滋賀 京都 大阪 兵庫 奈良 和歌山'],
    ['中国', '鳥取 島根 岡山 広島 山口'],
    ['四国', '徳島 香川 愛媛 高知'],
    ['九州・沖縄', '福岡 佐賀 長崎 熊本 大分 宮崎 鹿児島 沖縄']
  ].map(([region,prefectures])=>({region,prefectures:prefectures.split(' ')}));
  const PREF_REGION = Object.fromEntries(REGIONS.flatMap(r=>r.prefectures.map(pref=>[pref,r.region])));
  const prefectureDisplay = p => p==='北海道'?'北海道':p==='東京'?'東京都':(p==='大阪'||p==='京都')?p+'府':p+'県';
  const state = {spots:[],reports:{},data:null,query:'',pref:'',status:'all',cameraOnly:false,selectedId:null,map:null,layers:null,markers:new Map(),geopoint:null,lastDataFetch:null,spotsLoadedAt:0,listLimit:120,initialBounds:null,tileLayer:null,lowData:true,detailCache:new Map(),prefectureLoads:new Map()};
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
  // Small array-based index for map pins; full details are fetched only when selected.
  function decodeCatalog(payload){
    if(payload?.schemaVersion!==1 || !Array.isArray(payload.rows) || !payload.rows.length)
      throw new Error('Unsupported compact index schema');
    return payload.rows.map(row=>{
      if(!Array.isArray(row) || row.length<9 || typeof row[0]!=='string' ||
         typeof row[3]!=='number' || typeof row[4]!=='number')
        throw new Error('Invalid compact spot');
      const spot={id:row[0],name:row[1],prefecture:row[2],lat:row[3],lon:row[4],candidate:!!row[7]};
      if(row[8])spot.elevation=row[8];
      if(row[5])spot.camera={url:row[5],mode:row[6]||'directory'};
      return spot;
    });
  }
  function withDetails(spot){return {...spot,...(state.detailCache.get(spot.id)||{})};}
  async function loadSpotDetails(spot){
    if(state.detailCache.has(spot.id) || location.protocol==='file:')return;
    const pref=spot.prefecture;
    if(!state.prefectureLoads.has(pref)){
      const uri='data/prefectures/'+encodeURIComponent(pref)+'.json';
      const pending=fetch(uri,{cache:'force-cache'})
        .then(r=>{if(!r.ok)throw new Error('detail HTTP '+r.status);return r.json();})
        .then(items=>{
          if(!Array.isArray(items))throw new Error('Invalid prefecture data');
          for(const item of items)if(item && typeof item.id==='string')state.detailCache.set(item.id,item);
        })
        .catch(err=>{
          state.prefectureLoads.delete(pref);
          console.warn('Could not fetch prefecture details',err);
          if(state.selectedId===spot.id)notify('地点の詳細情報を取得できませんでした');
        });
      state.prefectureLoads.set(pref,pending);
    }
    await state.prefectureLoads.get(pref);
    if(state.selectedId===spot.id){
      const selected=state.spots.find(s=>s.id===spot.id);
      if(selected)renderSelectedDetail(selected);
    }
  }
  function sortedSpots(){return [...state.spots].sort((a,b)=>STATUS[currentReport(a).status].rank-STATUS[currentReport(b).status].rank || a.prefecture.localeCompare(b.prefecture,'ja') || a.name.localeCompare(b.name,'ja'));}
  function visibleSpots(){const words=state.query.trim().toLocaleLowerCase('ja');return sortedSpots().filter(s=>{
    const status=currentReport(s).status;
    return (!words || `${s.name} ${s.prefecture} ${s.description||''}`.toLocaleLowerCase('ja').includes(words)) &&
      (!state.pref || (state.pref.startsWith('region:') ? PREF_REGION[s.prefecture]===state.pref.slice(7) : state.pref===s.prefecture)) &&
      (!state.cameraOnly || !!s.camera) &&
      (state.status==='all'||(state.status==='best'?['full','peak'].includes(status):state.status===status));
  });}
  function createSelectOptions(){
    const available=new Set(state.spots.map(s=>s.prefecture));
    const previous=state.pref;
    $('prefecture').innerHTML='<option value="">全国（すべての地域）</option>'+
      REGIONS.map(r=>{
        const prefs=r.prefectures.filter(p=>available.has(p));
        if(!prefs.length)return '';
        return '<optgroup label="'+safe(r.region)+'">'+
          '<option value="region:'+safe(r.region)+'">▸ '+safe(r.region)+'全体</option>'+
          prefs.map(p=>'<option value="'+safe(p)+'">'+safe(prefectureDisplay(p))+'</option>').join('')+
          '</optgroup>';
      }).join('');
    $('prefecture').value=previous;
  }
  function renderFilters(){const labels=[['all','すべて'],['best','見頃まとめ'],['full','最盛期'],['peak','見頃'],['starting','色づき始め'],['green','青葉'],['past','終盤'],['unknown','未確認']];
    $('status-filters').innerHTML=labels.map(([key,label])=>{
      const n=key==='all'?state.spots.length:state.spots.filter(s=>key==='best'?['full','peak'].includes(currentReport(s).status):currentReport(s).status===key).length;
      const color=key==='all'?'#b6c4b5':key==='best'?'#dc6e50':STATUS[key].color;
      return `<button type="button" class="status-chip ${state.status===key?'active':''}" data-status="${key}" aria-pressed="${state.status===key?'true':'false'}" style="--c:${color}"><span class="dot"></span>${label}<small>${n}</small></button>`;
    }).join('');
  }
  function cameraOpen(spot){if(!spot?.camera)return;const url=safeURL(spot.camera.url);if(url==='#')return;window.open(url,'_blank','noopener,noreferrer,width=1100,height=750');}
  function syncMobileControls(count=visibleSpots().length){
    const input=$('mobile-search');
    if(input && document.activeElement!==input && input.value!==state.query)input.value=state.query;
    const peaks=$('mobile-peaks');
    const cameras=$('mobile-cameras');
    if(peaks){peaks.classList.toggle('active',state.status==='best');peaks.setAttribute('aria-pressed',String(state.status==='best'));}
    if(cameras){cameras.classList.toggle('active',state.cameraOnly);cameras.setAttribute('aria-pressed',String(state.cameraOnly));}
    const results=$('mobile-results-count');
    if(results)results.textContent=count+'件';
    const toggle=$('mobile-list-toggle');
    if(toggle)$('mobile-list-text').textContent=$('sidebar').classList.contains('open')?'一覧を閉じる':`スポット一覧  ${count}件`;
  }
  function applySearchFilters({resetLimit=true}={}){
    if(resetLimit)state.listLimit=120;
    renderFilters();renderList();renderMap();
  }
  function renderList(){const visible=visibleSpots();$('results-count').textContent=`${visible.length} / ${state.spots.length} 地点`;
    const listed=visible.slice(0,state.listLimit);
    $('results-list').innerHTML=visible.length?listed.map(s=>{
      const r=currentReport(s),meta=STATUS[r.status];
      return `<button class="place-row ${state.selectedId===s.id?'active':''}" type="button" data-id="${safe(s.id)}" style="--c:${meta.color}">
        <span class="place-icon">${s.camera?'📹':STATUS_EMOJI[r.status]}</span>
        <span class="place-info"><span class="place-name">${safe(s.name)}</span><span class="place-meta">${safe(s.prefecture)} ${s.elevation?`<span class="bullet">●</span> ${s.elevation}m`:''} ${s.camera?'<span class="place-cam" title="ライブカメラあり">📹</span>':''}</span></span>
        <span class="place-status"><i></i>${meta.text}</span><span class="place-arrow">›</span></button>`;
    }).join('')+(visible.length>listed.length?`<button type="button" class="results-more" id="results-more">さらに表示（残り ${visible.length-listed.length} 件）</button>`:''):'<div class="empty-results">条件に合うスポットがないみたい。<br>フィルターを解除して探し直してみて。</div>';
    syncMobileControls(visible.length);
  }
  function updateStats(){let peak=0;for(const s of state.spots){if(['full','peak'].includes(currentReport(s).status))peak++}
    $('peak-count').textContent=peak;$('camera-count').textContent=state.spots.filter(s=>!!s.camera).length;
    $('total-count').textContent=state.spots.length+' LOCATIONS';
    const generated=state.data?.generatedAt;
    $('updated-small').textContent=generated?new Intl.DateTimeFormat('ja-JP',{timeZone:'Asia/Tokyo',hour:'2-digit',minute:'2-digit'}).format(new Date(generated)):'未取得';
    $('sync-caption').textContent=generated?'システム確認 '+fmtDate(generated)+' JST':'公開初期データを表示';
  }
  function pinIcon(spot,status){
    const meta=STATUS[status] || STATUS.unknown;
    const emoji=spot.camera?'📹':(STATUS_EMOJI[status] || STATUS_EMOJI.unknown);
    const camera=spot.camera ? '<span class="camera-pin-dot" aria-hidden="true"></span>' : '';
    return L.divIcon({
      className:`leaflet-div-icon marker-${status} ${spot.camera?'marker-camera':''} ${state.selectedId===spot.id?'marker-selected':''}`,
      html:`<div class="leaf-pin" style="--c:${meta.color}"><span class="marker-core"><span class="marker-emoji" aria-hidden="true">${emoji}</span></span>${camera}</div>`,
      iconSize:[44,44],iconAnchor:[22,22]
    });
  }
  function addSpotMarker(spot){
    const status=currentReport(spot).status;
    const title=`${spot.name}：${STATUS[status].text}${spot.camera?'（📹タップでカメラを開く）':''}`;
    const marker=L.marker([spot.lat,spot.lon],{icon:pinIcon(spot,status),riseOnHover:true,title,alt:title});
    marker.on('click',()=>{if(spot.camera)cameraOpen(spot);else selectSpot(spot.id);});
    state.layers.addLayer(marker);
    state.markers.set(spot.id,marker);
  }
  function renderMap(){
    if(!state.map)return;
    state.layers.clearLayers();state.markers.clear();
    // Only render the visible viewport. At high zoom this prevents thousands of hidden DOM markers.
    const view=state.map.getBounds().pad(.32);
    const visible=visibleSpots().filter(s=>view.contains([s.lat,s.lon])),zoom=state.map.getZoom();
    if(zoom>=8 || visible.length<13){visible.forEach(addSpotMarker);return;}
    // Native lightweight clusters avoid a third-party plugin and keep nationwide spots readable.
    const cell=zoom<=4?5:zoom===5?2.4:zoom===6?1.2:0.6;
    const bins=new Map();
    for(const spot of visible){
      const key=Math.floor(spot.lat/cell)+':'+Math.floor(spot.lon/cell);
      if(!bins.has(key))bins.set(key,[]);
      bins.get(key).push(spot);
    }
    for(const group of bins.values()){
      if(group.length===1){addSpotMarker(group[0]);continue;}
      const lat=group.reduce((sum,s)=>sum+s.lat,0)/group.length;
      const lon=group.reduce((sum,s)=>sum+s.lon,0)/group.length;
      // Mixed-status clusters show a proportional colour ring, not a misleading single status.
      const counts={};
      for(const s of group){const status=currentReport(s).status;counts[status]=(counts[status]||0)+1;}
      let angle=0;
      const segments=[];
      for(const [status,meta] of Object.entries(STATUS)){
        const count=counts[status]||0;
        if(!count)continue;
        const next=angle+360*count/group.length;
        segments.push(`${meta.color} ${angle.toFixed(2)}deg ${next.toFixed(2)}deg`);
        angle=next;
      }
      const dominant=Object.keys(STATUS).sort((a,b)=>(counts[b]||0)-(counts[a]||0))[0];
      const cameras=group.some(s=>s.camera);
      const ring=`conic-gradient(${segments.join(',')})`;
      const html=`<div class="cluster-pin" style="--ring:${ring}"><span class="cluster-emoji" aria-hidden="true">${STATUS_EMOJI[dominant]}</span><b>${group.length}</b>${cameras?'<span class="cluster-cam" aria-hidden="true">📹</span>':''}</div>`;
      const icon=L.divIcon({className:'koyo-cluster-icon',html,iconSize:[52,52],iconAnchor:[26,26]});
      const marker=L.marker([lat,lon],{icon,riseOnHover:true,title:`${group.length}地点を集約`});
      const summary=Object.entries(STATUS).filter(([status])=>counts[status]).map(([status,meta])=>`${meta.text} ${counts[status]}`).join('・');
      marker.bindTooltip(`${group.length}地点（${summary}） · クリックで拡大`);
      marker.on('click',()=>state.map.flyTo([lat,lon],Math.min(10,zoom+2),{duration:.55}));
      state.layers.addLayer(marker);
    }
  }
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
    const sourceUrl=report?.sourceUrl || spot.sourceUrl;
    const source=sourceUrl && safeURL(sourceUrl)!=='#' ? `<a href="${safeURL(sourceUrl)}" target="_blank" rel="noopener noreferrer">${report?'紅葉観測の情報源':'地点の出典'} ↗</a>`:'<span>情報源なし</span>';
    const dateInfo=report?`最終報告：${fmtDate(report.observedAt)} (${age}日前)${stale?'　※更新期限超過':''}`:'現時点で確認済みの色づき報告がありません';
    const sourceType=report?.kind==='official'?'公式観測':report?.kind==='community'?'現地レポート':report?.kind==='third_party'?'公開情報':spot.candidate?'紅葉観賞候補':'情報待ち';
    return `<div class="detail-accent" style="--c:${meta.color}"></div><div class="detail-inner"><div class="detail-head"><span class="detail-kicker">${safe(spot.prefecture).toUpperCase()} / AUTUMN GUIDE</span><button id="detail-close" class="detail-close" type="button" aria-label="詳細を閉じる">×</button></div>
      <h3 class="detail-name">${safe(spot.name)}</h3><div class="detail-tags"><span class="detail-tag main" style="--c:${meta.color}"><i></i>${meta.text}</span><span class="detail-tag">${sourceType}</span>${camera?`<span class="detail-tag">📹 ${spot.camera.mode==='directory'?'配信元のカメラ案内':'ライブカメラあり'}</span>`:''}</div>
      <p class="detail-date ${stale?'detail-stale':''}">${dateInfo}</p><p class="detail-description">${safe(spot.description||'地点情報を読み込み中です。')}<br>例年の目安：${safe(spot.typicalSeason||'確認中')}</p>
      <div class="detail-weather"><span id="weather-content" class="weather-loading">現地の天気を取得中...</span></div>
      <div class="detail-actions ${camera?'has-camera':''}">${camera?`<button type="button" class="detail-btn cam" id="detail-camera">📹 ${spot.camera.mode==='directory'?'カメラ案内を開く':'ライブカメラを見る'} ↗</button>`:''}<a class="detail-btn" target="_blank" rel="noopener noreferrer" href="${safeURL(googleMaps)}">⌖ 地図で開く ↗</a><a class="detail-btn secondary" target="_blank" rel="noopener noreferrer" href="${safeURL(submit)}">✎ 状況を報告 ↗</a></div>
      <div class="detail-extra"><span>${safe(report?.sourceName||spot.sourceName||'未確認')} ${stale?' / 古い報告':''}</span>${source}</div>
      <div class="detail-spot-id"><span>スポットID</span><code>${safe(spot.id)}</code><button id="copy-spot-id" type="button" title="スポットIDをコピー">コピー</button></div></div>`;
  }
  function updatePinSelection(){state.markers.forEach((marker,id)=>{marker.getElement()?.classList.toggle('marker-selected',id===state.selectedId);});}
  function bindDetailActions(spot){$('detail-close')?.addEventListener('click',closeDetail);$('detail-camera')?.addEventListener('click',()=>cameraOpen(spot));$('copy-spot-id')?.addEventListener('click',()=>{if(navigator.clipboard?.writeText){navigator.clipboard.writeText(spot.id).then(()=>notify('スポットIDをコピーしました')).catch(()=>notify('コピーできませんでした'));}else{notify('スポットIDを選択してコピーしてください');}});}
  function renderSelectedDetail(spot){
    const detailed=withDetails(spot);
    $('detail').innerHTML=detailHTML(detailed);
    $('detail').hidden=false;
    bindDetailActions(detailed);
    loadWeather(detailed);
  }
  function selectSpot(id){
    const spot=state.spots.find(s=>s.id===id);if(!spot)return;
    state.selectedId=id;renderSelectedDetail(spot);
    if(state.map){state.map.flyTo([spot.lat,spot.lon],Math.max(10,state.map.getZoom()),{duration:.55});updatePinSelection();}
    $('sidebar').classList.remove('open');$('mobile-list-toggle').setAttribute('aria-expanded','false');
    renderList();void loadSpotDetails(spot);
  }
  function closeDetail(){state.selectedId=null;$('detail').hidden=true;$('detail').innerHTML='';renderList();if(state.map)updatePinSelection();}
  function render(){
    renderFilters();renderList();updateStats();renderMap();
    if(state.selectedId){
      const spot=state.spots.find(s=>s.id===state.selectedId);
      if(spot){renderSelectedDetail(spot);void loadSpotDetails(spot);}
    }
  }
  const OSM_URL='https://tile.openstreetmap.org/{z}/{x}/{y}.png';
  function createMapTiles(){
    // A 512px display tile and zoomOffset -1 reuses OSM's regular 256px images.
    // At the same screen size, requests roughly one quarter as many tiles.
    return L.tileLayer(OSM_URL,{
      tileSize:state.lowData?512:256,zoomOffset:state.lowData?-1:0,
      maxZoom:19,attribution:'© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>',
      updateWhenIdle:true,updateWhenZooming:false,keepBuffer:0,detectRetina:false,crossOrigin:true
    });
  }
  function updateMapQualityButton(){
    const b=$('map-quality');if(!b)return;
    b.textContent=state.lowData?'⚡':'精';
    b.title=state.lowData?'省データ表示（高精細に切り替える）':'高精細表示（省データに戻す）';
    b.setAttribute('aria-pressed',String(!state.lowData));
    b.setAttribute('aria-label',b.title);
  }
  function toggleMapQuality(){
    if(!state.map)return;
    state.lowData=!state.lowData;
    if(state.tileLayer)state.map.removeLayer(state.tileLayer);
    state.tileLayer=createMapTiles().addTo(state.map);
    updateMapQualityButton();
    notify(state.lowData?'省データ地図に切り替えました':'高精細なOSM地図に切り替えました');
  }
  function initMap(){
    if(typeof L==='undefined'){
      $('map-fallback').innerHTML='<span class="fallback-emoji">🍁</span><span>地図ライブラリを取得できません</span><small>通信環境を確認してください。スポット一覧は利用できます。</small>';
      return;
    }
    try{
      // Set final bounds before loading any tiles: no intermediate zoom requests.
      // OSM credit is shown by .map-credit; Leaflet's own control would overlap it.
      state.map=L.map('map',{zoomControl:false,attributionControl:false,minZoom:3,maxZoom:17,preferCanvas:true,
        zoomAnimation:false,fadeAnimation:false,markerZoomAnimation:false});
      const points=state.initialBounds||state.spots.map(s=>[s.lat,s.lon]);
      const bounds=L.latLngBounds(points);
      if(bounds.isValid())state.map.fitBounds(bounds,{padding:[20,20],maxZoom:5,animate:false});
      else state.map.setView([36.6,138.0],4);
      state.tileLayer=createMapTiles().addTo(state.map);
      updateMapQualityButton();
      state.layers=L.layerGroup().addTo(state.map);
      $('map-fallback').remove();
      L.control.zoom({position:'bottomright'}).addTo(state.map);
      state.map.on('moveend',renderMap);
      renderMap();
    }catch(e){console.warn('Map init failed',e);state.map=null;}
  }
  async function loadLive({silent=false}={}){
    const start=Date.now();$('refresh').classList.add('spin');
    try{
      if(location.protocol==='file:'){
        if(!silent)notify('ローカル表示です。公開後は自動でデータを更新します');
        return;
      }
      const refreshCatalog=!state.spotsLoadedAt || Date.now()-state.spotsLoadedAt>60*60*1000;
      const [catalogResponse,liveResponse]=await Promise.all([
        refreshCatalog?fetch('data/spots-lite.json',{cache:'no-cache'}):Promise.resolve(null),
        fetch('data/live.json',{cache:'no-store'})
      ]);
      if((catalogResponse&&!catalogResponse.ok)||!liveResponse.ok)throw new Error('HTTP error');
      const [catalog,live]=await Promise.all([
        catalogResponse?catalogResponse.json():Promise.resolve(null),
        liveResponse.json()
      ]);
      if(!live?.reports || typeof live.reports!=='object')throw new Error('Invalid observations');
      const spots=catalogResponse?decodeCatalog(catalog):state.spots;
      const previous=state.data?.generatedAt;
      state.spots=spots;state.reports=live.reports;state.data=live;state.lastDataFetch=new Date();
      if(catalogResponse)state.spotsLoadedAt=Date.now();
      if(catalogResponse||previous!==live.generatedAt){createSelectOptions();render();}
      if(!silent)notify(live.generatedAt===previous?'確認完了。最新の取得結果です':'最新データを読み込みました');
    }catch(e){
      if(!silent)notify('最新データを取得できません。保存済みの地図を表示しています');
      console.warn('Could not update lightweight map data',e);
    }finally{
      setTimeout(()=>$('refresh').classList.remove('spin'),Math.max(250,550-(Date.now()-start)));
    }
  }
  function wireControls(){
    $('search').addEventListener('input',e=>{state.query=e.target.value;const mobile=$('mobile-search');if(mobile)mobile.value=state.query;applySearchFilters()});
    $('mobile-search')?.addEventListener('input',e=>{state.query=e.target.value;$('search').value=state.query;applySearchFilters()});
    $('mobile-peaks')?.addEventListener('click',()=>{state.status=state.status==='best'?'all':'best';applySearchFilters()});
    $('mobile-cameras')?.addEventListener('click',()=>{state.cameraOnly=!state.cameraOnly;$('camera-only').checked=state.cameraOnly;applySearchFilters()});
    $('prefecture').addEventListener('change',e=>{state.pref=e.target.value;applySearchFilters()});
    $('camera-only').addEventListener('change',e=>{state.cameraOnly=e.target.checked;applySearchFilters()});
    $('status-filters').addEventListener('click',e=>{const button=e.target.closest('button[data-status]');if(!button)return;state.status=button.dataset.status;applySearchFilters()});
    $('clear-filters').addEventListener('click',()=>{state.status='all';state.query='';state.pref='';state.cameraOnly=false;$('search').value='';$('mobile-search').value='';$('prefecture').value='';$('camera-only').checked=false;state.listLimit=120;render()});
    $('results-list').addEventListener('click',e=>{
      const more=e.target.closest('#results-more');
      if(more){state.listLimit+=120;renderList();return;}
      const button=e.target.closest('button[data-id]');if(button)selectSpot(button.dataset.id);
    });
    $('refresh').addEventListener('click',()=>loadLive());
    $('map-quality')?.addEventListener('click',toggleMapQuality);
    $('fit').addEventListener('click',()=>{if(!state.map)return;const p=visibleSpots();if(p.length)state.map.fitBounds(L.latLngBounds(p.map(s=>[s.lat,s.lon])),{padding:[45,45],maxZoom:11})});
    $('locate').addEventListener('click',()=>{if(!navigator.geolocation){notify('位置情報に対応していません');return}navigator.geolocation.getCurrentPosition(p=>{state.map?.flyTo([p.coords.latitude,p.coords.longitude],10);notify('現在地の周辺を表示しています')},()=>notify('位置情報の利用が許可されていません'),{timeout:9000,enableHighAccuracy:false})});
    $('mobile-list-toggle').addEventListener('click',()=>{const el=$('sidebar'),open=el.classList.toggle('open');$('mobile-list-toggle').setAttribute('aria-expanded',String(open));syncMobileControls();if(open)$('search').focus({preventScroll:true});});
    document.addEventListener('keydown',e=>{if(e.key==='/' && !['INPUT','TEXTAREA'].includes(document.activeElement?.tagName)){e.preventDefault();(window.matchMedia('(max-width:820px)').matches?$('mobile-search'):$('search')).focus();}if(e.key==='Escape'){closeDetail();$('sidebar').classList.remove('open');$('mobile-list-toggle').setAttribute('aria-expanded','false');syncMobileControls();}});
  }
  function main(){let bootstrap={spots:[],live:{reports:{},generatedAt:null}};
    try{bootstrap=JSON.parse($('bootstrap-data').textContent);}catch(e){console.warn('Missing offline data',e)}
    state.spots=bootstrap.spots||[];state.reports=bootstrap.live?.reports||{};state.data=bootstrap.live||null;
    state.initialBounds=bootstrap.bounds||null;
    for(const item of state.spots)state.detailCache.set(item.id,item);
    $('today-label').textContent=tokyoDate().replace(/\//g,'.').toUpperCase();const year=new Intl.DateTimeFormat('en',{timeZone:'Asia/Tokyo',year:'numeric'}).format(new Date());$('season-year').textContent=year;$('map-kicker-year').textContent=year;
    createSelectOptions();wireControls();render();initMap();
    loadLive({silent:true});setInterval(()=>loadLive({silent:true}),5*60*1000);
    // Freshness changes at midnight, even when source data is unchanged.
    setInterval(()=>{renderFilters();renderList();updateStats();renderMap()},60*60*1000);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',main);else main();
})();
