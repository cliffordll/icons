/* Local preview only: image assets are never edited by this page. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const key = icon => icon.category + '/' + icon.source.split('/').pop();
  const stem = icon => icon.source.split('/').pop().replace(/\.png$/, '');
  const groups = {file:'文件与文件夹',task:'任务与传输',play:'播放与音频',view:'导航与布局',edit:'编辑与操作',user:'用户与通信',info:'状态与提示',sys:'系统与服务',net:'网络',lock:'安全与可见性',date:'日期',doc:'文档',sheet:'表格',slide:'演示',image:'图片',audio:'音频',video:'视频',live:'流媒体与链接',pack:'压缩与镜像',code:'代码与配置',data:'数据库',app:'程序与系统',other:'通用文件'};
  const defaults = {category:'tools',group:'',search:'',size:24,compareSize:48,mode:'png',background:'white',guides:false,collapsed:false,selected:['tools/user-user.png','tools/user-contact.png','tools/user-users.png']};
  let saved = {};
  try { saved = JSON.parse(localStorage.getItem('icon-preview-v1') || '{}'); } catch (_) { /* Private browsing may disable storage. */ }
  const state = {...defaults,...saved};
  if (!Array.isArray(state.selected)) state.selected = defaults.selected;
  if (typeof state.search !== 'string') state.search = '';
  if (!['','tools','files'].includes(state.category)) state.category = 'tools';
  if (typeof state.group !== 'string') state.group = '';
  if (!['white','gray','dark','checker'].includes(state.background)) state.background = 'white';
  if (![24,30,36,48,384].includes(Number(state.size))) state.size = 24;
  if (![24,30,36,48,384].includes(Number(state.compareSize))) state.compareSize = 48;
  if (!['png','svg'].includes(state.mode)) state.mode = 'png';
  let registry = [...icons], revision = '', uiRevision = '', etag = '', polling = false;
  state.selected = [...new Set(state.selected)].filter(id => registry.some(icon => key(icon) === id));
  let draggedIcon = null;
  const node = (tag, className, text) => { const el = document.createElement(tag); if (className) el.className = className; if (text !== undefined) el.textContent = text; return el; };
  function persist() { try { localStorage.setItem('icon-preview-v1',JSON.stringify(state)); } catch (_) {} }
  function toast(message) { $('toast').textContent = message; clearTimeout(toast.timer); toast.timer = setTimeout(() => $('toast').textContent = '',2500); }
  function imagePath(icon, size) {
    const path = state.mode === 'svg' && icon.vector_source ? icon.vector_source
      : size > 48 ? icon.source : `${size}/${icon.category}/${icon.source.split('/').pop()}`;
    return path + (revision ? '?v=' + revision : '');
  }
  function canvas(icon, size, zoom=false) {
    const box = node('span','icon-canvas');
    const displaySize = zoom ? Number(state.compareSize) : size;
    box.style.width = box.style.height = displaySize + 'px';
    const img = node('img'); img.src = imagePath(icon,size); img.width = img.height = displaySize; img.alt = stem(icon); img.draggable = false;
    img.addEventListener('error',() => { img.title = '该资源尚未导出或正在保存'; });
    box.append(img); return box;
  }
  function toggle(icon) {
    const id = key(icon), index = state.selected.indexOf(id);
    if (index >= 0) state.selected.splice(index,1);
    else state.selected.push(id);
    persist(); render();
  }
  function reorder(id, targetIndex) {
    const from = state.selected.indexOf(id);
    if (from < 0 || targetIndex < 0 || targetIndex >= state.selected.length || from === targetIndex) return;
    state.selected.splice(from,1);
    state.selected.splice(targetIndex,0,id);
    persist(); comparison();
    const moved = [...$('comparison-grid').children].find(card => card.dataset.icon === id);
    moved?.focus({preventScroll:true});
    toast('已调整顺序');
  }
  function navigation() {
    $('categories').replaceChildren();
    for (const [value,label] of [['','全部图标'],['tools','工具图标'],['files','文件类型']]) {
      const b = node('button','nav-button' + (state.category === value ? ' active' : ''),label);
      b.append(node('small','',registry.filter(i => !value || i.category === value).length));
      b.onclick = () => {state.category = value; state.group = ''; persist(); render();}; $('categories').append(b);
    }
    const entries = registry.filter(i => !state.category || i.category === state.category);
    const prefixes = [...new Set(entries.map(i => i.group))].sort();
    if (state.group && !prefixes.includes(state.group)) state.group = '';
    $('groups').replaceChildren();
    for (const value of ['',...prefixes]) {
      const b = node('button','nav-button' + (state.group === value ? ' active' : ''),value ? groups[value] || value : '全部分组');
      b.append(node('small','',entries.filter(i => !value || i.group === value).length));
      b.onclick = () => {state.group = value; persist(); render();}; $('groups').append(b);
    }
  }
  function comparison() {
    const chosen = state.selected.map(id => registry.find(i => key(i) === id)).filter(Boolean);
    const compareSize = Number(state.compareSize);
    $('compare').style.setProperty('--compare-size',compareSize+'px');
    $('compare-count').textContent = chosen.length + ' 个';
    $('compare').classList.toggle('collapsed',state.collapsed);
    $('collapse').textContent = state.collapsed ? '展开对比' : '收起';
    $('collapse').setAttribute('aria-expanded',String(!state.collapsed));
    const area = $('comparison-grid'); area.replaceChildren();
    if (!chosen.length) area.append(node('div','empty-comparison','点击下方图标，加入并排对比。'));
    for (const icon of chosen) {
      const card = node('article','comparison-card');
      const id = key(icon), index = state.selected.indexOf(id);
      card.dataset.icon = id; card.tabIndex = -1;
      const title = node('div','comparison-name');
      const handle = node('span','drag-handle','⠿'); handle.draggable = true; handle.title = '拖动调整顺序'; handle.setAttribute('aria-hidden','true');
      handle.ondragstart = event => {draggedIcon = id; event.dataTransfer.effectAllowed = 'move'; event.dataTransfer.setData('text/plain',id); card.classList.add('dragging');};
      handle.ondragend = () => {draggedIcon = null; for (const el of $('compare').querySelectorAll('.dragging,.drag-over')) el.classList.remove('dragging','drag-over');};
      card.ondragover = event => {if (draggedIcon && draggedIcon !== id) {event.preventDefault(); event.dataTransfer.dropEffect = 'move'; card.classList.add('drag-over');}};
      card.ondragleave = event => {if (!card.contains(event.relatedTarget)) card.classList.remove('drag-over');};
      card.ondrop = event => {event.preventDefault(); const source = draggedIcon; draggedIcon = null; if (source && source !== id) reorder(source,state.selected.indexOf(id));};
      const actions = node('span','card-order');
      for (const [offset,label,symbol] of [[-1,'前移','‹'],[1,'后移','›']]) {
        const button = node('button','order-button',symbol); button.type = 'button'; button.title = label; button.setAttribute('aria-label',label+' '+stem(icon));
        button.disabled = index+offset < 0 || index+offset >= state.selected.length;
        button.onclick = () => reorder(id,index+offset); actions.append(button);
      }
      const remove = node('button','remove','×'); remove.title = '移除 ' + stem(icon); remove.setAttribute('aria-label',remove.title); remove.onclick = () => toggle(icon); actions.append(remove);
      title.append(handle,node('span','comparison-stem',stem(icon)),actions);
      card.append(title);
      const zoom = node('div','zoom-art preview-surface'); zoom.append(canvas(icon,compareSize,true)); card.append(zoom);
      card.append(node('div','preview-caption',`${compareSize} × ${compareSize}px · ` + (state.mode === 'svg' && icon.vector_source ? 'SVG 矢量源' : compareSize === 384 ? '原图' : '对应尺寸 PNG')));
      const row = node('div','native-row');
      for (const size of [24,30,36,48]) {
        const sample = node('div','native-sample'), art = node('div','native-art preview-surface'); art.append(canvas(icon,size)); sample.append(art,node('small','',size + 'px')); row.append(sample);
      }
      card.append(row);
      const links = node('div');
      for (const [label,path] of [['源 PNG',icon.source],['SVG',icon.vector_source]]) {
        if (!path) continue;
        const a = node('a','source-link',label); a.href = path + (revision ? '?v=' + revision : ''); a.target = '_blank'; a.rel = 'noopener'; links.append(a);
      }
      card.append(links); area.append(card);
    }
    $('toolbar-strips').replaceChildren();
    const strip = node('div','toolbar-strip preview-surface');
    for (const icon of chosen) {
      const button = node('div','toolbar-button'), id = key(icon);
      button.title = stem(icon)+' · 拖动调整顺序'; button.dataset.icon = id; button.draggable = true;
      button.ondragstart = event => {draggedIcon = id; event.dataTransfer.effectAllowed = 'move'; event.dataTransfer.setData('text/plain',id); button.classList.add('dragging');};
      button.ondragend = () => {draggedIcon = null; for (const el of $('compare').querySelectorAll('.dragging,.drag-over')) el.classList.remove('dragging','drag-over');};
      button.ondragover = event => {if (draggedIcon && draggedIcon !== id) {event.preventDefault(); event.dataTransfer.dropEffect = 'move'; button.classList.add('drag-over');}};
      button.ondragleave = event => {if (!button.contains(event.relatedTarget)) button.classList.remove('drag-over');};
      button.ondrop = event => {event.preventDefault(); const source = draggedIcon; draggedIcon = null; if (source && source !== id) reorder(source,state.selected.indexOf(id));};
      button.append(canvas(icon,24)); strip.append(button);
    }
    $('toolbar-strips').append(strip);
  }
  function render() {
    navigation();
    document.body.dataset.bg = state.background;
    $('grid').style.setProperty('--list-size',Number(state.size)+'px');
    document.body.classList.toggle('guides',state.guides);
    $('title').textContent = state.group ? groups[state.group] || state.group : state.category === 'tools' ? '工具图标' : state.category === 'files' ? '文件类型' : '全部图标';
    const tokens = state.search.toLowerCase().trim().split(/\s+/).filter(Boolean);
    const visible = registry.filter(i => (!state.category || i.category === state.category) && (!state.group || i.group === state.group)
      && tokens.every(token => `${stem(i)} ${i.name} ${i.label} ${groups[i.group] || ''}`.toLowerCase().includes(token)));
    $('count').textContent = visible.length + ' / ' + registry.length;
    $('mode-hint').textContent = state.mode === 'png'
      ? '列表与对比均可选择 24/30/36/48px 对应 PNG，或 384px 原图。'
      : 'SVG：按所选尺寸预览矢量源；没有 SVG 的图标使用对应尺寸 PNG，选择原图时使用 384px PNG。';
    const grid = $('grid'); grid.replaceChildren();
    if (!visible.length) grid.append(node('p','empty','没有匹配图标，试试其他名称或分组。'));
    for (const icon of visible) {
      const selected = state.selected.includes(key(icon)), card = node('button','card' + (selected ? ' selected' : ''));
      card.type = 'button'; card.setAttribute('aria-pressed',String(selected)); card.title = (selected ? '移出对比：' : '加入对比：') + stem(icon);
      card.append(node('span','select-indicator','✓'));
      const art = node('div','art preview-surface'), box = canvas(icon,Number(state.size)); box.querySelector('img').loading = 'lazy'; art.append(box);
      card.append(art,node('span','card-name',stem(icon)),node('span','card-label',icon.label + (state.mode === 'svg' && !icon.vector_source ? ' · PNG' : '') + (Number(state.size)>48 && !(state.mode === 'svg' && icon.vector_source) ? ' · 原图' : '')));
      card.onclick = () => toggle(icon); grid.append(card);
    }
    comparison();
  }
  for (const id of ['size','mode','background','guides']) {
    const el = $(id); if (el.type === 'checkbox') el.checked = Boolean(state[id]); else el.value = state[id];
    el.addEventListener('change',() => {state[id] = el.type === 'checkbox' ? el.checked : el.value; persist(); render();});
  }
  $('compare-size').value = state.compareSize;
  $('compare-size').onchange = event => {state.compareSize = Number(event.target.value); state.collapsed = false; persist(); comparison();};
  $('search').value = state.search;
  $('search').oninput = event => {state.search = event.target.value; persist(); render();};
  $('clear').onclick = () => {state.selected = []; persist(); render();};
  $('people').onclick = () => {state.category = 'tools'; state.group = 'user'; state.search = ''; $('search').value = ''; state.selected = [...defaults.selected]; state.collapsed = false; persist(); render();};
  $('collapse').onclick = () => {state.collapsed = !state.collapsed; persist(); comparison();};
  function status(text,kind) { $('live').textContent = text; $('live').dataset.state = kind; }
  async function refresh(manual=false) {
    if (polling || draggedIcon) return;
    if (location.protocol === 'file:') {status('离线预览 · 双击 preview.cmd 开启实时刷新','offline'); if (manual) {revision = String(Date.now()); render();} return;}
    polling = true;
    try {
      const response = await fetch('/api/state',{cache:'no-store',headers:etag && !manual ? {'If-None-Match':etag} : {}});
      if (response.status === 304) {status('实时预览已连接 · 约 1.5 秒检查','live'); return;}
      if (!response.ok) throw new Error('Preview server unavailable');
      const next = await response.json();
      if (!Array.isArray(next.icons) || typeof next.revision !== 'string') throw new Error('Invalid preview state');
      etag = response.headers.get('ETag') || '';
      if (uiRevision && uiRevision !== next.uiRevision) {persist(); location.reload(); return;}
      uiRevision = next.uiRevision;
      if (revision !== next.revision || manual) {
        const changed = Boolean(revision); revision = next.revision; registry = next.icons;
        state.selected = state.selected.filter(id => registry.some(i => key(i) === id));
        render(); if (changed) toast('图标已更新 · ' + new Date().toLocaleTimeString());
      }
      status('实时预览已连接 · 约 1.5 秒检查','live');
    } catch (_) { status('自动刷新未连接 · 请运行 preview.cmd','error'); }
    finally {polling = false;}
  }
  $('refresh').onclick = () => refresh(true);
  window.iconPreview = {render};
  render(); refresh(); setInterval(() => {if (!document.hidden) refresh();},1500);
  document.addEventListener('visibilitychange',() => {if (!document.hidden) refresh();});
})();
