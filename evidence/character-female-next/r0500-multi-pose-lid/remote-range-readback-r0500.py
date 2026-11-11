"""Verify the pushed LFS objects through bounded, ordered byte ranges."""
from concurrent.futures import ThreadPoolExecutor
from collections import deque
from datetime import datetime, timezone
from hashlib import sha256
from itertools import islice
from pathlib import Path
from urllib.error import URLError
import json
import runpy
import subprocess

ROOT = Path(__file__).resolve().parent
probe = runpy.run_path(str(ROOT / 'probe-lfs-range-r0500.py'))
REPO = probe['REPO']
REF = probe['BRANCH_REF']
get_download_actions = probe['get_download_actions']
download_range = probe['download_range']
CHUNK = 8 * 1024 * 1024


def git(*args):
    return subprocess.run(['git', *args], cwd=REPO, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=True).stdout


def verify_remote_tip(commit):
    assert git('rev-parse', 'HEAD').decode().strip() == commit
    assert git('ls-remote', '--exit-code', 'origin', REF).decode().split()[0] == commit
    assert git('status', '--porcelain=v1') == b''


def fetch(action, first, last, size):
    for attempt in range(3):
        try:
            return download_range(action, first, last, size)
        except (URLError, TimeoutError):
            if attempt == 2:
                raise


def read_object(asset, action, destination):
    size = asset['bytes']
    ranges = iter((first, min(first + CHUNK, size) - 1) for first in range(0, size, CHUNK))
    digest = sha256()
    written = 0
    partial = destination.with_suffix('.part')
    with ThreadPoolExecutor(max_workers=4) as workers, partial.open('xb') as stream:
        pending = deque(workers.submit(fetch, action, first, last, size)
                        for first, last in islice(ranges, 4))
        while pending:
            data = pending.popleft().result()
            stream.write(data)
            digest.update(data)
            written += len(data)
            following = next(ranges, None)
            if following is not None:
                pending.append(workers.submit(fetch, action, *following, size))
            if written % (4 * CHUNK) == 0 or written == size:
                print('R500_RANGE_READBACK', Path(asset['path']).name, written, size, flush=True)
    assert written == size and digest.hexdigest() == asset['oid']
    partial.replace(destination)


def main():
    commit = (ROOT / 'local-commit.txt').read_text().strip()
    proof = json.loads((ROOT / 'archive-staging-verification.json').read_bytes())
    assert git('rev-parse', 'HEAD^').decode().strip() == proof['parent']
    assert git('remote', 'get-url', 'origin').decode().strip() == 'https://github.com/peca12968/AevryndWeb.git'
    verify_remote_tip(commit)
    assets = proof['lfsFiles']
    for asset in assets:
        expected = ('version https://git-lfs.github.com/spec/v1\n'
                    f'oid sha256:{asset["oid"]}\nsize {asset["bytes"]}\n').encode()
        assert git('show', commit + ':' + asset['path']) == expected
    actions = get_download_actions(assets)
    cache = ROOT / 'range-readback-cache'
    cache.mkdir()
    verified = []
    for asset in assets:
        read_object(asset, actions[asset['oid']], cache / asset['oid'])
        verified.append(asset | dict(readbackMatches=True))
    verify_remote_tip(commit)
    result = dict(repository='https://github.com/peca12968/AevryndWeb', branch=proof['branch'], commit=commit,
                  commitURL='https://github.com/peca12968/AevryndWeb/commit/' + commit, exactRemoteTipVerified=True,
                  workingTreeClean=True, verifiedFreshLFSObjects=verified, transport='Git LFS basic action with ordered HTTP ranges',
                  recordedAtUTC=datetime.now(timezone.utc).isoformat())
    (ROOT / 'github-archive-receipt.json').write_bytes(json.dumps(result, indent=2).encode('utf-8'))
    print(result['commitURL'], flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # Error details may include a private signed download action.
        print('R500_RANGE_READBACK_FAILED', type(error).__name__, getattr(error, 'code', None), flush=True)
        raise SystemExit(1) from None
