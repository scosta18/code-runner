from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import tempfile
import os

app = FastAPI(title="Code Runner", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

LANGUAGE_CONFIG = {
    "python": {
        "image": "python:3.12-slim",
        "filename": "solution.py",
        "cmd": ["python", "solution.py"],
    },
    "javascript": {
        "image": "node:20-slim",
        "filename": "solution.js",
        "cmd": ["node", "solution.js"],
    },
    "java": {
        "image": "openjdk:17-slim",
        "filename": "Solution.java",
        "cmd": ["sh", "-c", "javac Solution.java && java Solution"],
    },
    "cpp": {
        "image": "gcc:12",
        "filename": "solution.cpp",
        "cmd": ["sh", "-c", "g++ -o solution solution.cpp && ./solution"],
    },
}


class ExecuteRequest(BaseModel):
    code: str
    language: str = "python"
    stdin: str = ""


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/execute")
def execute(request: ExecuteRequest):
    cfg = LANGUAGE_CONFIG.get(request.language.lower())
    if not cfg:
        return {"success": False, "error": f"Unsupported language: {request.language}"}

    # Write code to a temp file
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, cfg["filename"])
        with open(filepath, "w") as f:
            f.write(request.code)

        try:
            result = subprocess.run(
                [
                    "docker", "run", "--rm",
                    "--memory=128m",
                    "--cpus=0.5",
                    "--network=none",
                    "-v", f"{tmpdir}:/code",
                    "-w", "/code",
                    cfg["image"],
                ] + cfg["cmd"],
                capture_output=True,
                text=True,
                timeout=15,
                input=request.stdin or None,
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "output": result.stdout + result.stderr,
                "exit_code": result.returncode,
            }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Execution timed out (15s limit)"}
        except Exception as e:
            return {"success": False, "error": str(e)}