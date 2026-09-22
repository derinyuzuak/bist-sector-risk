"""Execute walkthroughs using this Python interpreter, without global kernel install."""
from pathlib import Path
import tempfile
import json
import os
import sys
import nbformat
from nbclient import NotebookClient

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix="bist-kernel-") as tmp:
    kernel_dir = Path(tmp)/"kernels"/"bist-local"
    kernel_dir.mkdir(parents=True)
    (kernel_dir/"kernel.json").write_text(json.dumps({"argv":[sys.executable,"-m","ipykernel_launcher","-f","{connection_file}"],"display_name":"BIST local Python","language":"python"}), encoding="utf-8")
    os.environ["JUPYTER_PATH"] = tmp + os.pathsep + os.environ.get("JUPYTER_PATH", "")
    os.environ["IPYTHONDIR"] = str(Path(tmp)/"ipython")
    os.environ["JUPYTER_RUNTIME_DIR"] = str(Path(tmp)/"runtime")
    for path in sorted((root/"notebooks").glob("*.ipynb")):
        nb = nbformat.read(path, as_version=4)
        NotebookClient(nb, timeout=180, kernel_name="bist-local", resources={"metadata":{"path":str(root)}}).execute()
        nbformat.write(nb, path)
        print(f"Executed {path.name}")
