"""Prepare pinned browser assets after building the documentation site."""
import hashlib
import io
from pathlib import Path
import shutil
import tarfile
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "site" / "calculator"
URL = "https://registry.npmjs.org/@loumalouomega/gmsh-wasm/-/gmsh-wasm-0.4.0.tgz"
SHA256 = "d25b857e9694f8ae0ecc7fdd9d3076a57fa0e4dba6956d3a94c76e2570434ac9"
FILES = ("gmsh.mjs", "gmsh-core.mjs", "gmsh-core.wasm", "gmsh-descriptor.mjs", "runtime.mjs")

def main():
    if not (DEST / "index.html").is_file():
        raise SystemExit("Build the site first: python -m mkdocs build --strict")
    with urlopen(URL, timeout=120) as response:
        archive = response.read()
    if hashlib.sha256(archive).hexdigest() != SHA256:
        raise SystemExit("Gmsh archive checksum mismatch")
    vendor = DEST / "vendor"
    vendor.mkdir(exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
        for name in FILES:
            stream = tar.extractfile(f"package/dist/{name}")
            if stream is None:
                raise RuntimeError(f"Missing {name} in Gmsh archive")
            with (vendor / name).open("wb") as output:
                shutil.copyfileobj(stream, output)
        stream = tar.extractfile("package/LICENSE")
        if stream is None:
            raise RuntimeError("Missing Gmsh license")
        with (vendor / "LICENSE").open("wb") as output:
            shutil.copyfileobj(stream, output)
    shutil.copyfile(ROOT / "microstrip_quasistatic.py", DEST / "solver.py")
    print(f"Prepared browser calculator in {DEST}")

if __name__ == "__main__":
    main()
