# 03 主干路径

> 目标：只追「最常见的正常启动 / 运行」主干，忽略错误处理与边角分支。
> Done-when：能白板画出从 boot 到 init 的主干，标出每阶段的锁与所有权。
> **状态（增补 2026-09-21）**：**上游已 promote**（bootloader → `start_kernel`）；`start_kernel` 之内待做。
> 图集：[`diagrams/kernel-loading.md`](diagrams/kernel-loading.md)（10 张）——**本文引用，不复制**。
> 探索时间线：[`journal.md`](journal.md) J-0002~J-0020。

## 入口

- **入口点**：`init/main.c` 的 `start_kernel()`（C 主干起点）；其上游是汇编 `arch/x86/kernel/head_64.S:startup_64`。
- **触发方式**：固件 → bootloader 加载 `bzImage` → 跳 `code32_start`（默认 `0x100000`）。
- **最上游（源码外）**：GRUB / systemd-boot / UEFI 把 `bzImage` 读入内存；内核只提供契约——`arch/x86/boot/header.S` + `Documentation/arch/x86/boot.rst`。

## 阶段划分

| # | 阶段 | 职责 | 关键模块 | 进入条件 | 退出 / 转交 |
|---|------|------|---------|---------|------------|
| 0 | 固件 + bootloader | 读 bzImage、填 `boot_params`、跳入口 | GRUB（树外）；`boot/header.S` | 上电 | 跳 `code32_start` |
| 1 | 16-bit setup（legacy） | 内存/视频探测、进化保护模式 | `boot/main.c`、`boot/pm.c`、`boot/pmjump.S` | 16-bit protocol | `protected_mode_jump(code32_start)` |
| 2 | 自解压 stub | CPU 环境 + 解压真内核 | `boot/compressed/head_64.S`、`misc.c` | 32/64-bit protocol（或经阶段 1） | `jmp` 真内核入口 |
| 3 | 真内核早期汇编 | GDT/IDT/页表/段 | `kernel/head_64.S` | 解压完成 | `callq *initial_code` |
| 4 | C 起点 | 早期映射、微码、bootdata | `kernel/head64.c` | `.S → .C` 分界 | `start_kernel()` |
| 5 | **`start_kernel` 之内** | 架构初始化、调度/RCU、`rest_init` | `init/main.c`、`setup_arch`、`rest_init` | — | `kernel_init` → 用户空间 init |

> 阶段 0~4 全景见 [图 1](diagrams/kernel-loading.md)；三入口协议见 [图 8](diagrams/kernel-loading.md)；`.S → .C` 分界见 [图 10](diagrams/kernel-loading.md)。

## 关键调用链（主干）

> 用 `A() -> B() -> C()` 记录，标 `file:line`；**忽略错误返回分支**。

**阶段 0 · bootloader（树外）**
```
firmware -> GRUB: parse setup header -> load protected-mode part to code32_start
         -> fill boot_params (e820 / cmdline / initrd) -> jump entry
```

**阶段 1 · 16-bit setup（legacy，`arch/x86/boot/`）**
```
header.S:233 _start -> header.S:538 start_of_setup -> main.c:133 main()
  -> ... detect_memory / set_video ... -> pm.c go_to_protected_mode()
  -> pmjump.S protected_mode_jump(code32_start)
```

**阶段 2 · 自解压 stub（`arch/x86/boot/compressed/`）**
```
head_64.S:83  startup_32 -> head_64.S:286 startup_64 -> head_64.S:453 .Lrelocated
  -> misc.c:405 extract_kernel() -> misc.c:355 decompress_kernel() -> misc.c:365 __decompress()
  -> misc.c:294 parse_elf() -> head_64.S:483 jmp *%rax
```

**阶段 3 · 真内核早期汇编（`arch/x86/kernel/head_64.S`）**
```
startup_64:38 -> common_startup_64:188 -> callq *initial_code:413
  initial_code = x86_64_start_kernel (:474)
```

**阶段 4 · C 起点（`arch/x86/kernel/head64.c`）**  ← `.S → .C` 分界
```
x86_64_start_kernel:425 -> x86_64_start_reservations:491 -> start_kernel():507
```

**阶段 5 · `start_kernel`（`init/main.c`）**  ← 待做（下一工作单元）
```
start_kernel() -> setup_arch() -> ... -> rest_init() -> kernel_init() -> user-space init
```

## 核心数据结构

| 结构 | 定义位置 | 作用 | 被谁使用 |
|------|---------|------|---------|
| `struct boot_params` | `arch/x86/include/uapi/asm/bootparam.h` | 引导参数（"zero page"，4 KB） | loader/16-bit setup 填；`setup_arch` 读 |
| `struct setup_header hdr` | 同上（偏移 `0x1F1`） | bzImage 头 / boot protocol | loader 读改；内核读 |
| `e820_table[128]` | 同上（偏移 `0x2D0`） | 内存映射 | `e820__memory_setup()`（`arch/x86/kernel/setup.c:836`） |

> 字段细节见 `Documentation/arch/x86/zero-page.rst`、`boot.rst:185-268`；一生见 journal J-0011 / J-0020、[图 4](diagrams/kernel-loading.md)。

## 需要的背景概念

- **stub / piggyback / 自解压**：stub 是解压器，压缩内核以 `.incbin` 捎带进来（journal J-0008）。
- **boot protocol 三入口**：16 / 32 / 64-bit（journal J-0009、[图 8](diagrams/kernel-loading.md)）。
- **两个 `vmlinux`**：`compressed/vmlinux`（stub）vs 顶层 `vmlinux`（真内核）（journal J-0016）。
- **硬件信息多来源**：boot_params 只装最小集，其余内核自探（journal J-0020）。

## 锁与所有权（Done-when 要求）

- **阶段 0~4：单 CPU、无调度、无锁。** 所有权 = 控制权逐级移交（loader → setup → stub → 真内核）；数据 = `boot_params` 以寄存器（`%esi→%rsi→%r15→%rdi`）传递。
- **阶段 5 起**才出现真正的并发/所有权：`setup_arch` 的 memblock 分配、`rest_init` 的 kthreads、`start_kernel` 末期 `rcu_init`/调度器就绪。**待补**。

## 证据

- 图：`diagrams/kernel-loading.md`（图 1~10）
- 时间线：`journal.md` J-0002~J-0020
- 关键 `path:line`：`boot/header.S:233,271-273,538`；`boot/pm.c`（末行）；`boot/pmjump.S`；`boot/compressed/head_64.S:83,286,453,483`；`boot/compressed/misc.c:294,355,365,405`；`kernel/head_64.S:38,188,413,474`；`kernel/head64.c:425,491,507`；`arch/x86/kernel/setup.c:836`

## Open Questions

- **阶段 5 主干**：`start_kernel` → `setup_arch` → `rest_init` → `kernel_init` → 用户空间 init（**下一步**）。
- 加载链边角（EFI / KASLR / SMP 唤醒 / SEV-TDX / 5-level / setup_data）见 [`index.md`](index.md) 的 Parking。
