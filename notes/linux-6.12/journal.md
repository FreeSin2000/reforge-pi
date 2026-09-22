# Linux 6.12 探索日志（journal）

> 探索循环的**时间线**，记录频繁、条目可短。记「问题 / 假设 / 发现 / 困惑 / 反例」，
> **包括错的假设**——后续用新条目修正，不删旧条目。
>
> **稳定结论只在综合检查点 promote** 到 01~04 / `glossary.md` / `map.md` / `_concepts/`，并在此留下 `→` 指针。

**类型**：疑问 · 假设 · 发现 · 困惑 · 反例
**置信度**：低 · 中 · 高　　**状态**：未定 · 待验证 · 已定

---

### J-0001 · 2026-09-21 · 项目顶层如何组织

- **类型**：发现 / 疑问
- **问题**：linux 这棵树是怎么组织的？从哪读起？
- **尝试解释**：不是「一个应用」，而是**按子系统 × 架构的目录树**；同一棵树被四套正交系统解释：
  1. **代码**：顶层 24 个目录，通用子系统（`kernel/ mm/ fs/ net/ ipc/ block/ io_uring/ security/ crypto/ sound/`）+ 架构相关（`arch/<arch>/`）+ 驱动（`drivers/` 143 个子目录）+ 共享头文件（`include/`）+ 库（`lib/`）。顶层**没有** `.c` 文件（`ls *.c` = 0），全部下沉到目录。
  2. **构建**：Kbuild 三件套——顶层 `Makefile`（版本/编译器/目标）+ 每个目录的 `Makefile`/`Kbuild`（`obj-y` 递归下降）+ `Kconfig`（配置树，顶层 `Kconfig` 用 `source` 拼出整棵配置树）。目录树即构建树（`Kbuild` 尾部 `obj-y += init/ usr/ arch/$(SRCARCH)/ ...`）。
  3. **人**：`MAINTAINERS`（78 万字节）把 `F:` 路径模式映射到维护者/邮件列表/树。
  4. **文档**：`Documentation/`（75 个子目录，reStructuredText，`make htmldocs`）。
- **规模分布**：`drivers/` 1.1G ≈ 69%（噪音，不通读）；真正主干很小——`init/` 200K、`kernel/` 15M、`mm/` 5.7M、`fs/` 51M、`ipc/` 280K。
- **阅读入口（初判）**：`init/main.c`（`start_kernel`）→ `kernel/`（调度/进程）→ `mm/`（内存）→ `arch/x86/`（架构层，含 `boot/`）；`drivers/` 按需当参考。`include/linux/`（1536 个头文件）是内核内部 API 总线，`include/uapi/` 是与用户态共享的 ABI，`include/asm-generic/` 是跨架构回退。
- **证据**：`src/linux-6.12/` 顶层 `ls`、`du -sh */`、`Makefile:1-8`、`Kbuild` 尾部、`Kconfig`、`README`、`MAINTAINERS:1-40`。
- **置信度**：中
- **状态**：待验证（入口链尚未实读，仅凭目录结构判断）
- **去向**：候选 promote 进 `01-structure.md`
- **标签**：#结构 #kbuild #入口

### J-0002 · 2026-09-21 · `start_kernel` 之前：内核如何被加载

- **类型**：发现 / 疑问
- **问题**：`init/main.c` 之前，「内核如何被加载」在源码中有体现吗？
- **尝试解释**：**一半在源码里，一半不在**。拆成两段：
  - **(a) bootloader → 内核入口**：加载逻辑（GRUB/systemd-boot/UEFI）**不在内核树里**；内核源码只提供**接口**——`arch/x86/boot/header.S` 里的 boot protocol 头（`hdr`、`boot_flag=0xAA55`、`code32_start`），规范在 `Documentation/arch/x86/boot.rst`（1444 行）。
  - **(b) 内核自解压/重定位 → `start_kernel`**：**全在源码里**，是“自举 stub”。
