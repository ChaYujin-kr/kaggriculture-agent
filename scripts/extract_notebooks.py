"""Extract %%writefile cells (agent code) and a markdown digest from downloaded Kaggle notebooks.

usage: python scripts/extract_notebooks.py research/notebooks research/extracted
For each notebook NAME: research/extracted/NAME/<files written by %%writefile>, plus digest.md
(markdown cells + code-cell sizes) for quick reading.
"""
import glob
import json
import os
import sys

src, dst = sys.argv[1], sys.argv[2]
for nb_path in glob.glob(os.path.join(src, "*", "*.ipynb")):
    name = os.path.basename(os.path.dirname(nb_path))
    out = os.path.join(dst, name)
    os.makedirs(out, exist_ok=True)
    nb = json.load(open(nb_path, encoding="utf-8"))
    digest, written = [], []
    for i, cell in enumerate(nb.get("cells", [])):
        text = "".join(cell.get("source", []))
        if cell.get("cell_type") == "markdown":
            digest.append(text)
            continue
        first = text.split("\n", 1)[0].strip()
        if first.startswith("%%writefile"):
            fn = first.split()[-1]
            body = text.split("\n", 1)[1] if "\n" in text else ""
            path = os.path.join(out, os.path.basename(fn))
            mode = "a" if "-a" in first.split() else "w"
            with open(path, mode, encoding="utf-8") as f:
                f.write(body)
            written.append(os.path.basename(fn))
            digest.append(f"[code cell {i}: %%writefile {fn}, {len(body.splitlines())} lines]")
        else:
            digest.append(f"[code cell {i}: {len(text.splitlines())} lines]\n```\n{text[:1500]}\n```")
    with open(os.path.join(out, "digest.md"), "w", encoding="utf-8") as f:
        f.write("\n\n".join(digest))
    print(f"{name}: writefile -> {sorted(set(written)) or 'none'}")
