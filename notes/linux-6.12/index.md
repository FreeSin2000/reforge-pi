# Linux 6.12 (LTS)

> **TL;DR**
> - 是什么：单体宏内核操作系统，Linux 内核的长期支持版本，现代发行版的核心。
> - 现在读到：脚手架就位，尚未开始读源码。
> - 下一步：做 **01-structure**（顶层目录分类 + 核心阅读对象 + 入口文件）。
> - 卡在：无。
>
> 本文件保持**小而稳**：只放状态、问题、里程碑、Done-when 和四份文档的链接。细节都在 01~04。

**源码路径**：`src/linux-6.12/`

## 进度

- [ ] 01-structure —— 项目结构
- [ ] 02-build —— 构建方案
- [ ] 03-main-path —— 主干路径
- [ ] 04-debug-plan —— 动态调试方案

## Milestones（「能跑起来」的标志性节点）

- [ ] **M1 能构建**：从干净源码产出可运行的产物（bzImage / vmlinux）
- [ ] **M2 能运行**：qemu 启动到内核 console / 第一个用户进程
- [ ] **M3 能观测**：gdb 加载 vmlinux 符号，在启动关键函数命中第一个断点
- [ ] **M4 能追踪**：沿 03 的主干路径动态验证一个假设（如 `start_kernel` 调用链）

## Done-when（各文档的完成判据）

| 文档 | 算「读完」的标准 |
|------|-----------------|
| 01-structure | 不看树也能说出核心目录职责，并指出从哪个文件读起 |
| 02-build | 能从零复现构建（`x86_64_defconfig` → `bzImage`），说清主要选项与依赖 |
| 03-main-path | 能白板画出从 boot 到 init 的主干，标出每阶段的锁与所有权 |
| 04-debug-plan | 前置条件 checklist 全绿，且有 build/boot/debug 脚本 |

## 当前 Open Questions

- 最小可引导产物是什么？（vmlinux / bzImage / initramfs 的关系）
- 只读核心子系统时，如何建索引（cscope / universal-ctags / clangd）而不编译全树？
- 主干路径从 x86_64 的 `arch/x86/boot/` 还是 `init/main.c` 切入？
- 动态调试用 qemu `-s -S` + gdb，还是 kgdb？哪个准备成本更低？
- 是否需要 git 历史（`git log -S`）？若要，考虑 `--filter=blob:none` 部分克隆。

## Reading Log

| 日期 | 主题 | 结论 / 产出 | 证据 |
|------|------|-------------|------|
| 2026-09-21 | 建立脚手架 | 工作区约定 + 四份笔记模板 + 工具清单就位 | AGENTS.md / notes/_tooling/ |

## 快速事实

| 项 | 值 |
|----|----|
| 版本 / 发布日 | 6.12 LTS / 2024-11-17 |
| 语言 / 规模 | C 为主 + 少量 Rust；约 86,600 个文件、约 3,960 万行 |
| 文件构成 | `.c` ≈34,700 · `.h` ≈25,300 · `.S` ≈1,340 · `.rs` 76 |
| 解压体积 | 1.6 GB（其中 `drivers/` 1.1 GB 占 ~69%） |
| 构建系统 | Kbuild（顶层 `Makefile` + 1729 个 `Kconfig` + `scripts/` 518 个文件） |
| 默认配置样例 | `arch/x86/configs/x86_64_defconfig`（`.config` 需本地生成） |
| 许可证 | GPL-2.0（`COPYING`） |
| sha256 | `b1a2562be56e42afb3f8489d4c2a7ac472ac23098f1ef1c1e40da601f54625eb` |

> 体积/行数/目录占比由 `du`、`find | wc` 实测；工具现状见 `notes/_tooling/README.md`。
