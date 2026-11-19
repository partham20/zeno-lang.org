"""Add a release to the site's tools/releases.json from its public files.

    python3 releases_add.py <releases.json> <version> <date>

The names and checksums come from the release's SHA256SUMS.txt, and each
size from the answer to a HEAD request for the file."""
import hashlib, json, subprocess, sys

path, version, date = sys.argv[1:4]
base = f"https://github.com/zeno-src/zeno-lang/releases/download/v{version}/"

def get(url):
    return subprocess.run(["curl", "-sSL", "-m", "60", url], capture_output=True, check=True).stdout

def size(url):
    head = subprocess.run(["curl", "-sSIL", "-m", "60", url], capture_output=True, text=True, check=True).stdout
    lengths = [line.split(":")[1].strip() for line in head.splitlines() if line.lower().startswith("content-length:")]
    return int(lengths[-1])

sums = get(base + "SHA256SUMS.txt")
assets = []
for line in sums.decode().splitlines():
    digest, name = line.split()
    assets.append({"name": name, "size": size(base + name), "url": base + name, "sha256": digest})
assets.append({"name": "SHA256SUMS.txt", "size": len(sums), "url": base + "SHA256SUMS.txt",
               "sha256": hashlib.sha256(sums).hexdigest()})
assets.sort(key=lambda a: a["name"].lower())
releases = [r for r in json.load(open(path)) if r["tag"] != f"v{version}"]
releases.append({"tag": f"v{version}", "name": f"Zeno {version}", "date": date,
                 "url": f"https://github.com/zeno-src/zeno-lang/releases/tag/v{version}", "assets": assets})
releases.sort(key=lambda r: [int(n) for n in r["tag"][1:].split(".")], reverse=True)
open(path, "w").write(json.dumps(releases, indent=1) + "\n")
print(version, len(assets), "files")
