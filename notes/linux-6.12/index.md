# Linux 6.12 (LTS)

> **TL;DR**
> - 是什么：单体宏内核操作系统，Linux 内核的长期支持版本，现代发行版的核心。
> - 现在读到：内核加载链路（`arch/x86/boot` → `start_kernel`）已探索并成图。
> - 下一步：按「路线图」推进 **W1**（`start_kernel` 全景）。
> - 卡在：无。
>
> 本文件保持**小而稳**：只放状态、问题、里程碑、Done-when 和四份文档的链接。细节都在 01~04。

**源码路径**：`src/linux-6.12/`

## 进度

- [ ] 01-structure —— 项目结构
- [ ] 02-build —— 构建方案
- [ ] 03-main-path —— 主干路径（**上游 boot→`start_kernel` 已 promote**；之内待做）
- [ ] 04-debug-plan —— 动态调试方案

## 路线图（进入内核主干，2026-09-21 规划）

> 从 `start_kernel` 到用户空间 init，拆成 **4 个工作单元**（每个 ≈ 一个会话，建议 `/name` 命名）；之后进子系统专题。
> 图集见 `diagrams/kernel-loading.md`；主要沉淀目标是 `03-main-path.md`。

| 单元 | 主题 | 关键入口 | 产出 |
|------|------|---------|------|
| **W1** | `start_kernel` 全景（总纲） | `init/main.c:903` | 03 阶段5 上半（初始化序列 + 分类） |
| **W2** | `setup_arch` 架构初始化 | `arch/x86/kernel/setup.c:729` | 03 + `_concepts`（memblock 等） |
| **W3** | 早期基础设施（percpu/sched/rcu/irq/time/console） | 各 `*_init` | 03 阶段5 |
| **W4** | `rest_init` → `kernel_init` → 用户空间 init | `init/main.c:701,1460` | 03 完成（Done-when）+ **M2** |
| W5+ | 子系统专题：mm / sched / fs / net / … | 各子系统 | 专题笔记 |
| 支线 | qemu+gdb 动态验证（M3/M4） | — | `04-debug-plan.md` |

**单元完成判据**：能白板画出该段主干 + 说清锁/所有权；边角 parking。

### 主题视角 · 主题 0：内核公共机制（“读内核的语言”）

> **定位**：不属于任何单一子系统，但**所有主题都要用**。目标不是深入，而是**认识词汇**。
> **Done-when**：能说清「用户调用 `read()` 怎么掉进内核」，并认识内核里最常见的公共 API（锁 / 分配 / `current`）。

| 子主题 | 从哪进入 | 关键入口 | 为什么先学 |
|--------|---------|---------|-----------|
| 0.1 系统调用 | 早期汇编 + CPU 初始化 | `head_64.S:386`(EFER.SCE)、`cpu/common.c:2072 syscall_init`、`entry_64.S:87 entry_SYSCALL_64`、`entry/common.c:76 do_syscall_64`、`entry/syscalls/syscall_64.tbl` | 用户↔内核唯一大门；每个主题都以 syscall 为入口 |
| 0.2 中断 / 异常 | `trap_init()` / `init_IRQ()` | `arch/x86/kernel/traps.c`、`arch/x86/kernel/irq/` | 与 syscall 同级的入口（IDT） |
| 0.3 并发原语 | `lockdep_init()` / `locking_selftest()` | `include/linux/{spinlock,mutex,rcupdate}.h` | 读任何并发代码的前提 |
| 0.4 内存分配 API | `mm_core_init` | `include/linux/{slab,gfp}.h` | 任何代码都在分配内存 |
| 0.5 `current` / per-cpu | `setup_per_cpu_areas()` | `include/asm/current.h`、`include/linux/percpu-defs.h` | “当前进程”是所有代码的隐含上下文 |
| 0.6 日志 / printk | `setup_log_buf()` / `console_init()` | `kernel/printk/` | 调试与观测的基础 |

**读多深**：0.1 精读入口链路；0.2~0.6 只到“认识 API + 知道谁提供”。深入留给对应子系统主题。

### 主题视角 · 主题 1：程序、进程、地址空间

> **Done-when**：能白板画出「一个进程的 `task_struct` + `mm_struct` + VMA + 页表 从哪来、怎么建、怎么被 `exec` 替换」。
> 路线 = 从 `start_kernel` 沿“能力递进”走到主题本体（执行顺序视角的 W1~W4 是同一段路）。

