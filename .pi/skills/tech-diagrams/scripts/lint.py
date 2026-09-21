#!/usr/bin/env python3
"""ASCII 图 linter —— 按 tech-diagrams 规范做确定性检查。

用法:
    python3 lint.py FILE...              # 检查纯图文本
    python3 lint.py --md FILE.md...      # 提取 markdown fenced code block 再检查
    cat fig.txt | python3 lint.py        # 检查 stdin

检查项:
    TAB   含 Tab（宽度可变，禁止）
    WSP   尾随空格
    WIDE  显示宽度超软上限（中文按 2 列计算）
    VWIDE 显示宽度超硬上限
    CJK   框线（| 或 │）之间出现中文，易错位
    CHAR  非白名单字符（非 ASCII、非 box-drawing、非箭头）
    MIX   同一文件混用 box-drawing 与纯 ASCII 画线
退出码: 有 VWIDE/CJK/TAB/MIX/CHAR 时为 1，否则 0。
"""
import sys
import unicodedata
import argparse

BOX = set("─│┌┐└┘├┤┬┴┼═║╔╗╚╝╠╣╦╩╬")
ARROWS = set("▼►◄▲")
ALLOWED = BOX | ARROWS
CJK_RANGES = ((0x2E80, 0x9FFF), (0x3000, 0x303F), (0xFF00, 0xFFEF))


def dwidth(s: str) -> int:
    w = 0
    for ch in s:
        if unicodedata.combining(ch):
            continue
        w += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return w


def is_cjk(ch: str) -> bool:
    return any(lo <= ord(ch) <= hi for lo, hi in CJK_RANGES)


def has_cjk(s: str) -> bool:
    return any(is_cjk(c) for c in s)


def check(lines, soft, hard):
    issues = []
    maxw = 0
    sees_box = sees_asciiline = False
    for i, raw in enumerate(lines, 1):
        line = raw.rstrip("\n")
        w = dwidth(line)
        maxw = max(maxw, w)
        if "\t" in line:
            issues.append((i, "TAB", "含 Tab"))
        if line.strip() and line != line.rstrip(" \t"):
            issues.append((i, "WSP", "行尾有空白"))
        if line.strip():
            if w > hard:
                issues.append((i, "VWIDE", f"宽度 {w} > {hard}"))
            elif w > soft:
                issues.append((i, "WIDE", f"宽度 {w} > {soft}"))
        if ("│" in line or "|" in line) and has_cjk(line):
            issues.append((i, "CJK", "框内出现中文"))
        bad = sorted({c for c in line if ord(c) > 0x7E
                      and c not in ALLOWED and not is_cjk(c) and not c.isspace()})
        if bad:
            pretty = " ".join(f"{c!r}(U+{ord(c):04X})" for c in bad)
            issues.append((i, "CHAR", f"非白名单字符: {pretty}"))
        if any(c in BOX for c in line):
            sees_box = True
        if "---" in line or "+--" in line or "--+" in line:
            sees_asciiline = True
    if sees_box and sees_asciiline:
        issues.append((0, "MIX", "box-drawing 与纯 ASCII 画线混用"))
    return issues, maxw


def extract_blocks(text):
    """取出 markdown 的 fenced code block 内容（每个块一行列表）。"""
    blocks, cur = [], None
    for ln in text.splitlines():
        if ln.lstrip().startswith("```"):
            if cur is None:
                cur = []
            else:
                blocks.append(cur)
                cur = None
            continue
        if cur is not None:
            cur.append(ln)
    if cur is not None:
        blocks.append(cur)
    return blocks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--md", action="store_true", help="只检查 markdown fenced code blocks")
    ap.add_argument("-s", "--soft", type=int, default=80)
    ap.add_argument("-w", "--hard", type=int, default=100)
    a = ap.parse_args()

    if a.files:
        sources = [(f, open(f, encoding="utf-8").read()) for f in a.files]
    else:
        sources = [("<stdin>", sys.stdin.read())]

    hard_fail = False
    for name, text in sources:
        if a.md:
            blocks = extract_blocks(text)
            if blocks:
                units = [(f"{name} block#{i}", b) for i, b in enumerate(blocks, 1)]
            else:
                units = [(name, None)]
        else:
            units = [(name, text.splitlines())]

        for uname, lines in units:
            if lines is None:
                print(f"\n== {uname} ==\n  (no fenced code blocks)")
                continue
            issues, maxw = check(lines, a.soft, a.hard)
            print(f"\n== {uname}  (max width {maxw}, soft {a.soft} / hard {a.hard}) ==")
            if not issues:
                print("  OK")
                continue
            for ln, code, msg in issues:
                loc = f"L{ln:<4}" if ln else "file"
                print(f"  {loc} {code:<6} {msg}")
                if code in ("VWIDE", "CJK", "TAB", "MIX", "CHAR"):
                    hard_fail = True
    print()
    sys.exit(1 if hard_fail else 0)


if __name__ == "__main__":
    main()
