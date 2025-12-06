#!/usr/bin/env python3
import csv
import base64
import sys
from pathlib import Path

JS_HEADER = """// comments.js
// Generated from CSV. Mapping: code -> base64-encoded feedback.
// This is obfuscation, not real security.

function decodeBase64(str) {
  try {
    return atob(str);
  } catch (e) {
    console.error("Failed to decode base64 string", e);
    return "";
  }
}

// Encoded feedback: { code: base64(comment) }
const COMMENTS_BY_CODE_ENC = {
"""

JS_FOOTER = """};

window.COMMENTS_BY_CODE = {};

for (const [code, enc] of Object.entries(COMMENTS_BY_CODE_ENC)) {
  window.COMMENTS_BY_CODE[code] = decodeBase64(enc);
}
"""


def generate_comments_js(csv_path: Path, js_path: Path) -> None:
  """Read CSV with columns 'code' and 'comment' and write comments.js."""
  rows = []

  # cp1252 works well for Windows exports with “smart quotes”
  with csv_path.open(newline="", encoding="cp1252") as f:
      reader = csv.DictReader(f)
      if "code" not in reader.fieldnames or "comment" not in reader.fieldnames:
          raise ValueError(
              f"CSV must contain headers 'code' and 'comment'. "
              f"Found: {reader.fieldnames}"
          )

      for row in reader:
          code = (row.get("code") or "").strip()
          comment = (row.get("comment") or "").strip()
          if not code:
              continue  # skip rows without code

          # base64 encode comment (UTF-8)
          enc = base64.b64encode(comment.encode("utf-8")).decode("ascii")
          rows.append((code, enc))

  # Dedupe: if a code appears multiple times, last one wins
  dedup = {}
  for code, enc in rows:
      dedup[code] = enc

  with js_path.open("w", encoding="utf-8") as out:
      out.write(JS_HEADER)

      items = list(dedup.items())
      for i, (code, enc) in enumerate(items):
          comma = "," if i < len(items) - 1 else ""
          out.write(f'  "{code}": "{enc}"{comma}\n')

      out.write(JS_FOOTER)

  print(f"Generated {js_path} from {csv_path} ({len(dedup)} entries).")


if __name__ == "__main__":
  # Usage:
  #   python generate_comments_js.py comments.csv [comments.js]
  if len(sys.argv) < 2:
      print("Usage: python generate_comments_js.py input.csv [output.js]")
      sys.exit(1)

  csv_path = Path(sys.argv[1])
  if len(sys.argv) >= 3:
      js_path = Path(sys.argv[2])
  else:
      js_path = csv_path.with_name("comments.js")

  generate_comments_js(csv_path, js_path)
# python generate_comments_js.py comments.csv