# 待制作图标临时清单

计划制作日期：2026-10-28。

共 60 个，已完成 60 个，待制作 0 个：新造型 25 个、组合或变体 24 个、追加布局与会话操作 5 个、扩展与开发工具 3 个、设备图标 3 个。已排除 Edge、Firefox 品牌造型。此清单根据聊天中的参考截图整理，制作时逐项勾选，并确定最终名称和分类前缀。

## 新造型 25 个

- [x] 01．定位＋放大镜 → `view-location-search`
- [x] 02．定位＋齿轮 → `view-location-settings`
- [x] 03．地球＋网络节点 → `net-globe-network`
- [x] 04．双定位标记 → `view-locations`
- [x] 05．WebSocket 连接 → `net-websocket`
- [x] 06．API 字样 → `net-api`
- [x] 07．POST 字样 → `net-post`
- [x] 08．字符串拼接 → `edit-text-join`
- [x] 09．拼音 ab → `edit-pinyin`
- [x] 10．圆角框 H → `sys-html-round`
- [x] 11．六边形 H → `sys-html-hex`
- [x] 12．扇形色卡 → `edit-swatches`
- [x] 13．文本分栏 → `edit-columns`
- [x] 14．斜向条纹 → `edit-stripes`
- [x] 15．A＋加号（字符计数） → `edit-char-count`
- [x] 16．文本横线＋加号 → `edit-text-add`
- [x] 17．文本长度过滤 → `edit-text-length`
- [x] 18．条码 → `file-barcode`
- [x] 19．汉字笔划符号 → `edit-strokes`
- [x] 20．手写笔画 → `edit-handwriting`
- [x] 21．Nº 数字清除 → `edit-numbers-clear`
- [x] 22．删除回车换行 → `edit-line-break-remove`
- [x] 23．去除空行 → `edit-blank-remove`
- [x] 24．文本去重 → `edit-text-dedup`
- [x] 25．炸弹状图标（Rabbit 参考） → `sys-bomb`

## 组合和变体 24 个

- [x] 26．纸飞机＋代码 → `user-send-code`
- [x] 27．纸飞机＋百分号 → `user-send-percent`
- [x] 28．纸飞机＋向下箭头 → `user-send-download`
- [x] 29．地图＋代码 → `view-map-code`
- [x] 30．地球＋WWW → `net-globe-www`
- [x] 31．盾牌＋定位点 → `lock-shield-location`
- [x] 32．盾牌＋代码符号 → `lock-shield-code`
- [x] 33．服务器＋闪电 → `net-server-bolt`
- [x] 34．链接＋装饰短线 → `net-link-spark`
- [x] 35．双圆端点连线 → `net-node-link`
- [x] 36．双层标签 → `file-tags`
- [x] 37．表情日历 → `date-calendar-smile`
- [x] 38．Aa＋勾选 → `edit-case-check`
- [x] 39．引号＋文本横线 → `edit-quote-text`
- [x] 40．A/B 排序列表 → `edit-sort-alpha`
- [x] 41．文本横线＋斜线 → `edit-text-off`
- [x] 42．截取框＋文字 → `edit-text-crop`
- [x] 43．带框右对齐 → `edit-align-right-frame`
- [x] 44．带框竖排文字 → `edit-text-vertical-frame`
- [x] 45．带外框的锁 → `lock-lock-frame`
- [x] 46．带外框的密码星号 → `lock-password-frame`
- [x] 47．带外框的钥匙 → `lock-key-frame`
- [x] 48．多方向随机箭头 → `edit-random`
- [x] 49．独立铅笔 → `edit-pencil`

## 追加布局与会话操作 5 个

- [x] 50．左侧栏：窗口中划分左侧窄栏，参考截图第一个图标。 → `view-sidebar-left`
- [x] 51．侧栏加上下分区：左侧窄栏，右侧上下两个区域，参考截图第二个图标。 → `view-sidebar-stack`
- [x] 52．底部面板：窗口中划分下方横向面板，参考截图第三个图标。 → `view-panel-bottom`
- [x] 53．左右分栏：左右两块并排区域，参考截图第四个图标。 → `view-split`
- [x] 54．切换聊天或会话：使用气泡与切换箭头表达，与现有双气泡会话、普通方向箭头区分。 → `user-chat-switch`

布局四项共用框体尺寸、分隔线线宽和圆角，检查 24px 下的分区辨识度；参考图中的区域填充按本库统一风格处理。切换会话的组合造型沿用 0.6px 可见断口规范。

## 扩展与开发工具 3 个

- [x] 55．扩展管理：方块拼接布局，右上角一块斜置，参考截图上方图标；与现有拼图形 sys-extension 保留为不同样式。 → `sys-extensions`
- [x] 56．远程资源管理：显示器与远程连接标记组合，参考截图下方图标及“远程资源管理器”提示；与普通显示器、终端图标区分，组合处遵循 0.6px 可见断口规范。 → `sys-remote`
- [x] 57．运行和调试：右向空心播放三角与左下方小虫叠放，参考截图；优先复用现有 play-start、sys-debug 的造型语言，组合遮挡处保留 0.6px 可见断口。 → `sys-run-debug`

## 设备图标 3 个

- [x] 58．磁盘或硬盘：采用扁平盘体、前面板与小指示灯表达本地存储设备，与 file-save 的软盘保存造型、sys-database 的数据库圆柱区分，保持统一线宽与圆角。 → `sys-disk`
- [x] 59．键盘：采用横向键盘轮廓、简化键位和空格键，控制细节密度，确保 24px 下可辨认，保持统一线宽与圆角。 → `sys-keyboard`
- [x] 60．鼠标：采用圆润鼠标轮廓、左右按键分隔及滚轮，与 view-click 的点击光标造型区分，保持统一线宽和视觉大小。 → `sys-mouse`

## 制作和验收

- 遵循 [DESIGN.md](DESIGN.md) 的整套图标一致性原则，结合现有图标检查视觉大小、线条、圆角和留白。
- 工具图标默认采用 `#444444`、24px 坐标下 1.35px 描边，可比矩形圆角为 0.6px；保留已确认的图标组例外。
- 组合图标优先复用现有主体；遮挡断口的可见间距默认 0.6px，按描边外缘及圆头端点计算，后方隐藏轮廓断开，保持透明背景。
- SVG 放在 `source/svgs/`，源 PNG 放在 `source/tools/`，同步生成 24、30、36、48px PNG。
- 同步维护 `manifest.json`、`gallery.html`、`DESIGN.md` 中的图标数量及相关规范。
- 同时检查放大预览和各档实际尺寸，确认清晰度及同组、整套图标的协调程度。
- 运行 `python scripts/update_gallery.py` 和 `python -m unittest discover -s tests -v`，检查 `git diff --check`。