- **验证的调用链（x86_64, bzImage 路径）**：
  1. bootloader 把 protected-mode 部分加载到 `code32_start`（默认 0x100000），保护模式跳入 →
  2. `arch/x86/boot/compressed/head_64.S:83 startup_32` → `:286 startup_64` → `:453 .Lrelocated`
  3. `.Lrelocated` 调 `arch/x86/boot/compressed/misc.c:405 extract_kernel()`，解压内嵌的 vmlinux 并返回入口地址 → `jmp *%rax`
  4. → `arch/x86/kernel/head_64.S:38 startup_64` → `:188 common_startup_64` → `:413 callq *initial_code(%rip)`
  5. `initial_code = x86_64_start_kernel`（`head_64.S:474`）
  6. `arch/x86/kernel/head64.c:425 x86_64_start_kernel` → `:491 x86_64_start_reservations` → `:507 start_kernel()`
  7. → `init/main.c`
- **另有两条岔路（暂 parking）**：
  - **遗留 16-bit 路径**：`header.S:233 _start` → `:538 start_of_setup` → `arch/x86/boot/main.c:133 main()`（内存探测/显存/BIOS 查询）→ `go_to_protected_mode()`。只用于从 boot sector（软盘/MBR）启动。
  - **EFI stub 路径**：`CONFIG_EFI_STUB` 把 bzImage 变成 PE 可执行文件，UEFI 直接引导（`arch/x86/boot/compressed/efi.c`）。
- **产物构建**：`arch/x86/boot/Makefile:19` targets = `vmlinux.bin setup.bin setup.elf bzImage`；`bzImage = build(setup.bin, vmlinux.bin)`。
- **证据**：上列 `path:line` 均为实读；`Documentation/arch/x86/boot.rst:1-60`。
- **置信度**：高（每条跳转都在源码中定位到）
- **状态**：已定
- **去向**：候选 promote 进 `03-main-path.md`（作为启动主干的最上游一段）
- **标签**：#启动 #boot-protocol #arch-x86

### J-0003 · 2026-09-21 · 加载链路详细化（特权级 / 内存布局 / boot_params）

- **类型**：发现
- **目的**：把 J-0002 的链路补成可画图的细节：特权级迁移、bzImage 组成、解压前/后内存布局、boot_params 数据流。
- **特权级迁移**：bootloader（含固件）→ `code32_start` 以 **32-bit 保护模式** 进 `startup_32` → `lret` 进 **long mode（64-bit）** 的 `startup_64` → 一路 64-bit 到 `start_kernel`。
- **bzImage 磁盘布局**（`boot/tools/build.c:171-240`）：setup（≥5 扇区，补齐）+ protected-mode kernel（= `vmlinux.bin` = `compressed/vmlinux`）+ 末尾 4 字节 CRC32。字段：0x1F1 `hdr`/setup_sects，0x1FE `boot_flag=0xAA55`，0x200 `_start`，`0x202 "HdrS"` v0x020f，`code32_start` 默认 0x100000。
- **三条入口**：
  1. 现代 bootloader（GRUB `linux`）直接跳 `code32_start`，**跳过 16-bit setup**；
  2. legacy：`header.S:_start(0x200)` → `start_of_setup` → `boot/main.c:main()` → `pm.c:go_to_protected_mode()` → `protected_mode_jump(code32_start,...)`；
  3. EFI stub：`CONFIG_EFI_STUB`，UEFI 直接引导 PE，`compressed/efi.c:efi_pe_entry`。
- **解压细节**：`compressed/head_64.S:413 .Lrelocated` 调 `misc.c:405 extract_kernel`；内部 `choose_random_location()`（KASLR）、`decompress_kernel()`，返回 `output + entry_offset`；`.Lrelocated` 末尾 `jmp *%rax` 跳真内核。`startup_64`（compressed）还负责 4↔5 级页表切换 `configure_5level_paging()` 与把压缩内核拷到缓冲区末尾以便**原地解压**（`std; rep movsq`）。
- **真内核早期汇编**：`kernel/head_64.S:38 startup_64`（`%rsi`→`%r15`，`startup_64_setup_gdt_idt`，`__startup_64` 重定位页表，CR3←`early_top_pgt`，`jmp common_startup_64`）→ `:188 common_startup_64`（cr4、GDT/段/IDT、EFER SCE/NX、CR0、`callq *initial_code`）→ `:474 initial_code = x86_64_start_kernel`。
- **boot_params 一生**：bootloader 填 → `copy_boot_params()` → `%esi`（32-bit）→ `%rsi`→`%r15`（64-bit）→ `x86_64_start_kernel(char *real_mode_data)` → `copy_bootdata()` → 全局 `boot_params`。
- **证据**：见正文每行 `path:line`；`boot/tools/build.c:171-240`、`head_64.S` 全文实读。
- **置信度**：高
- **状态**：已定
- **去向**：候选 promote 进 `03-main-path.md`（替换/扩写 J-0002 版本）
- **标签**：#启动 #bzImage #boot_params

