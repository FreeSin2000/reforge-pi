# 工具与索引（第 0.5 步）

「怎么在 40M 行里找到一行」是独立的基础设施问题。本目录记录本机工具现状、用途与安装方式。

## 现状（实测）

| 类别 | 工具 | 状态 | 用途 |
|------|------|:----:|------|
| 搜索 | ripgrep (rg) 14.1 | ✅ | 快速文本搜索 |
| 构建 | gcc 13.3 / make 4.3 / binutils 2.42 | ✅ | 编译链接 |
| 构建依赖 | flex / bison / bc / libncurses-dev / libssl-dev / libelf-dev | ✅ | 内核构建所需 |
| 调试 | qemu-system-x86_64 10.1 / gdb 15.1 / tmux | ✅ | 动态调试 |
| 导航 | cscope 15.9 | ✅ | 符号索引、找调用者 / 被调用者（本地 `~/.local/bin`，免 root） |
| 导航 | universal-ctags 5.9 | ✅ | 生成 tags，供编辑器 / CLI 跳转（`~/.local/bin/ctags` → `ctags-universal`） |
| 语义 | clangd + bear | ❌ | 编译数据库驱动的语义跳转 |
| 调试信息 | dwarves (pahole) | ❌ | 查看结构体内存布局 / BTF |
| 符号源 | libdw-dev | ❌ | 仅当从源码构建 pahole 才需要 |

**结论**：构建、调试、基础导航（`rg` + `cscope` + `ctags`）**已就绪**；还差语义层（`clangd`/`bear`）与 `pahole`。

## 安装状态

- **已完成（免 root，本地安装）**：`cscope`、`universal-ctags` → `~/.local/bin/`。
- **待安装（需要你的 sudo 密码）**：`clangd`、`bear`、`dwarves`。

  ```bash
  sudo bash notes/_tooling/install-tools.sh
  ```

  脚本会安装 `cscope universal-ctags clangd bear dwarves`（前两个已本地就绪，重复安装无害）。
  > 若 `universal-ctags` 与系统里 Emacs 自带的 `ctags` 冲突，apt 会提示替换——按提示确认即可。

## 用途与建议

- **cscope**：内核传统导航首选，`cscope -Rbkq` 建库，支持「谁调用我 / 我调用了谁」。大树上比 `grep` 强得多。
- **universal-ctags**：配合编辑器跳转，也能用 `readtags` 命令行查询。
- **clangd + bear**：`bear -- make ...` 生成 `compile_commands.json`，语义级跳转 / 引用。成本较高、可选。
- **pahole**：读结构体真实内存布局、看 padding / 缓存行，调试内存与并发时有用。

## 索引范围原则

**建索引前先限定范围**（例如只对 `kernel/ mm/ fs/ include/ arch/x86/`），不要为全树 40M 行建臃肿索引——这直接决定后续检索的 token 成本。
