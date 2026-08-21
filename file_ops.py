async def run(action: str, path: str, content: str = None, encoding: str = "utf-8") -> str:
    """
    File operations: read, write, append, list, delete, exists, mkdir.
    Operates on the local filesystem the agent is running on. Returns a
    plain string result or an "[ERROR] ..." message on failure -- never
    raises, so a bad path can't kill the whole tool call.
    """
    from pathlib import Path as _Path

    action = (action or "").lower().strip()
    if not path:
        return "[ERROR] 'path' is required."
    p = _Path(path).expanduser()

    try:
        if action == "read":
            if not p.exists():
                return f"[ERROR] File not found: {p}"
            if not p.is_file():
                return f"[ERROR] Not a file: {p}"
            text = p.read_text(encoding=encoding, errors="replace")
            MAX_CHARS = 20000
            if len(text) > MAX_CHARS:
                return text[:MAX_CHARS] + f"\n...[truncated, {len(text)} chars total]"
            return text

        elif action == "write":
            if content is None:
                return "[ERROR] 'content' is required for write."
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding=encoding)
            return f"Wrote {len(content)} chars to {p}"

        elif action == "append":
            if content is None:
                return "[ERROR] 'content' is required for append."
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "a", encoding=encoding) as f:
                f.write(content)
            return f"Appended {len(content)} chars to {p}"

        elif action == "list":
            if not p.exists():
                return f"[ERROR] Path not found: {p}"
            if not p.is_dir():
                return f"[ERROR] Not a directory: {p}"
            entries = sorted(p.iterdir(), key=lambda e: (e.is_file(), e.name.lower()))
            if not entries:
                return f"(empty directory: {p})"
            lines = []
            for e in entries:
                kind = "DIR " if e.is_dir() else "FILE"
                size = "" if e.is_dir() else f" ({e.stat().st_size} bytes)"
                lines.append(f"[{kind}] {e.name}{size}")
            return "\n".join(lines)

        elif action == "delete":
            if not p.exists():
                return f"[ERROR] Path not found: {p}"
            if p.is_dir():
                import shutil as _shutil
                _shutil.rmtree(p)
                return f"Deleted directory {p}"
            p.unlink()
            return f"Deleted file {p}"

        elif action == "exists":
            if not p.exists():
                return f"false -- {p} does not exist"
            kind = "directory" if p.is_dir() else "file"
            return f"true -- {p} exists ({kind})"

        elif action == "mkdir":
            p.mkdir(parents=True, exist_ok=True)
            return f"Created directory {p}"

        else:
            return (
                f"[ERROR] Unknown action '{action}'. "
                "Use: read, write, append, list, delete, exists, mkdir."
            )
    except PermissionError as e:
        return f"[ERROR] Permission denied: {e}"
    except OSError as e:
        return f"[ERROR] OS error: {e}"