### J-0004 · 2026-09-21 · 工作区演进：建图 skill + 沉淀改增量

- **类型**：决定
- **背景**：本次会话反复画加载链路 ASCII 图，暴露出两个约定不便：① 画图方法没固化，每次重写；②「综合检查点」把沉淀压到低频、一次性，负担重。
- **动作**：
  1. 建 skill `.pi/skills/tech-diagrams/`（`SKILL.md` + `references/patterns.md` 8 类图型模板 + `references/style.md` 排版清单）；当前**仅纯 ASCII**，不引外部工具（npm/WASM/浏览器方案已验证但按用户要求暂缓）。
  2. 改 `AGENTS.md`：「综合检查点」→「**增量检查点**」，pi 可自主触发、一次只 promote 一个主题、固定文档可反复增补；放开「不建 skill」约定。
- **证据**：`AGENTS.md:40,53,70,87,120`；`.pi/skills/tech-diagrams/`。
- **置信度**：高
- **状态**：已定
- **去向**：约定已落到 AGENTS.md（单一事实来源），此处只留时间线
- **标签**：#工作区 #skill #沉淀节奏

### J-0005 · 2026-09-21 · 自查：刚画的图不合规 + 上了 lint

- **类型**：发现 / 反例
- **问题**：拿 `tech-diagrams` 规范回头查本次画的加载链路图，是否达标？
- **尝试解释**：**不达标**。实测（`scripts/lint.py`）：
  - 框内中文 16 处（fig1×9 / fig2×6 / fig4×1）——违反「中文慎入图内」，等宽下会错位；
  - 非白名单字符：`· ← → … ★`（违反“只用 ASCII/box-drawing”）；
  - 尾随空格 3 处（fig3）；
  - 跨图字符集不统一（fig1/2 用 box-drawing，fig3 用纯 ASCII）。
  - 达标项：宽度全部 ≤80；节点基本带 `file:line`；阶段分隔带与 `▼` 主语义正确。
- **动作**：给 skill 加 `scripts/lint.py`（查宽度/尾随空格/Tab/框内中文/非法字符/字符集混用）与 SKILL.md 自检节；给出 `fig2` 合规重写示范（框内全 ASCII、中文移到图外）。
- **证据**：`/tmp/figs/*` + lint 输出；`.pi/skills/tech-diagrams/scripts/lint.py`。
- **置信度**：高
- **状态**：已定（工具就绪；**旧图本身尚未重画**）
- **去向**：若要 promote 进 `03-main-path.md`，先按新规范重画
- **标签**：#skill #ascii #自查

### J-0006 · 2026-09-21 · 图重画落盘 + lint --md

- **类型**：决定
- **承接**：J-0005（旧图不合规、待重画）。
- **动作**：
  1. 按 `tech-diagrams` 规范重画 5 张加载链路图（纯 ASCII、框内无中文、宽度 69~76），落盘 `notes/linux-6.12/diagrams/kernel-loading.md`；
  2. `lint.py` 加 `--md` 模式（直接检查 markdown 内的 fenced code block），5 块全绿。
- **证据**：`notes/linux-6.12/diagrams/kernel-loading.md`；`lint.py --md` 输出。
- **置信度**：高
- **状态**：已定
- **去向**：可作 `03-main-path.md` 的最上游素材（尚未 promote）
- **标签**：#启动 #ascii #落盘

### J-0007 · 2026-09-21 · bzImage 是什么 / 全称 / 历史

