"""Test a bounded range request on the same Git LFS download action."""
from pathlib import Path
from time import perf_counter
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen
from base64 import b64encode
import json
import subprocess

ROOT = Path(__file__).resolve().parent
ENDPOINT = 'https://github.com/peca12968/AevryndWeb.git/info/lfs/objects/batch'
MEDIA = 'application/vnd.git-lfs+json'
BRANCH_REF = 'refs/heads/character-history-v249'
REPO = Path('F:/AevryndStorage/CharacterHistoryGit')


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def origin_authorization():
    # Let Git use the same noninteractive credential helper as the normal LFS readback.
    request = b'url=https://github.com/peca12968/AevryndWeb.git/info/lfs\n\n'
    result = subprocess.run(['git', 'credential', 'fill'], cwd=REPO, input=request,
                            capture_output=True, check=True)
    fields = dict(line.split(b'=', 1) for line in result.stdout.splitlines() if b'=' in line)
    assert fields[b'protocol'] == b'https' and fields[b'host'] == b'github.com'
    return 'Basic ' + b64encode(fields[b'username'] + b':' + fields[b'password']).decode('ascii')


def get_download_actions(assets):
    objects = [{'oid': row['oid'], 'size': row['bytes']} for row in assets]
    payload = json.dumps(dict(operation='download', transfers=['basic'], ref={'name': BRANCH_REF},
                              objects=objects)).encode('utf-8')
    headers = {'Accept': MEDIA, 'Content-Type': MEDIA, 'Authorization': origin_authorization()}
    request = Request(ENDPOINT, data=payload, headers=headers, method='POST')
    with build_opener(NoRedirect()).open(request, timeout=15) as response:
        result = json.load(response)
    actual = {item['oid']: item for item in result['objects']}
    assert set(actual) == {item['oid'] for item in objects}
    return {row['oid']: actual[row['oid']]['actions']['download'] for row in assets}


def download_range(action, first, last, total):
    headers = dict(action.get('header', {}))
    headers['Range'] = f'bytes={first}-{last}'
    request = Request(action['href'], headers=headers)
    with urlopen(request, timeout=18) as response:
        expected = f'bytes {first}-{last}/{total}'
        assert response.status == 206 and response.headers.get('Content-Range') == expected
        data = response.read(last - first + 1)
    assert len(data) == last - first + 1
    return data


def main():
    proof = json.loads((ROOT / 'archive-staging-verification.json').read_bytes())
    asset = max(proof['lfsFiles'], key=lambda row: row['bytes'])
    action = get_download_actions([asset])[asset['oid']]
    first, length = 64 * 1024 * 1024, 1024 * 1024
    started = perf_counter()
    data = download_range(action, first, first + length - 1, asset['bytes'])
    elapsed = perf_counter() - started
    source = next(ROOT.glob('*.blend'))
    with source.open('rb') as stream:
        stream.seek(first)
        assert stream.read(length) == data
    record = dict(verifiedSampleBytes=length, offset=first, elapsedSeconds=elapsed,
                  bytesPerSecond=length/elapsed, status=206)
    (ROOT / 'remote-range-probe.json').write_bytes(json.dumps(record, indent=2).encode('utf-8'))
    print(record, flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # A temporary download action can contain a private signed query string.
        print('R494_RANGE_PROBE_FAILED', type(error).__name__, getattr(error, 'code', None), flush=True)
        raise SystemExit(1) from None
