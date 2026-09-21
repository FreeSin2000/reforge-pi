#!/usr/bin/env python3
"""ASCII 图 linter —— 按 tech-diagrams 规范做确定性检查。

用法:
    python3 lint.py [-s SOFT] [-w HARD] FILE...     # 检查文件
    cat fig.txt | python3 lint.py                    # 检查 stdin

检查项:
    TAB   含 Tab（宽度可变，禁止）
    WSP   尾随空格
    WIDE  显示宽度超软上限（中文按 2 列计算）
    VWIDE 显示宽度超硬上限
    CJK   框内出现 CJK（│ ... │ 之间），易错位
    MIX   同一文件混用 box-drawing 与纯 ASCII 画线
退出码: 有 VWIDE/CJK/TAB/MIX 时为 1，否则 0。
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
        if line != line.rstrip(" \t") and line.strip():
            issues.append((i, "WSP", "行尾有空白"))
        if line.strip():
            if w > hard:
                issues.append((i, "VWIDE", f"宽度 {w} > {hard}"))
            elif w > soft:
                issues.append((i, "WIDE", f"宽度 {w} > {soft}"))
        if "│" in line and has_cjk(line):
            issues.append((i, "CJK", "框内出现中文"))
        bad = sorted({c for c in line if ord(c) > 0x7E
                      and c not in ALLOWED and not is_cjk(c) and not c.isspace()})
        if bad:
            pretty = " ".join(f"{c!r}(U+{ord(c):04X})" for c in bad)
            issues.append((i, "CHAR", f"非白名单字符: {pretty}"))
        if any(c in BOX for c in line):
            sees_box = True
        # 纯 ASCII 画线：连续 >=3 个 - 或 +--+ 或 | 竖线
        if "---" in line or "+--" in line or "--+" in line:
            sees_asciiline = True
    if sees_box and sees_asciiline:
        issues.append((0, "MIX", "box-drawing 与纯 ASCII 画线混用"))
    return issues, maxw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("-s", "--soft", type=int, default=80)
    ap.add_argument("-w", "--hard", type=int, default=100)
    a = ap.parse_args()

    if a.files:
        sources = [(f, open(f, encoding="utf-8").read().splitlines()) for f in a.files]
    else:
        sources = [("<stdin>", sys.stdin.read().splitlines())]

    hard_fail = False
    for name, lines in sources:
        issues, maxw = check(lines, a.soft, a.hard)
        print(f"\n== {name}  (max width {maxw}, soft {a.soft} / hard {a.hard}) ==")
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