- **类型**：发现
- **问题**：`bzImage` 是什么？全称与历史？
- **尝试解释**：
  - 全称 **big zImage**。源码旁证：`arch/x86/boot/header.S:273` 注释 `# 0x100000 = default for big kernel`；`boot.rst` 未逐字写 “big zImage”。（全称置信度：中——公认解释 + 旁证，非文档逐字）
  - `z` = 压缩自解压（gzip/zlib）。`bzImage` 把压缩内核加载到 **0x100000（1MB）**，突破 `zImage` 的 **0x10000（<640K，≤512K）** 限制。
  - 时间线：Protocol 2.00（kernel **1.3.73**，1.3.x 开发系列）引入 bzImage（`boot.rst:20`）；`zImage` 已 deprecated（`boot.rst:32`）。
  - 现代 x86 实际只用 bzImage；`all: bzImage` 为默认（`arch/x86/Makefile:303,308`）。
- **证据**：`boot.rst:20,32,245,1195-1207`；`arch/x86/boot/header.S:273`；`arch/x86/boot/Makefile:19,68`；`arch/x86/Makefile:300,306,308`。
- **置信度**：高（地址/历史）/ 中（全称措辞）
- **状态**：已定
- **去向**：可补进 `diagrams/kernel-loading.md` 作背景段
- **标签**：#启动 #bzImage #历史

### J-0008 · 2026-09-21 · vmlinux 与 self-extracting stub 原理

- **类型**：发现
- **问题**：vmlinux 是什么？自解压 stub 是什么、原理？
- **尝试解释**：
  - **vmlinux** = 内核完整真身，**未压缩 ELF**（含符号），由 `vmlinux.o` + 链接脚本链接（`Makefile:1165` → `scripts/Makefile.vmlinux`；`vmlinux.lds.S:41 ENTRY(phys_startup_64)`）。bootloader **不直接加载**它。
  - **stub** = `arch/x86/boot/compressed/` 编译出的 `vmlinux`，即 bzImage 的 protected-mode 部分；官方定性 “self-extracting executable”（`init/Kconfig:273`）。
  - **piggyback**：`mkpiggy.c` 生成 `piggy.S`，用 `.incbin` 把 `vmlinux.bin.gz` 嵌进 `.rodata..compressed`，并从压缩文件尾部读 u32 原长作 `z_output_len`。
  - **解压器编译时选定**：`misc.c:65-89` 条件 `#include` 一个 `lib/decompress_<algo>.c`（提供 `STATIC __decompress`）；默认 gzip（`init/Kconfig:271`）。**≠** 运行时魔数分发（`lib/decompress.c` 的 `decompress_method` 是 initramfs 用）。
  - **运行**：`extract_kernel` → `decompress_kernel` → `__decompress` → `parse_elf` → `handle_relocations` → `entry` → `jmp`。
- **证据**：`Makefile:1142,1165`；`scripts/Makefile.vmlinux:34-36`；`vmlinux.lds.S:41`；`arch/x86/boot/compressed/Makefile:8-20`；`mkpiggy.c:52-63`；`misc.c:65-89,294,355-373`；`init/Kconfig:271-273`。
- **置信度**：高
- **状态**：已定
- **去向**：可补进 `diagrams/kernel-loading.md`（构建链图）
- **后续**：图 6（构建链）/ 图 7（运行链）已补入 `diagrams/kernel-loading.md`。
- **标签**：#启动 #vmlinux #自解压

### J-0009 · 2026-09-21 · boot protocol 三入口 / code32_start 语义

- **类型**：发现（含对图的修正）
- **问题**：16-bit setup 是否经 `protected_mode_jump` 跳 `code32_start`？`code32_start` 是什么？现代 GRUB 是否跳过 setup？
- **尝试解释**：
  1. ✅ **16-bit**：`pm.c` 的 `go_to_protected_mode()` 末行 `protected_mode_jump(boot_params.hdr.code32_start, ...)`；`pmjump.S` 置 CR0.PE、`ljmpl` 进 32-bit、最后 `jmpl *%eax`。
  2. `code32_start` = **保护模式跳转地址**，默认 = 内核加载地址（`boot.rst:534`），默认值 `0x100000`（`header.S:271-273`）；relocatable 内核加载到非标准地址时 bootloader 必须改它（`boot.rst:671-673`）。
  3. ✅ **现代 GRUB 跳过 setup**——因为 boot protocol 有**三种入口**（`boot.rst:1337-1444`）：
     - **16-bit**：跑 setup → `protected_mode_jump` → `code32_start`
     - **32-bit**：保护模式、paging off，直接跳 `code32_start`（= kernel start = `startup_32`）
     - **64-bit**：64-bit、paging on，直接跳 `code32_start + 0x200`（= `startup_64`；对应 `compressed/head_64.S` 的 `.org 0x200`）
     - EFI handover（deprecated）/ EFI stub
