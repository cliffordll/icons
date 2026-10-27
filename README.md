# Icons

可复用的工具和文件类型图标库。消费项目专有的 `app` 图标、Logo、原稿及历史文件由各自项目维护，不放入本仓库。

## 目录

- `source/tools/`、`source/files/`：高分辨率透明 PNG。
- `source/svgs/`：SVG 源文件，和 PNG 分开存放。
- `24/`、`30/`、`36/`、`48/`：各尺寸的工具及文件类型 PNG。
- `manifest.json`：图标名称、用途和统一绘制参数。
- `gallery.html`：浏览器直接打开的本地图标总览。
- `scripts/`：生成工具和文档边框模板。
- [DESIGN.md](DESIGN.md)：通用图标设计规则。

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
此次文件名迁移后，消费项目更新资源时需要同步调整路径映射。

## 生成

```powershell
python -m pip install -r requirements-dev.txt
python scripts/render_tool_icons.py --all
python scripts/render_tool_icons.py --names bell save glossary
python scripts/render_file_icons.py --all
python scripts/render_file_icons.py --names pdf mp4 m3u8
python scripts/update_gallery.py
```

建议 Python 3.10 或更高版本。文件图标默认使用 Windows 的 Segoe UI Semibold，其他环境通过 `--font` 指定字体文件。生成依赖不属于消费项目的运行时依赖。

## 使用

消费项目只复制实际需要的 source PNG 和 24、30、36、48 四档 PNG，并维护自己的资源映射。例如 downloader 只保留运行时使用的通用资源副本，其专属应用图标与历史素材始终留在 downloader 内。

## 测试

在仓库根目录运行 `python -m unittest discover -s tests -v`。
