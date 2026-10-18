#!/usr/bin/env python3
"""Wait for a run's result in one call, instead of sleeping and reading the log again and again.

Watches a text file (a driver's result file, the Unity log, etc.) and returns on whichever comes first:
the end mark, an error line, no progress mark for longer than --stall seconds, or --timeout seconds.
Prints a short summary: why it returned, the line that decided it, and the counts; the full text stays in
the file. Exit codes: 0 end mark, 2 error line, 3 stalled, 4 timeout, 5 the file never appeared.

  python wait_for.py <file> --end "<regex>" [--error "<regex>"] [--progress "<regex>"] [--tag "<text>"]
                     [--stall <seconds>] [--timeout <seconds>] [--from-start] [--show <lines>]

Give the tool call that runs it a time limit above --timeout. By default only lines written after the
start count (--from-start reads the whole file), so marks from an earlier round don't end the wait.
"""
import argparse
import os
import re
import sys
import time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--end", required=True, help="regex of the end mark")
    ap.add_argument("--error", default=r"Exception|\berror CS\d+|\bError\b", help="regex of a line that ends the wait as an error")
    ap.add_argument("--progress", default=None, help="regex of a progress mark; with --stall, no new one ends the wait")
    ap.add_argument("--tag", default=None, help="only lines containing this text count and are shown (e.g. [TMP-task])")
    ap.add_argument("--stall", type=float, default=None, help="seconds without a progress mark that count as stalled")
    ap.add_argument("--timeout", type=float, required=True, help="seconds to wait at most")
    ap.add_argument("--from-start", action="store_true", help="read the file from its start, not from its current end")
    ap.add_argument("--show", type=int, default=5, help="last tag lines to print with the summary")
    a = ap.parse_args()

    end, err = re.compile(a.end), re.compile(a.error) if a.error else None
    prog = re.compile(a.progress) if a.progress else None
    t0 = last_progress = time.time()
    pos = None
    tagged, errors, kept = 0, 0, []
    buf = ""

    def finish(code, why, line=""):
        print(f"{why}{': ' + line.strip()[:300] if line else ''}")
        print(f"tag lines: {tagged}, error lines: {errors}, waited: {time.time() - t0:.0f}s, file: {a.file}")
        for k in kept[-a.show:]:
            print("  " + k.strip()[:300])
        sys.exit(code)

    while True:
        now = time.time()
        if os.path.exists(a.file):
            size = os.path.getsize(a.file)
            if pos is None:
                pos = 0 if a.from_start else size
            if size < pos:  # the file was rewritten: read it again from the start
                pos = 0
            if size > pos:
                with open(a.file, "rb") as fh:
                    fh.seek(pos)
                    chunk = fh.read(size - pos)
                pos = size
                buf += chunk.decode("utf-8", errors="replace")
                *lines, buf = buf.split("\n")
                for line in lines:
                    if a.tag and a.tag not in line and not end.search(line):
                        continue
                    tagged += 1
                    kept.append(line)
                    if prog and prog.search(line):
                        last_progress = now
                    if end.search(line):
                        finish(0, "END", line)
                    if err and err.search(line):
                        errors += 1
                        finish(2, "ERROR", line)
        if a.stall is not None and prog and now - last_progress > a.stall:
            finish(3, f"STALLED: no progress mark for {a.stall:.0f}s", kept[-1] if kept else "")
        if now - t0 > a.timeout:
            finish(4 if os.path.exists(a.file) else 5, "TIMEOUT" if os.path.exists(a.file) else "NO FILE")
        time.sleep(0.5)


if __name__ == "__main__":
    main()
