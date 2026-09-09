# OpenCAD UX（中文）

> 面向 FreeCAD 的「受 Fusion 360 启发的产品设计工作区」，服务于消费电子产品的
> ID 与结构设计：键盘、鼠标、耳机、接收器、充电底座、电子产品外壳等。

OpenCAD UX **不是** Fusion 360 的仿制外壳：它是一套 FreeCAD 附加组件
(Python Workbench)，以产品设计为重心重构工作区布局，使用完全原创的图标与主题，
并且所有核心操作都通过 **FreeCAD 公开 API 与标准命令** 执行，不依赖模拟点击，
不复制 Autodesk 的任何商标、图标、源码或专有视觉资产（仅研究不受保护的通用
CAD 交互范式）。

版本：**0.1.0（MVP）** ｜ 许可：**GPL-3.0-or-later** ｜ 开发验证环境：
FreeCAD 1.1.3（macOS arm64）。详细功能与差异见 [README.md](README.md)
与 [docs/TESTING.md](docs/TESTING.md)。

## 主要功能

- 统一 **Product Design 工作台**：默认隐藏与产品建模无关的专业工作台
  （BIM/建筑/CAM/FEM/Robot/渲染等），可在设置中随时重新启用；不删除任何底层功能。
- **Ribbon 工具栏**完全由 `resources/ribbon.json` 定义：Sketch（草图）、
  Constraints（约束）、Create（创建）、Modify（修改）、Combine（组合）、
  Inspect（检查）、Insert/Export（插入/导出），共 7 组 53 个按钮；改配置文件即可
  调整按钮/分组/顺序，无需改代码。
- 原创 **浅色/深色主题**，一键切换并支持还原之前的样式。
- **Fusion 风格快捷键预设**：S/L/R/C/D/E/F/H/M/P/Q、Shift+F、
  Delete/Esc、⌘(Ctrl)+Z/Shift+Z/S/O/N；自动做冲突检测，支持导入/导出，
  可随时恢复 FreeCAD 默认快捷键（我们通过「按键拦截层」实现，**不改写**你现有
  的 FreeCAD 快捷键）。
- **命令搜索**（S）：中英文模糊搜索（输入「倒角」「外壳」「拉伸」「合并」等
  中文也能命中）、最近使用优先、图标/名称/快捷键/分组展示、按选择过滤不可用项、
  Enter 直接执行真实 FreeCAD 命令。
- **上下文操作**（Q 或右侧面板）：依据所选对象（草图/实体面/边/多实体/参考图）
  给出最相关动作。
- **参考图工作流**：PNG/JPG 导入并吸附到 XY/XZ/YZ 平面、按真实宽度快速校准、
  两点校准数学、透明度、显示/隐藏、锁定（基于 FreeCAD 公开的
  `Image::ImagePlane`）。
- **设置页面**：外观/图标与按钮尺寸/Ribbon 分组显隐/导航/快捷键/面板方位/
  界面语言/备份与恢复/检查更新/调试日志等。
- 三个**真实可打开**的消费电子示例模型（键盘外壳、鼠标概念外壳、带螺丝柱与
  USB 开孔的盒体），由脚本生成 .FCStd 并自动导出 STEP/STL。

## 安装

推荐通过 Addon Manager（发布后）。手动安装：

1. 下载发行 ZIP（`OpenCAD-UX-0.1.0.zip`），解压得到含
   `package.xml / Init.py / InitGui.py / opencad_ux/` 的文件夹；
2. 拷贝到 FreeCAD 用户 Mod 目录（macOS 通常为
   `~/Library/Application Support/FreeCAD/<版本>/Mod`）；
3. 重启 FreeCAD，在工作台切换器选择 **Product Design (OpenCAD UX)**。

本仓库脚本：`bash scripts/install.sh`（自动备份配置后再安装）、
`bash scripts/uninstall.sh`（卸载并恢复）、`bash scripts/make_zip.sh`（打 ZIP）。

> 安装/应用主题/应用导航前，`install.sh` 会先把 FreeCAD 自身的配置文件备份到
> `<用户数据>/OpenCADUX/backups/`，卸载或「恢复默认布局」时可完整还原；
> 不覆盖、不破坏你既有的 FreeCAD 设置。

## 常用快捷键

| 键 | 命令 | 键 | 命令 |
|---|---|---|---|
| S | 命令搜索 | M | 移动/变换 |
| L | 直线 | P | 投影几何 |
| R | 矩形 | Q | 上下文操作 |
| C | 圆 | Shift+F | 适配视图 |
| D | 草图尺寸 | Delete | 删除所选 |
| E | 拉伸/Pad | Esc | 取消当前命令 |
| F | 圆角 | Ctrl/⌘+Z / Shift+Z | 撤销/重做 |
| H | 孔 | Ctrl/⌘+S / O / N | 保存/打开/新建 |

## 鼠标导航

FreeCAD 1.0/1.1（含 1.1.3）**没有内置 Fusion 导航模式**。OpenCAD UX 会：
先探测是否有原生 Fusion 导航类（有则直接用官方实现）；否则自动应用最接近的
内置 **Revit** 模式（通过 FreeCAD 自己的 `NavigationStyle` 参数）；中键拖动平移/
Shift+中键旋转这类自定义映射在现版本 FreeCAD 公开 Python API 中**无法实现**，
需可选的 C++ 补丁才能做到像素级一致——详见 README「鼠标与导航」差异表。

## 测试

```bash
bash scripts/run_pure_tests.sh      # 纯 Python 单测（无需 FreeCAD）
bash scripts/run_console_tests.sh   # 在真实 FreeCADCmd 中运行 25 项测试
bash scripts/run_examples.sh        # 生成三个示例模型并导出 STEP/STL
bash scripts/check_static.sh        # 语法、图标一致性、ribbon 结构
```

## 已知限制

- 现有 FreeCAD 公开 API 无法实现 Fusion 式「移动面 / 偏移面」，点击会给出明确
  说明与替代方案（Transform、编辑原草图、抽壳）。
- PartDesign 的圆角/抽壳**特征对象**无法脱离 GUI 任务对话框用 Python 无头创建
  （需要选择边/面的引用），示例工程改用等价的 OCC 形状运算
  (`makeFillet`/`makeThickness`)，主轮廓仍是参数化历史。
- 鼠标键位自定义与 Press/Pull 式直接操控受 FreeCAD 公开 API 限制。
- GUI 自动化受本机已知的 Qt/macOS 无障碍崩溃影响（见 docs/DEVELOPMENT.md），
  界面行为以工作台内置的「GUI 自检」命令验证。

许可与图标归属：代码 GPL-3.0-or-later（见 LICENSE）；全部图标为本项目原创生成
（`scripts/make_icons.py`），不含 Autodesk 等第三方专有资产；未捆绑任何第三方
运行时代码，详见 docs/LICENSES.md。
