# Icons

可复用的工具和文件类型图标库。消费项目专有的 `app` 图标、Logo、原稿及历史文件由各自项目维护，不放入本仓库。

## 正式 Logo

2026-10-30 确认采用 V15：黄色边框立方体，蓝色顶部为朝下笔尖、红色左侧为网格、绿色右侧为设置齿轮。

- [可编辑 SVG](source/logos/logo.svg) 为正式矢量源；[透明 PNG](source/logos/logo.png) 为对应的 1254×1254 原尺寸成品。
- 黑白版：[SVG](source/logos/logo-bw.svg) / [PNG](source/logos/logo-bw.png)，黑色框架、白色面、黑色图标，透明背景，1254×1254；几何与正式彩色版一致。
- 外部对比参考：[AllOmnitools 图标](source/logos/references/allomnitools-icon-512.png)，来源 [allomnitools.com](https://allomnitools.com/)，仅用于视觉比较。
- `source/logos/history/cube-v15.*` 保留为已确认版本记录，V7、V8 备选也统一归档在 `source/logos/history/`；后续修改以 `logo.svg` 为入口，并同步导出 `logo.png`。
- 此目录维护图标库自身的品牌 Logo，不属于工具或文件类型图标，不纳入通用图标 manifest；gallery 左上角和浏览器标签页使用正式 Logo。Windows 使用 `preview.lnk` 启动本地预览，其快捷方式图标来自根目录 `favicon.ico`。

## 目录

- `source/tools/`、`source/files/`：高分辨率透明 PNG。
- `source/svgs/tools/`：工具图标的纯矢量 SVG。
- `source/svgs/files/`：120个文件类型图标的纯矢量 SVG，标签已转为路径。
- `24/`、`30/`、`36/`、`48/`：各尺寸的工具及文件类型 PNG。
- `manifest.json`：图标名称、用途和统一绘制参数。
- `gallery.html`：浏览器直接打开的本地图标总览。
- `scripts/`：生成工具和文档边框模板。
- [DESIGN.md](DESIGN.md)：现行样式、分组规则、创建流程与验收要求；新增时从“新增图标统一入口”开始阅读。
- [AGENTS.md](AGENTS.md)：供 AI 助手自动读取的仓库维护指引。

## 文件名前缀

目录保持平铺，文件统一采用 `分类-原名称`，例如 `video-mp4.png`、`edit-copy.svg`。
分类前缀使用容易辨认的 3～5 字母英文短词或常见缩写。
同一图标的 SVG、源 PNG 和四档 PNG 使用相同文件名，按文件名排序即可聚合同类资源。

| 目录 | 前缀与分类 |
| --- | --- |
| files | `doc` 文档、`sheet` 表格、`slide` 演示、`image` 图片、`audio` 音频、`video` 视频、`live` 流媒体与链接、`pack` 压缩与镜像、`code` 代码与配置、`data` 数据库、`app` 程序与系统、`other` 通用 |
| tools | `file` 文件与文件夹、`task` 传输与任务、`play` 播放与音频、`view` 导航与布局、`edit` 编辑与操作、`user` 用户与通信、`info` 状态与提示、`sys` 系统与服务、`net` 网络、`lock` 安全与可见性、`date` 日历 |

`manifest.json` 中的 `name` 保留原始标识，`group` 记录分类前缀，`source` 和 `vector_source` 记录实际文件路径。
例如 `mp4` 对应 `source/files/video-mp4.png`，命令行仍使用 `--names mp4`。
工具图标若有同名操作（例如下载），渲染时用完整文件名区分：`--names task-download file-download`。
此次文件名迁移后，消费项目更新资源时需要同步调整路径映射。

## 生成

```powershell
python -m pip install -r requirements-dev.txt
python scripts/build_badge_icons.py
python scripts/build_file_icons.py
python scripts/build_list_icons.py
python scripts/build_circle_control_icons.py
python scripts/build_control_icons.py
python scripts/render_tool_icons.py --all
python scripts/render_tool_icons.py --names bell save glossary
python scripts/render_file_icons.py --all
python scripts/render_file_icons.py --names pdf mp4 m3u8
python scripts/render_file_icons.py --render-only --all
python scripts/update_gallery.py
```

建议 Python 3.10 或更高版本。重建文件SVG时默认使用 Windows 的 Segoe UI Semibold，其他环境通过 `--font` 指定字体文件。SVG内保存字形路径，查看不依赖字体；仅从现有SVG重新导出PNG可用 `--render-only --all`（或 `--render-only --names pdf`），无需字体文件。生成依赖不属于消费项目的运行时依赖。

工具图标 `file-new` 使用 `source/svgs/tools/file-new.svg` 作为矢量源。修改或重建新建文件图标时运行 `python scripts/render_file_icons.py --names new`，同步生成工具与文件组的 PNG。

文档基底 `source/svgs/tools/file-file.svg` 是 `file-new`、`file-search` 和 `file-download` 的共享主体。先运行 `python scripts/build_file_icons.py` 由基底生成 `file-new.svg`，再运行角标与 PNG 渲染脚本；文件类型图标通过 `render_file_icons.py` 复用同一文档框体规范。

文件类型通过 `render_file_icons.py` 继承清单中的底色、标签及排版参数，生成完整SVG，再逐档直接渲染PNG。标签两侧的缺口切在矢量边框上，不使用位图遮罩或嵌入图片。`other-new.svg`复用工具`file-new.svg`，保留无色圆、无格式标签的特殊造型。重建SVG会更新`vector_source`与排版记录，随后运行`update_gallery.py`同步离线图集；只导出PNG不会修改清单。

搜索、放大、缩小共用 `scripts/icon_templates/magnifier.svg`；调整模板后先运行 `python scripts/build_magnifier_icons.py`，再重建7个搜索角标、渲染对应PNG。角标与独立图标的模板关系及最新参数见 DESIGN.md 的“放大镜家族统一”。

右下附加标记的尺寸与断口由 `scripts/build_badge_icons.py` 维护。调整主体或标记后先运行该脚本，再渲染 PNG；可用 `--names user-send-code view-map-code` 仅重建指定 SVG。完整范围和尺寸见 [BADGE-AUDIT.md](BADGE-AUDIT.md)。

两行/三行方块、圆圈、数字及任务列表共用 `scripts/build_list_icons.py` 的布局参数。调整这一组时先运行该脚本，再运行 `python scripts/render_tool_icons.py --names list-square-two list-square batch list-circle-two list-circle list-ordered`，同步全部6个图标。`view-list-bullet`按用户要求保留原布局，不由该脚本覆盖；规范见 [DESIGN.md](DESIGN.md)。

## 使用

### 本地实时预览

双击仓库根目录的 `preview.cmd`，或在终端运行：

```powershell
python scripts/preview_server.py
```

启动后自动打开 `http://127.0.0.1:8765/gallery.html`，按 Ctrl+C 停止。只需 Python 标准库，无需安装前端依赖。端口被占用时可添加 `--port 8766`；不自动打开浏览器可添加 `--no-browser`。

- 按分类、用途和名称筛选图标，列表与对比区均可选择24、30、36、48px对应导出PNG，或原图（384px）。
- 点击图标加入并排对比（不限制数量），顶部按所选尺寸预览，同时查看四档实际尺寸和24px工具栏效果；“人物组”可直接对比 user、contact、users。通过对比区的“对比尺寸”统一切换24、30、36、48px或原图（384px），默认为48px；尺寸和来源在图下标注，不放大小尺寸PNG。
- 拖动对比卡片左上角的手柄，或用卡片右上角的前移/后移按钮调整顺序；下方工具栏也可直接拖动图标排序，与上方卡片同步，刷新后保留。
- 切换白色、浅灰、深色及透明棋盘背景，打开画布边界与中心线，检查留白、居中及视觉重量。深色背景不会反转图标颜色。
- PNG 模式查看各档成品，SVG 模式直接查看源文件；没有 SVG 的图标使用 PNG。PNG 更新需先运行对应的图标生成脚本，预览工具不修改或自动生成图标。
- 服务约每1.5秒检查资源变化并刷新，保持搜索、选中图标和预览设置。修改 manifest 后服务会直接读取新清单；交付前仍需运行 `python scripts/update_gallery.py` 同步离线图集。

也可以直接打开 `gallery.html` 使用离线预览，此时不自动检查文件变化，点击“刷新资源”重新加载图片。原生尺寸指 CSS 像素，查看时将浏览器缩放设为100%，系统DPI缩放仍由浏览器处理。

消费项目只复制实际需要的 source PNG 和 24、30、36、48 四档 PNG，并维护自己的资源映射。例如 downloader 只保留运行时使用的通用资源副本，其专属应用图标与历史素材始终留在 downloader 内。

## 测试

在仓库根目录运行 `python -m unittest discover -s tests -v`。
