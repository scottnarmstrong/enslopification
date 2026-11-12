#!/usr/bin/env python3
"""Check that every relative Markdown link in the repository resolves, including #anchors.

Anchors resolve against explicit <a id="..."> tags and GitHub-style heading slugs (lower case, punctuation removed,
spaces to hyphens, -1, -2 for repeats). External links (http, https, mailto) are not fetched. Templates (files under
an assets/ directory) are skipped: their links point into the repository they will be copied to.

Usage: python3 -I tests/check_links.py [ROOT]      (default: the repository containing this file)
Exit 1 if any link is broken.
"""
import re
import sys
from pathlib import Path

LINK = re.compile(r'(?<!\!)\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)')
CODE = re.compile(r'```.*?```|`[^`\n]*`', re.S)


def slugs(text: str) -> set[str]:
    out, seen = set(), {}
    for m in re.finditer(r'<a\s+(?:id|name)="([^"]+)"', text):
        out.add(m.group(1))
    for line in CODE.sub('', text).splitlines():
        m = re.match(r'^(#{1,6})\s+(.*?)\s*#*\s*$', line)
        if not m:
            continue
        h = re.sub(r'<[^>]+>', '', m.group(2))
        h = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', h)          # link text only
        s = re.sub(r'[^\w\- ]', '', h.lower()).replace(' ', '-')
        n = seen.get(s, 0)
        out.add(s if n == 0 else f'{s}-{n}')
        seen[s] = n + 1
    return out


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    files = [p for p in root.rglob('*.md')
             if not {'.git', '.orchestrator', 'assets'} & set(p.relative_to(root).parts)]
    cache, bad, n = {}, 0, 0
    for f in sorted(files):
        text = f.read_text(encoding='utf-8')
        for m in LINK.finditer(CODE.sub('', text)):
            tgt = m.group(1)
            if re.match(r'^(https?|mailto):', tgt) or '{{' in tgt:
                continue
            n += 1
            path, _, anchor = tgt.partition('#')
            dest = (f.parent / path).resolve() if path else f
            if not dest.exists():
                print(f'BROKEN {f.relative_to(root)}: {tgt} (no such file)'); bad += 1; continue
            if anchor and dest.suffix == '.md':
                if dest not in cache:
                    cache[dest] = slugs(dest.read_text(encoding='utf-8'))
                if anchor not in cache[dest]:
                    print(f'BROKEN {f.relative_to(root)}: {tgt} (no anchor #{anchor})'); bad += 1
    print(f'check_links: {n} relative links in {len(files)} files, {bad} broken')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
