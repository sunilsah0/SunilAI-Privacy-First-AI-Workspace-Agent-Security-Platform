"""Builds the two downloadable packages.

Run from the repository root:
    python scripts/make_packages.py v1.0.0            # writes to ./dist
    python scripts/make_packages.py v1.0.0 some/dir   # writes somewhere else

It packages the COMMITTED source (git archive) plus the edition-specific files.
"""
import hashlib
import pathlib
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKAGING = ROOT / "scripts" / "packaging"

EDITIONS = {
    "personal": {"preset": ".env.personal.example", "readme": "README-personal.md"},
    "enterprise": {"preset": ".env.enterprise.example", "readme": "README-enterprise.md"},
}
LEAVE_OUT = (".github", "tests", "backups", "dist")


def build(version: str, out: pathlib.Path) -> list[pathlib.Path]:
    out.mkdir(parents=True, exist_ok=True)
    built: list[pathlib.Path] = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = pathlib.Path(tmp)
        source_zip = tmp_path / "source.zip"
        subprocess.run(["git", "archive", "--format=zip", "-o", str(source_zip), "HEAD"],
                       cwd=ROOT, check=True)
        for edition, cfg in EDITIONS.items():
            name = f"SunilAI-{edition}-{version}"
            work = tmp_path / name
            with zipfile.ZipFile(source_zip) as z:
                z.extractall(work)
            for folder in LEAVE_OUT:
                shutil.rmtree(work / folder, ignore_errors=True)
            for preset in work.glob(".env*.example"):
                preset.unlink()
            if not (work / "docker-compose.release.yml").exists():
                raise SystemExit("docker-compose.release.yml is not committed. Commit your work first.")

            template = (ROOT / cfg["preset"]).read_text(encoding="utf-8")
            (work / ".env.template").write_text(template, encoding="utf-8", newline="\n")
            shutil.copy2(PACKAGING / "install.ps1", work / "install.ps1")
            shutil.copy2(PACKAGING / "install.sh", work / "install.sh")
            shutil.copy2(PACKAGING / cfg["readme"], work / "README-FIRST.md")
            shutil.rmtree(work / "scripts" / "packaging", ignore_errors=True)

            target = out / f"{name}.zip"
            with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
                for path in sorted(work.rglob("*")):
                    if path.is_file():
                        zf.write(path, f"{name}/{path.relative_to(work).as_posix()}")
            built.append(target)

    sums = [f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}" for p in built]
    (out / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n", encoding="ascii")
    return built


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: python scripts/make_packages.py <version> [output-folder]")
    version = sys.argv[1]
    out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "dist"
    for path in build(version, out):
        print("built", path)
    print("wrote", out / "SHA256SUMS.txt")


if __name__ == "__main__":
    main()