- **含义**：64-bit loader **直接进 `startup_64`**，不经过 `startup_32` 的 32-bit 部分；`startup_32`(offset 0) / `startup_64`(offset 0x200) 的偏移是 **ABI**。→ 图 1 / 图 5 需补注。
- **证据**：`boot/pm.c` 末行；`boot/pmjump.S`；`boot.rst:526-541,671-673,1195-1207,1337-1444`；`header.S:271-273`；`compressed/head_64.S:83,286`。
- **置信度**：高
- **状态**：已定
- **去向**：更新 `diagrams/kernel-loading.md`（补三入口 / 图1,5 注）
- **标签**：#启动 #boot-protocol #code32_start

### J-0010 · 2026-09-21 · legacy setup 做了什么 / 现代谁代理

- **类型**：发现
- **问题**：legacy 16-bit setup 做了哪些事？现代 GRUB 是否代理了同样的事？
- **尝试解释**：
  - legacy setup（`boot/main.c` 的 `main()`）**13 步**：init_default_io_ops → copy_boot_params → console_init → init_heap → validate_cpu → set_bios_mode → detect_memory(e820/e801/88) → keyboard_init → query_ist → query_apm_bios → query_edd → set_video → go_to_protected_mode。
  - **官方表述**（`zero-page.rst:6-8`）：boot_params 各字段 “should be **filled by bootloader or 16-bit real-mode setup code**” —— 二选一。所以现代 GRUB **是**代理了“参数填充”，但方式是直接写 boot_params，不是重跑 setup 代码。
  - 数据落点/消费者不变：内核 `setup_arch` → `e820__memory_setup()` 读 `boot_params.e820_table`（`arch/x86/kernel/setup.c:836`）。
  - 职责三分：① bootloader 接管（内存/显示/cmdline/initrd/boot_params）；② 内核后续接管（建 memblock、CPU 校验、early console）；③ 淘汰（APM/EDD/keyboard/IST，字段 OBSOLETE）。
- **证据**：`boot/main.c:11-180`；`boot/memory.c:18-119`；`zero-page.rst:1-49`；`arch/x86/kernel/setup.c:836`。
- **置信度**：高
- **状态**：已定
- **去向**：可作 `diagrams/kernel-loading.md` 图 8 的注
- **标签**：#启动 #setup #boot-protocol

### J-0011 · 2026-09-21 · boot_params 结构、字段与文档位置

- **类型**：发现
- **问题**：boot_params 有哪些字段？含义？文档里有描述吗？
- **尝试解释**：
  - `boot_params` = “**zero page**”，固定 **4096 B**、16 字节对齐（`main.c:36 BUILD_BUG_ON`）；bootloader / 16-bit setup 填，内核 `copy_bootdata()` 保存为全局。
  - 四大块：① 固件/BIOS 信息（0x000-0x1F0：screen_info/apm_bios_info/ist_info/acpi_rsdp_addr/edid_info/efi_info…）；② `setup_header hdr`（0x1F1-0x268+，**就是 bzImage 头**）；③ `edd_mbr_sig_buffer`(0x290) 与 `e820_table[128]`(0x2D0)；④ `eddbuf`(0xD00)。
  - **文档分两份**（易漏）：`boot.rst:185-268` 讲 `hdr` 字段（带 read/write/modify 语义）；`zero-page.rst:1-47` 讲其余字段。
  - 结构体在 `arch/x86/include/uapi/asm/bootparam.h`（UAPI ABI）；子结构在 `screen_info.h`/`apm_bios.h`/`edd.h`/`asm/ist.h`/`video/edid.h`/`setup_data.h`。
- **证据**：`uapi/asm/bootparam.h`；`boot.rst:185-268`；`zero-page.rst:1-47`；`boot/main.c:36`。
- **置信度**：高
- **状态**：已定
- **去向**：可作 `diagrams/kernel-loading.md` 的 zero page 布局图（图 9?）
- **标签**：#启动 #boot_params #zero-page

