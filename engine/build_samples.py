#!/usr/bin/env python3
"""一键编译 samples/ 下所有示例，并同步打包成 Chrome 插件内置示例库 extension/samples_bundle.js。"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))
import apple_modules  # noqa: E402


def main():
    samples_dir = ROOT / "samples"
    bundle = []

    for sub in sorted(samples_dir.iterdir()):
        spec_path = sub / "modules.json"
        if not sub.is_dir() or not spec_path.exists():
            continue
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        out_dir = sub / "dist"
        pack = apple_modules.build_pack(spec, out_dir, base_dir=sub)
        pack["sampleKey"] = sub.name
        bundle.append(pack)
        art_kb = pack["articleBytes"] / 1024
        ok_all = pack["articleLint"]["ok"] and all(m["lint"]["ok"] for m in pack["modules"])
        print(f"✅ {sub.name}: {pack['title']} ({art_kb:.1f}KB · {len(pack['modules'])} 模块 · 合规={'OK' if ok_all else 'WARN'})")

    bundle_js = (
        "// 自动生成：由 python3 engine/build_samples.py 同步，勿手动编辑\n"
        "window.FEIS_BUILTIN_SAMPLES = "
        + json.dumps(bundle, ensure_ascii=False, indent=2)
        + ";\n"
    )
    out_js = ROOT / "extension" / "samples_bundle.js"
    out_js.write_text(bundle_js, encoding="utf-8")
    print(f"📦 已写入插件内置示例库 → {out_js.relative_to(ROOT)} ({len(bundle_js.encode())/1024:.1f}KB)")


if __name__ == "__main__":
    main()