| 阶段 | 进入点（`start_kernel` 的一步） | 关键入口（file:line） | 为主题提供 |
|------|------------------------------|----------------------|-----------|
| A 内核地址空间地基 | `setup_arch` → `paging_init` | `arch/x86/kernel/setup.c:729`、`arch/x86/mm/init_64.c:822` | 内核页表 / 直接映射（参照系） |
| B 物理内存分配 | `mm_core_init` | `mm/mm_init.c:2636` | 页分配器 / slab（一切对象之母） |
| C 进程/地址空间对象缓存 | `fork_init` / `proc_caches_init` / `anon_vma_init` / `thread_stack_cache_init` | `kernel/fork.c:1041,3156,412`、`mm/rmap.c:461` | `task_struct`/`mm_struct`/VMA/`anon_vma` 缓存 |
| D PID + 调度 | `pid_idr_init` / `sched_init` | `kernel/pid.c:650` | 进程能被标识、被调度 |
| E 第一个进程诞生 | `rest_init` → `user_mode_thread` → `kernel_clone` → `copy_process` | `init/main.c:701`、`kernel/fork.c:2854,2745,2118` | **进程从无到有** |
| F 第一个程序执行 | `kernel_init` → `run_init_process` → `kernel_execve` → `do_execveat_common` → `load_elf_binary` | `init/main.c:1460,1378`、`fs/exec.c:1961,1876`、`fs/binfmt_elf.c:819` | **程序加载 + 地址空间替换** |
| G 主题深入 | （本体，不再依赖 `start_kernel`） | `include/linux/sched.h:778`、`include/linux/mm_types.h:790,667` | `task_struct`/`mm_struct`/VMA/页表 |

**读多深**：A~D 只需“知道提供了什么能力”；E/F 要看懂关键步骤；G 才是主题正文。

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

**已答（归档）**
- ~~最小可引导产物是什么？~~ → **bzImage**；`vmlinux` 是未压缩 ELF 原料，`Image` 未压缩 raw，`zImage` 已弃用（J-0007 / J-0012）。
- ~~主干路径从 `arch/x86/boot/` 还是 `init/main.c` 切入？~~ → 从 **boot** 切入；现已到 `start_kernel` 门口（图 1 / 图 10）。
- ~~硬件信息是否都在 boot_params？~~ → 不是；只有 e820/显示/EFI/RSDP 指针等最小集（J-0020）。

**待解（可能阻塞下一步）**
- 动态调试用 qemu `-s -S` + gdb，还是 kgdb？哪个准备成本更低？（→ `04-debug-plan`）
- 只读核心子系统时，如何建索引（cscope / universal-ctags / clangd）而不编译全树？（→ `_tooling`）
- 是否需要 git 历史（`git log -S`）？`src/linux-6.12` 是 tarball，无 `.git`。

**Parking（加载链的边角，暂不追）**
- EFI stub 路径细节（`compressed/efi.c` `efi_pe_entry`）——三入口之一。
- KASLR 实现（`choose_random_location`）。
- SMP CPU 唤醒（`secondary_startup_64`、`realmode/rm/trampoline_*`）。
- 内存加密启动（SEV/TDX：`mem_encrypt.S`、`tdx.c`）。
- 5-level paging 切换（`configure_5level_paging`）。
- `setup_data` 链 / `hardware_subarch`。
- legacy setup 每步 BIOS 调用细节（价值低）。

## Reading Log

| 日期 | 主题 | 结论 / 产出 | 证据 |
|------|------|-------------|------|
| 2026-09-21 | 建立脚手架 | 工作区约定 + 四份笔记模板 + 工具清单就位 | AGENTS.md / notes/_tooling/ |
| 2026-09-21 | 内核加载链路 | 5 张合规 ASCII 图落盘；建 tech-diagrams skill；沉淀改增量 | `notes/linux-6.12/diagrams/kernel-loading.md` / journal J-0002~J-0006 |
| 2026-09-21 | 加载链路扩展 | 图 6~10（构建链 / 自解压 / 三入口 / lds / 汇编→C）；bzImage 史、两个 vmlinux、stub 生成、硬件信息多来源 | `diagrams/kernel-loading.md` / journal J-0007~J-0020 |

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
