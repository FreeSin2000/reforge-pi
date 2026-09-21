# 内核加载链路：bootloader → `start_kernel`（x86_64 / bzImage）

> **结论**：内核加载分两段 —— bootloader 把 `bzImage` 读进内存（加载逻辑在外部项目，**协议头**在内核里），
> 内核再自解压、自举到 `start_kernel`。
> **三条入口**：现代 GRUB 直接跳 `code32_start`；legacy 走 16-bit setup；EFI stub 让 UEFI 直接引导。
> **证据**：每图节点标 `path:line`，路径相对 `src/linux-6.12/`。
> **上游探索**：`notes/linux-6.12/journal.md` → J-0002 / J-0003。
> **制图规范**：`tech-diagrams` skill（纯 ASCII，宽度 ≤80，框内无中文）。

## 图 1 · 全景调用链（5 阶段）

```text
 stage 0 - firmware + bootloader              (outside kernel tree)
 ------------------------------------------------------------------------
   BIOS / UEFI firmware
        |  read MBR(0x7C00) or ESP loader
        v
   +--------------------------------------------------------------+
   | GRUB / systemd-boot / U-Boot        [external project]       |
   |   1. parse bzImage setup header (header.S fields)            |
   |   2. locate protected-mode kernel via setup_sects            |
   |   3. copy it to code32_start (default 0x100000)              |
   |   4. fill boot_params: e820 / cmdline / initrd              |
   |   5. enter 32-bit protected mode, jump code32_start          |
   +--------------------------------------------------------------+
        |  (modern GRUB skips the 16-bit setup below)
        v
 stage 1 - 16-bit setup (legacy boot-sector path)         real mode
 ------------------------------------------------------------------------
   header.S:233  _start                 short jmp
   header.S:538  start_of_setup
        |- normalize CS:DS, set stack
        |- verify setup_sig == 0x5a5aaa55
        |- clear bss
        `- calll main
   boot/main.c:133  main()
        |- copy_boot_params()
        |- console_init() / init_heap() / validate_cpu()
        |- detect_memory() / keyboard_init() / query_ist()
        |- query_apm_bios() / query_edd() / set_video()
        `- go_to_protected_mode()
   boot/pm.c        go_to_protected_mode()
        |- setup_idt() / setup_gdt()
        `- protected_mode_jump(code32_start, &boot_params)
        |
        v
 stage 2 - self-extracting stub              arch/x86/boot/compressed/
 ------------------------------------------------------------------------
   protected mode (32-bit)
   head_64.S:83   startup_32             first insn of prot-mode kernel
        |- cli / cld
        |- relocate delta -> %ebp (short call/pop)
        |- load GDT, reload segs, set stack
        |- verify_cpu()                  long-mode check
        |- build identity page tables (first 4G)
        |- CR4.PAE=1, CR3=pgtable, EFER.LME=1
        `- lret ------------------------------+
   long mode (64-bit)                           v
   head_64.S:286  startup_64
        |- choose decompression target (2M aligned)
        |- set stack boot_stack_end
        |- load_stage1_idt() / sev_enable()
        |- configure_5level_paging()     4 <-> 5 level switch
        |- copy compressed kernel to buffer end (in-place)
        `- jmp .Lrelocated
   head_64.S:453  .Lrelocated
        |- clear bss / load_stage2_idt() / initialize_identity_maps()
        |- call extract_kernel(boot_params, output)      misc.c:405
        |      |- sanitize_boot_params() / console_init()
        |      |- choose_random_location()               KASLR
        |      |- decompress_kernel()                    inflate vmlinux
        |      `- return output + entry_offset
        `- jmp *%rax ==============================> real kernel
        |
        v
 stage 3 - real kernel early asm              arch/x86/kernel/head_64.S
 ------------------------------------------------------------------------
   long mode (64-bit), physical addr + identity map
   head_64.S:38   startup_64
        |- %rsi(boot_params) -> %r15
        |- stack __top_init_kernel_stack
        |- GSBASE = fixed_percpu_data (stack canary)
        |- startup_64_setup_gdt_idt()
        |- lretq -> __KERNEL_CS
        |- sme_enable() / verify_cpu()
        |- __startup_64(_text, boot_params)   page-table fixup
        |- CR3 = early_top_pgt
        `- jmp *0f(%rip)
   head_64.S:188  common_startup_64
        |- fix CR4 (keep PAE/LA57/MCE, set PSE/PGE)
        |- per-CPU / smpboot_control
        |- reload GDT, set ds/ss/es/fs/gs, GSBASE
        |- early_setup_idt()
        |- EFER |= SCE/NX; CR0 = CR0_STATE; clear EFLAGS
        |- %rdi = %r15 (boot_params)
        `- callq *initial_code(%rip)             head_64.S:413
   head_64.S:474  initial_code = x86_64_start_kernel
        |
        v
 stage 4 - early C startup                    arch/x86/kernel/head64.c
 ------------------------------------------------------------------------
   head64.c:425   x86_64_start_kernel(real_mode_data)
        |- cr4_init_shadow() / reset_early_page_tables()
        |- clear_bss() / clear_page(init_top_pgt)
        |- sme_early_init() / kasan_early_init()
        |- idt_setup_early_handler() / tdx_early_init()
        |- copy_bootdata(__va(real_mode_data))
        |- load_ucode_bsp()              early microcode
        `- x86_64_start_reservations(real_mode_data)
   head64.c:491   x86_64_start_reservations()
        |- x86_early_init_platform_quirks()
        |- switch (hardware_subarch)
        `- start_kernel() =======================> init/main.c
