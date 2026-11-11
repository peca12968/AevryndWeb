"""Copy, stage and verify precisely the r487 research archive."""
from pathlib import Path
from hashlib import file_digest, sha256
import json
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
REPO = Path('F:/AevryndStorage/CharacterHistoryGit')
SOURCE = Path('assets-source/aevrynd-character/female-next/r0487-source')
EVIDENCE = Path('evidence/character-female-next/r0487-continuous-posterior-groom')
PARENT = 'ba744051deef7c97e34181f47c4b62c21a8c4875'
BRANCH = 'character-history-v249'
REMOTE = 'https://github.com/peca12968/AevryndWeb.git'
ATTRIBUTES = (f'\n# r0487 posterior and ear route research\n'
              f'{SOURCE.as_posix()}/*.blend filter=lfs diff=lfs merge=lfs -text\n'
              f'{SOURCE.as_posix()}/data/*.npz filter=lfs diff=lfs merge=lfs -text\n'
              f'{EVIDENCE.as_posix()}/** -filter -diff -merge -text\n').encode('utf-8')


def git(*args):
    return subprocess.run(['git', *args], cwd=REPO, check=True, stdout=subprocess.PIPE).stdout


def digest(path):
    with path.open('rb') as stream:
        return file_digest(stream, 'sha256').hexdigest()


def manifest_entry(path):
    return dict(bytes=path.stat().st_size, sha256=digest(path))


def copy_archive():
    assert git('rev-parse', 'HEAD').decode().strip() == PARENT
    assert git('branch', '--show-current').decode().strip() == BRANCH
    assert git('remote', 'get-url', 'origin').decode().strip() == REMOTE
    assert not git('status', '--porcelain=v1')
    assert not (REPO / SOURCE).exists() and not (REPO / EVIDENCE).exists()
    report = json.loads((ROOT / 'r0487-review.json').read_text(encoding='utf-8'))
    source = Path(report['source']['path'])
    assert report['decision'] == 'REJECT_BOTH_FOR_CHARACTER_ADOPTION'
    assert digest(source) == report['source']['sha256']

    (REPO / SOURCE / 'data').mkdir(parents=True)
    (REPO / EVIDENCE).mkdir(parents=True)
    shutil.copyfile(source, REPO / SOURCE / source.name)
    for name in ('guide-paths.npz', 'guide-ownership.npz'):
        shutil.copyfile(ROOT / name, REPO / SOURCE / 'data' / name)
    licenses = REPO / SOURCE.with_name('r0486-source') / 'licenses'
    shutil.copytree(licenses, REPO / SOURCE / 'licenses')
    shutil.copyfile(ROOT / 'README-r0487.md', REPO / SOURCE / 'README.md')
    names = [
        'work-card.txt', 'inspect-r0487.py', 'plan-r0487.py', 'plan_r0487_import.py',
        'author-r0487.py', 'preview-r0487.py', 'run-r0487.ps1', 'make-review-r0487.ps1',
        'archive-r0487.py', 'inspection.json', 'guide-landmarks.json', 'construction-receipt.json',
        'reopen-verification.json', 'neutral-contact-probe.json', 'preview-receipt.json',
        'r0487-review.json', 'r0487-head-comparison.png', 'r0487-posterior-body-comparison.png',
    ]
    names.extend(f'{mode}-{view}.png' for mode in ('control', 'drape', 'sweep')
                 for view in ('face', 'rear-oblique', 'opposite-profile', 'posterior-detail', 'full-body'))
    names.extend(f'guides-{mode}-{view}.png' for mode in ('drape', 'sweep')
                 for view in ('opposite-profile', 'posterior-detail'))
    names.extend(f'{stem}.{extension}' for stem in ('inspect', 'guides', 'author', 'preview')
                 for extension in ('log', 'err'))
    for name in names:
        shutil.copyfile(ROOT / name, REPO / EVIDENCE / name)
    manifest = {}
    for root in (SOURCE, EVIDENCE):
        for path in sorted((REPO / root).rglob('*')):
            if path.is_file():
                manifest[path.relative_to(REPO).as_posix()] = manifest_entry(path)
    data = json.dumps(manifest, indent=2).encode('utf-8')
    (ROOT / 'archive-package-manifest.json').write_bytes(data)
    (REPO / EVIDENCE / 'archive-package-manifest.json').write_bytes(data)
    attributes = REPO / '.gitattributes'
    original = git('show', 'HEAD:.gitattributes')
    assert attributes.read_bytes() == original
    attributes.write_bytes(original + ATTRIBUTES)
    git('sparse-checkout', 'add', SOURCE.as_posix() + '/', EVIDENCE.as_posix() + '/')
    git('add', '--', '.gitattributes', SOURCE.as_posix(), EVIDENCE.as_posix())


def verify_archive():
    manifest_path = ROOT / 'archive-package-manifest.json'
    manifest = json.loads(manifest_path.read_bytes())
    manifest[(EVIDENCE / manifest_path.name).as_posix()] = manifest_entry(manifest_path)
    expected = set(manifest) | {'.gitattributes'}
    staged = set(git('diff', '--cached', '--name-only', '-z').decode().strip('\0').split('\0'))
    assert staged == expected, (staged - expected, expected - staged)
    assert git('rev-parse', 'HEAD').decode().strip() == PARENT
    assert not git('diff', '--name-only')
    assert git('show', ':.gitattributes') == git('show', 'HEAD:.gitattributes') + ATTRIBUTES
    git('diff', '--cached', '--check')
    lfs = []
    for name, entry in manifest.items():
        path = REPO / name
        assert manifest_entry(path) == entry, name
        blob = git('show', ':' + name)
        pointer = re.fullmatch(rb'version https://git-lfs.github.com/spec/v1\noid sha256:([a-f0-9]{64})\nsize ([0-9]+)\n', blob)
        if path.suffix in ('.blend', '.npz'):
            assert pointer is not None, name
            oid, size = pointer[1].decode(), int(pointer[2])
            assert oid == entry['sha256'] and size == entry['bytes'], name
            cached = REPO / '.git/lfs/objects' / oid[:2] / oid[2:4] / oid
            assert manifest_entry(cached) == entry, name
            lfs.append(dict(path=name, oid=oid, bytes=size))
        else:
            assert len(blob) == entry['bytes'] and sha256(blob).hexdigest() == entry['sha256'], name
    assert len(lfs) == 3
    receipt = dict(parent=PARENT, branch=BRANCH, exactStagedScopeVerified=True,
                   files=len(staged), lfsFiles=lfs, lfsBytes=sum(row['bytes'] for row in lfs))
    (ROOT / 'archive-staging-verification.json').write_bytes(json.dumps(receipt, indent=2).encode('utf-8'))
    print(json.dumps(receipt, indent=2), flush=True)


if __name__ == '__main__':
    import sys

    if sys.argv[1:] != ['--verify-only']:
        copy_archive()
    verify_archive()