### J-0012 · 2026-09-21 · code32_start 处到底是什么

- **类型**：确认（核实用户假设）
- **假设**：`code32_start` 处 = self-extracting stub + 压缩的保护模式 kernel？
- **尝试解释**：**基本正确，但要精确**：
  - `code32_start` 处是 bzImage 的 protected-mode 段，即 `compressed/vmlinux`——一个 **PIE ELF**。
  - 它**不是两段独立的东西**：stub 是代码主体，压缩内核是它的 `.rodata..compressed` **数据段**（由 `piggy.S` 的 `.incbin` 嵌入）。**同一个 ELF**。
  - offset 0 = `startup_32`（32-bit 入口，ABI）；offset 0x200 = `startup_64`（64-bit 入口，ABI）。
  - bootloader 只搬这一段 + 跳入口；解压目标 `output` 由 `choose_random_location()` / `LOAD_PHYSICAL_ADDR` 定，**不一定 = code32_start**。
- **证据**：`boot/Makefile:73`（vmlinux.bin ← compressed/vmlinux）；`compressed/Makefile:8-20`；`compressed/head_64.S:83,286`；`boot.rst:1191-1193`；`compressed/misc.c:405,517`。
- **置信度**：高
- **状态**：已定
- **去向**：`diagrams/kernel-loading.md` 图 7 / 图 9 可补注
- **标签**：#启动 #stub #code32_start

### J-0013 · 2026-09-21 · boot 相关链接脚本（.lds.S / .ld）

- **类型**：发现
- **问题**：有没有 .ld 脚本？
- **尝试解释**：有多个层级（`find arch/x86 -name '*.ld*'`）：
  - `arch/x86/boot/compressed/vmlinux.lds.S` — **stub 的链接脚本**：`ENTRY(startup_64/32)`；`. = 0`（注释：head_64.S 假定 startup_32 在地址 0）；段 `.head.text`(HEAD_TEXT) / `.rodata..compressed`(piggy) / .text/.rodata/.data/.bss/.pgtable；DISCARD + ASSERT 掉 .got/.plt/.rel（PIE 约束）。
  - `arch/x86/boot/setup.ld` — 16-bit setup：`ENTRY(_start)`；`. = 0`；`.bstext`(定位 495) / `.header` / `.entrytext`(start_of_setup)；`.signature` 里 `setup_sig=0x5a5aaa55`；ASSERT `_end<=0x8000`、**`hdr==0x1f1`**、`__end_init<=5*512`。
  - `arch/x86/kernel/vmlinux.lds.S` — 真内核：`ENTRY(phys_startup_64)`；`LOAD_OFFSET=__START_KERNEL_map`。
  - 其他：`realmode/rm/realmode.lds.S`、`entry/vdso/*.lds.S`、`scripts/module.lds.S`；通用宏 `include/asm-generic/vmlinux.lds.h`。
- **彩蛋**：`setup.ld` 的 `ASSERT(hdr == 0x1f1)` 就是 boot protocol 里 **hdr 固定在 0x1F1** 的来源。
- **证据**：`compressed/vmlinux.lds.S:15-27`；`setup.ld:8-70`；`kernel/vmlinux.lds.S:34-41`。
- **置信度**：高
- **状态**：已定
- **去向**：`diagrams/kernel-loading.md` 可补“三个 ELF / lds”关系
- **标签**：#构建 #链接脚本 #stub

### J-0014 · 2026-09-21 · startup_32/64 属于哪个产物

