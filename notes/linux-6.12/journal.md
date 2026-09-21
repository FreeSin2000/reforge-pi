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
