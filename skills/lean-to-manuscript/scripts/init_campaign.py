#!/usr/bin/env python3
"""Create the private working tree of a Lean-to-manuscript campaign.

Creates the directories and template files listed in lean-to-manuscript/references/phases.md ("The working
repository"): BRIEF.md, statement.md, STYLE.md, DETAIL-STANDARD.md, NOTATION.md, TERMINOLOGY.tsv, MORNING.md,
REGISTER.md, DISCLOSURE.md, spine/ (SPINE.md, SPINE-NATURAL.md, CLAUSE-MAP.tsv, DRIFT-LOG.md), prompts/, proposals/, reviews/,
rollout/, correspondence/. Tables (.tsv) receive their header line only, never a template's example rows. Templates are copied from the assets of the skills in this
collection when they are installed next to this one; a missing template is replaced by a one-line placeholder and
reported. Existing files are never overwritten unless --force is given.

The script writes templates only. It decides nothing: every decision in BRIEF.md is the author's.

Usage:
    python3 -I init_campaign.py WORKDIR [--title "The construction of ..."] [--dry-run] [--force]
"""
import argparse
import sys
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[2]          # .../skills
HERE = SKILLS / 'lean-to-manuscript' / 'assets'

DIRS = ['spine', 'prompts', 'prompts/superseded', 'proposals', 'reviews', 'rollout', 'correspondence', 'notes']

# destination -> list of candidate sources (first existing one wins), relative to the skills directory
FILES = {
    'BRIEF.md': ['lean-to-manuscript/assets/BRIEF.template.md'],
    'MORNING.md': ['lean-to-manuscript/assets/MORNING.template.md'],
    'REGISTER.md': ['lean-to-manuscript/assets/REGISTER.template.md'],
    'NOTATION.md': ['lean-to-manuscript/assets/NOTATION.template.md'],
    'statement.md': ['honest-publication/assets/statement-page.template.md'],
    'DISCLOSURE.md': ['honest-publication/assets/disclosure-wordings.md'],
    'STYLE.md': ['exposition-standards/assets/STYLE-template.md'],
    'DETAIL-STANDARD.md': ['exposition-standards/assets/DETAIL-STANDARD-template.md'],
    'TERMINOLOGY.tsv': ['exposition-standards/assets/terminology-header.tsv'],
    'spine/SPINE.md': ['statement-spine/assets/SPINE-template.md'],
    'spine/SPINE-NATURAL.md': ['statement-spine/assets/SPINE-NATURAL-template.md'],
    'spine/CLAUSE-MAP.tsv': ['statement-spine/assets/clause-map-header.tsv'],
    'spine/DRIFT-LOG.md': ['statement-spine/assets/drift-log-template.md'],
    'correspondence/correspondence.tsv': ['honest-publication/assets/correspondence.template.tsv'],
    'agents.json': ['writing-workflow/assets/agents.example.json'],
    'rollout/section-cycle.json': ['writing-workflow/assets/rollout.section-cycle.example.json'],
    'rollout/fixup.json': ['writing-workflow/assets/rollout.fixup.example.json'],
}

README = """# Working files (private)

Working tree of a Lean-to-manuscript campaign, created by init_campaign.py. Decisions: BRIEF.md. Binding rules:
STYLE.md and DETAIL-STANDARD.md. Progress: REGISTER.md and MORNING.md. The canonical manuscript lives elsewhere
and is edited by the editor only. Superseded prompts go to prompts/superseded/ and are never reused.
"""


def main() -> int:
    ap = argparse.ArgumentParser(
        description='Create the working tree of a Lean-to-manuscript campaign from the collection\'s templates.',
        epilog='Example: python3 -I init_campaign.py ~/my-paper-work --title "A natural-language proof of ..."')
    ap.add_argument('workdir', help='directory to create or complete')
    ap.add_argument('--title', default='<title of the manuscript>', help='title substituted into BRIEF.md')
    ap.add_argument('--dry-run', action='store_true', help='list what would be created; write nothing')
    ap.add_argument('--force', action='store_true', help='overwrite existing files')
    a = ap.parse_args()

    root = Path(a.workdir).expanduser()
    created, kept, missing = [], [], []
    for d in DIRS:
        p = root / d
        if not p.exists():
            created.append(f'{d}/')
            if not a.dry_run:
                p.mkdir(parents=True, exist_ok=True)
    for dest, cands in [('README.md', [])] + list(FILES.items()):
        p = root / dest
        if p.exists() and not a.force:
            kept.append(dest)
            continue
        if dest == 'README.md':
            text = README
        else:
            src = next((SKILLS / c for c in cands if (SKILLS / c).is_file()), None)
            if src is None:
                missing.append(f'{dest} (template not installed: {cands[0]})')
                text = f'# {Path(dest).stem}\n\nTemplate not found ({cands[0]}); fill in by hand.\n'
            else:
                text = src.read_text(encoding='utf-8')
                if dest.endswith('.tsv'):          # header and comment lines only; never the example rows
                    lines = text.splitlines(keepends=True)
                    keep = [l for l in lines if l.startswith('#')]
                    first = next((l for l in lines if not l.startswith('#')), '')
                    text = ''.join(keep) + first
        if dest.startswith('rollout/'):          # installed configs extend each other under their new names
            text = text.replace('"rollout.section-cycle.example.json"', '"section-cycle.json"')
        if dest == 'BRIEF.md':
            text = text.replace('<title of the manuscript>', a.title)
        created.append(dest)
        if not a.dry_run:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding='utf-8')
    verb = 'would create' if a.dry_run else 'created'
    for x in created:
        print(f'{verb}: {x}')
    for x in kept:
        print(f'kept (exists): {x}')
    for x in missing:
        print(f'placeholder: {x}')
    print(f'init_campaign: {len(created)} {verb}, {len(kept)} kept, {len(missing)} placeholders in {root}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
