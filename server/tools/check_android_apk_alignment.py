from __future__ import annotations

import argparse
import struct
import sys
import zipfile
from pathlib import Path


def _data_offset(zf: zipfile.ZipFile, info: zipfile.ZipInfo) -> int:
    fp = zf.fp
    if fp is None:
        raise RuntimeError("zip file is closed")
    fp.seek(info.header_offset)
    header = fp.read(30)
    sig, ver, flag, comp, modt, modd, crc, cs, us, fnl, exl = struct.unpack("<IHHHHHIIIHH", header)
    return info.header_offset + 30 + fnl + exl


def check_apk(path: Path) -> list[str]:
    issues: list[str] = []
    with zipfile.ZipFile(path) as zf:
        for name in ("resources.arsc", "classes.dex", "AndroidManifest.xml"):
            try:
                info = zf.getinfo(name)
            except KeyError:
                issues.append(f"missing {name}")
                continue
            if name == "resources.arsc" and info.compress_type != zipfile.ZIP_STORED:
                issues.append("resources.arsc is compressed")
            offset = _data_offset(zf, info)
            if name in {"resources.arsc", "classes.dex"} and offset % 4 != 0:
                issues.append(f"{name} offset {offset} is not 4-byte aligned")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("apk", type=Path)
    args = parser.parse_args()
    issues = check_apk(args.apk)
    if issues:
        for item in issues:
            print(item)
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