```

一句话结论：`start_kernel` 之前，CPU 经历 **实模式 → 保护模式 → 长模式**，且一直用**物理地址 + 恒等映射**；页表重定位与 KASLR 都发生在解压 stub 里。

## 图 2 · bzImage 磁盘布局

```text
 bzImage file  (assembled by boot/tools/build.c:171-240)
+--------------------------------------+ 0x000
| PE/COFF header (EFI stub)            |
| sentinel (0xFF 0xFF)                 |
+--------------------------------------+ 0x1F1
| setup header (hdr)                   |
|   setup_sects                        |
|   boot_flag = 0xAA55  @ 0x1FE        |
+--------------------------------------+ 0x200
| _start (legacy boot sector)          |  header.S:233
| 16-bit setup code (setup.bin)        |  -> boot/main.c -> boot/pm.c
| (setup_sects * 512 B, min 5)         |
+--------------------------------------+ (setup_sects+1)*512
| protected-mode kernel                |  = vmlinux.bin
|   first insn = startup_32            |  <- self-extracting stub
|   last 4 bytes = CRC32               |
+--------------------------------------+ EOF
```

一句话结论：bootloader 只读 `0x1F1` 的 setup header 来“认识”内核；`0x200` 起的 16-bit setup 现代 GRUB 会跳过；`protected-mode` 段就是“压缩内核 + 自解压 stub”。（原料如何造出来，见 §图 6。）

## 图 3 · 内存布局（解压前 / 后）

```text
 [1] before: bootloader-loaded physical layout
   0x00000  +---------------------------+
            | real-mode data / zeropage |
            |   boot_params             | <-- ptr travels in %esi/%rsi
            +---------------------------+
            | ...                       |
   0x100000 +---------------------------+
            | protected-mode kernel     |
            |   startup_32 (entry)      |
            |   [compressed vmlinux]    |
            +---------------------------+

 [2] after: extract_kernel decompresses to final place (misc.c:390)
                        compressed image
                              |
              |               |                 |
    0    extract_offset     ...            +INIT_SIZE
    +-----------+---------------+----------------------+--------+
                |               |                      |        |
          VO__text      ZO startup_32            VO__end  ZO__end
                ^                                        ^
                +------ uncompressed kernel (VO) --------+
