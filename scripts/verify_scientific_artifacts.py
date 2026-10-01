"""Scoped Linux proof for retained scientific input mounts; no provider calls."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--image",default="oncojev:latest");args=parser.parse_args()
    image=subprocess.run(["docker","image","inspect","--format","{{.Id}}",args.image],check=True,capture_output=True,text=True).stdout.strip()
    data=b"sample\tx\ty\na\t1\t2\nb\t2\t4\n";digest=hashlib.sha256(data).hexdigest()
    with tempfile.TemporaryDirectory(prefix="oncojev-artifact-proof-") as temp:
        directory=Path(temp);(directory/digest).write_bytes(data)
        code="""import hashlib,json
from pathlib import Path
p=next(Path('/input/artifacts').iterdir())
assert hashlib.sha256(p.read_bytes()).hexdigest()==p.name
try:
 p.write_bytes(b'changed')
except OSError:
 pass
else:
 raise AssertionError('scientific input was writable')
try:
 Path('/escaped').write_text('changed')
except OSError:
 pass
else:
 raise AssertionError('root filesystem was writable')
print(json.dumps({'byte_sha256':p.name,'read_only_input':True,'read_only_root':True}))
"""
        result=subprocess.run(["docker","run","--rm","--network","none","--read-only","--cap-drop","ALL","--security-opt","no-new-privileges",
            "--tmpfs","/tmp:rw,nosuid,nodev,noexec,size=16m","-v",f"{directory}:/input/artifacts:ro","--entrypoint","python",image,"-c",code],
            check=True,capture_output=True,text=True,timeout=30)
        report=json.loads(result.stdout);assert report["byte_sha256"]==digest
        print(json.dumps({"image":image,"scope":"fixture scientific input mount; not public-software replay or scientific utility",**report}))


if __name__=="__main__":main()