- **类型**：发现
- **问题**：`startup_32` / `startup_64` 在内核里还是 setup.bin？源码如何体现？
- **尝试解释**：**在 protected-mode kernel（vmlinux.bin / stub），不在 setup.bin**。
  - 定义：`boot/compressed/head_64.S:83 startup_32`（offset 0，注释 “32bit entry is 0 and it is ABI”）、`:286 startup_64`（`.org 0x200`，注释 “64bit entry is 0x200 and it is ABI”）；`boot/compressed/head_32.S:46 startup_32`。
  - 编译：`boot/compressed/Makefile:88` `vmlinux-objs-y := ... head_$(BITS).o` → 编入 stub。
  - 定位：`boot/compressed/vmlinux.lds.S` 把 HEAD_TEXT 放 offset 0，`ENTRY(startup_64)`。
  - setup.bin 的 `setup-y`（`boot/Makefile:23-27`）**不含 head_*.o**；其入口是 `header.S:_start` → `start_of_setup` → `main`（main.o）。
  - 同名陷阱：全树 **5 处 startup_32**（compressed 头㉂㉁2、kernel/head_32、realmode trampoline 头㉂㉁2）、**3 处 startup_64**（compressed、kernel/head_64、realmode trampoline_64）。
- **证据**：上述 `path:line`。
- **置信度**：高
- **状态**：已定
- **去向**：可补 `diagrams/kernel-loading.md` 图 9/10（入口符号归属）
- **标签**：#启动 #stub #head

### J-0015 · 2026-09-21 · 解压发生在哪：startup 符号 vs startup 序列

- **类型**：澄清
- **问题**：“不是在 startup 被解压缩吗？”
- **尝试解释**：**解压在 stub 的启动序列里，但不在 `startup_32/64` 符号内**。
  - `startup_32`(head_64.S:83) / `startup_64`(:286) 只做入场准备（GDT/段/栈/页表/长模式/算目标/拷压缩数据到缓冲区末尾），`startup_64` 末尾 `jmp .Lrelocated`(:448)。
  - `.Lrelocated`(:453) 才 `call extract_kernel`(:477)。
  - `extract_kernel`(misc.c:405) → `decompress_kernel`(misc.c:355) → `__decompress`(misc.c:365)（`lib/decompress_<algo>.c`）真正 inflate。
  - 所以：若“startup”指整段启动序列/stub，对；若指 `startup_32/64` 符号本身，不准。
- **证据**：`head_64.S:83,286,448,453,477`；`misc.c:355,365,405,517`。
- **置信度**：高
- **状态**：已定
- **标签**：#启动 #stub #解压

### J-0016 · 2026-09-21 · 两个“vmlinux”：stub 与真内核同名

- **类型**：澄清 / 发现（命名陷阱）
- **问题**：startup_32/64 不是 vmlinux 里的符号吗？
- **尝试解释**：**对——但要区分两个都叫 `vmlinux` 的产物**：
  - **(A) `arch/x86/boot/compressed/vmlinux`** = **stub**（`compressed/Makefile:110` 链接 `vmlinux-objs-y` = head_$(BITS).o + misc.o + piggy.o…）。含 `startup_32`@0 / `startup_64`@0x200。其 objcopy → `arch/x86/boot/vmlinux.bin`（`boot/Makefile:73`）= bzImage 的 protected-mode 段。
  - **(B) 顶层 `./vmlinux`**（`Makefile:1165`）= **真内核**（高位链接）。含 `kernel/head_64.S:38 startup_64` + `phys_startup_64`。被压缩成 `vmlinux.bin.gz`（`compressed/Makefile:126`）嵌入 (A)。
  - 所以“startup 是 vmlinux 里的符号”对 (A) 成立；用户没说错，是**命名复用**造成歧义。
  - **重名产物**：`vmlinux` ×2（compressed/=stub、顶/=真内核）、`vmlinux.bin` ×2（`compressed/vmlinux.bin`=真内核瘦身；`boot/vmlinux.bin`=stub raw）。
- **证据**：`compressed/Makefile:20,110,114,126,153`；`boot/Makefile:73`；顶层 `Makefile:1165`；`kernel/vmlinux.lds.S:41`。
- **置信度**：高
- **状态**：已定
- **去向**：可作 `diagrams/kernel-loading.md` 图 10（两个 vmlinux / 命名复用）
- **标签**：#启动 #vmlinux #命名

### J-0017 · 2026-09-21 · stub 如何生成