```

一句话结论：`extract_kernel` 先 `choose_random_location()` 选 KASLR 基址，再把内嵌 vmlinux 解压到目标地址，返回 `output + entry_offset`。

## 图 4 · `boot_params` 的一生（数据流）

```text
 bootloader fills setup header (header.S)
        |
        v
 boot_params (zeropage, low memory)
        |
        |- setup/main.c: copy_boot_params()          [legacy path]
        |
        v
 %esi  --> compressed startup_32 / startup_64        32-bit -> 64-bit
        |        (reads fields via BP_* macros)
        v
 extract_kernel(rmode=%rsi, output)             misc.c:405
        |
        v
 kernel startup_64: %rsi --> %r15               head_64.S:44
        |
        v
 x86_64_start_kernel(char *real_mode_data)      head64.c:425
        |
        v
 copy_bootdata() --> global boot_params         head64.c:397
```

一句话结论：`boot_params` 从 bootloader 手里一路以**寄存器**（`%esi`→`%rsi`→`%r15`→`%rdi`）传递，最终由 `copy_bootdata()` 固化到全局。

## 图 5 · 特权级 / 执行环境时间轴

```text
 real mode (16)     | protected mode (32)     | long mode (64)
 -------------------+-------------------------+---------------------------->
 header.S:_start    |                         |
 start_of_setup     |                         |
 boot/main.c main() |                         |
 boot/pm.c jump --->| startup_32 (stub,32bit) |
                    |   `- lret ------------->| startup_64 (stub,64bit)
                    |                         |   `- jmp ---+
                    |                         |            v
                    |                         | kernel startup_64
                    |                         |   -> common_startup_64
                    |                         |   -> x86_64_start_kernel
                    |                         |   -> start_kernel
```

一句话结论：三条入口最终都汇聚到 64-bit 的 `startup_64`（真内核），再进入 C 语言的 `start_kernel`。

## 图 6 · 构建链：`vmlinux` 怎么变成 bzImage

```text
 build time - how bzImage is assembled
 ---------------------------------------------------------------------
   [all obj-y] --ar--> vmlinux.a --ld--> vmlinux.o
                                            |  scripts/Makefile.vmlinux
                                            v
                                        vmlinux            (ELF, uncompressed)
                                            | objcopy -R .comment -S
                                            v
                                       vmlinux.bin         (trimmed, still ELF)
                                            | + vmlinux.relocs (if relocatable)
                                            v
                                     vmlinux.bin.all
                                            | gzip  (+ append u32 orig size)
                                            v
                                     vmlinux.bin.gz        (+ 4-byte size)
                                            |
        +-----------------------------------+
        |  mkpiggy.c --> piggy.S:  .incbin "vmlinux.bin.gz"
        v
   stub vmlinux  [ decomp code | .rodata..compressed data ]
        |  boot/tools/build.c: setup.bin + vmlinux.bin + CRC32
        v
      bzImage
```

一句话结论：`vmlinux` 是未压缩 ELF 的“真身”；被 objcopy 瘦身、压缩后由 `mkpiggy.c` 用 `.incbin` **捎带**进解压 stub，再和 `setup.bin` 拼成 bzImage。

## 图 7 · 自解压 stub 运行链

```text
 run time - what the self-extracting stub does
 ---------------------------------------------------------------------
   startup_32 (32-bit) -> startup_64 (64-bit) -> .Lrelocated
        |
        v
   extract_kernel(boot_params, output)              misc.c:405
        |- choose_random_location()                 KASLR base
        v
   decompress_kernel(outbuf, virt_addr)             misc.c:355
        |- __decompress(input_data, input_len,
        |               outbuf, output_len, ...)
        |     input_data  = piggy .incbin blob
        |     __decompress = ONE algo, fixed at BUILD time
        |       (misc.c:65-89 #include lib/decompress_<algo>.c)
        |- parse_elf(outbuf)      -> entry point      misc.c:294
        `- handle_relocations(...)
        |
        v
   return output + entry_offset  --> jmp *%rax
```

一句话结论：stub 自己解压（解压器**编译时选定**，非运行时探测），解压后还要 `parse_elf` + `handle_relocations`，最后 `jmp` 到真内核入口。