- **类型**：发现
- **问题**：stub 是如何生成的？
- **尝试解释**：stub 由**两股输入**汇合：
  - **(A) 行李 = 压缩的真内核**：顶层 `vmlinux` --objcopy--> `compressed/vmlinux.bin`（`:114`）--+relocs→`vmlinux.bin.all`（`:123`）--gzip+`size_append`(追 u32 原长)-->`vmlinux.bin.gz`（`:126`；`Makefile.lib:334`）--`mkpiggy`-->`piggy.S`(`.incbin`)（`:153`）-->`piggy.o`。
  - **(B) stub 自己的代码**：`vmlinux-objs-y`（`:88-108`）= head_$(BITS).o + misc.o + string.o + cmdline.o + error.o + cpuflags.o + kernel_info.o（+ kaslr.c/pgtable_64.c/idt_64.o …）。
  - **(A)+(B)** `ld -T vmlinux.lds` → `compressed/vmlinux`（**STUB ELF, PIE**）（`:110`）→ objcopy → `boot/vmlinux.bin`（raw）→ build.c 拼 bzImage。
  - 重定位：`arch/x86/Makefile.postlink` 在 X86_NEED_RELOCS 时导出 `vmlinux.relocs` 并从 vmlinux 剥离 .rel*。
- **证据**：`compressed/Makefile:20,88-110,114,123,126,153`；`scripts/Makefile.lib:334`；`arch/x86/Makefile.postlink`；`boot/Makefile:68,73`。
- **置信度**：高
- **状态**：已定
- **去向**：与 `diagrams/kernel-loading.md` 图 6（构建链）对应
- **标签**：#构建 #stub #piggy

### J-0018 · 2026-09-21 · stub -> 真内核的分界点

- **类型**：确认
- **假设**：从 `boot/compressed/head_64.S` 跳到 `kernel/head_64.S` 才是真正进入内核？
- **尝试解释**：**基本对**。
  - 分界点：`compressed/head_64.S:483` 的 `jmp *%rax`（`.Lrelocated` 末尾）。
  - 目标：`parse_elf` 返回 `ehdr.e_entry - LOAD_PHYSICAL_ADDR`（`misc.c:346`）；真内核 ELF 的 `e_entry` = `ENTRY(phys_startup_64)`（`kernel/vmlinux.lds.S:41,117`）= `startup_64 - LOAD_OFFSET` → `kernel/head_64.S:38 startup_64`。
  - 所以跳到 `kernel/head_64.S` 的 `startup_64` 后，即“真内核”（解压后长期运行的那份）。
  - 措辞：stub 也是内核源码的一部分（广义内核），但狭义“真内核”从 `kernel/head_64.S` 开始；stub 是临时解压器。
  - 交接：boot_params 经 `%rsi`→`%r15`→`%rdi`；后续 `startup_64`→`common_startup_64`→`x86_64_start_kernel`(`head64.c`)。
- **证据**：`head_64.S:453,477,483`；`misc.c:346,405,517`；`kernel/vmlinux.lds.S:41,117`；`kernel/head_64.S:38`。
- **置信度**：高
- **状态**：已定
- **标签**：#启动 #stub #真内核

### J-0019 · 2026-09-21 · 用户梳理校正：.S→.C 的分界

- **类型**：澄清
- **用户的梳理**：stub 解压+处理 boot_params → 跳真内核 startup → start_kernel（.S→.C）→ init/main.c
- **尝试解释**：**前两条对；第 3、4 条要纠正**：
  - **.S→.C 的分界不是 `start_kernel`**，而是 `kernel/head64.c:425 x86_64_start_kernel`（由 `kernel/head_64.S` 的 `callq *initial_code` 调用，`head_64.S:413,474`）。
  - **`start_kernel` 就在 `init/main.c`**（不是“之后才是 main.c”）。链路：`x86_64_start_kernel` → `x86_64_start_reservations`（都在 head64.c）→ `start_kernel()`（head64.c:507 调用，定义在 `init/main.c`）。
  - 另外“初始化硬件”更准确是“初始化 **CPU 执行环境**（GDT/段/栈/页表/长模式）”；外设/内存管理初始化在 `start_kernel` 之后（`setup_arch` 等）。
- **正确分层**：[asm] `compressed/head_64.S` → [asm] `kernel/head_64.S` → [C] `head64.c` → [C] `init/main.c`
- **证据**：`kernel/head_64.S:38,188,413,474`；`head64.c:425,491,507`；`init/main.c start_kernel`。
- **置信度**：高
- **状态**：已定
- **标签**：#启动 #主干 #start_kernel
