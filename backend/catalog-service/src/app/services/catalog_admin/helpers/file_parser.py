import csv
import io
import json
import os


class NeighborhoodFileParser:
    def parse(self, *, file: bytes, filename: str) -> list[dict]:
        _, ext = os.path.splitext(filename.lower())
        if ext == ".csv":
            return self._parse_csv(file)
        if ext in (".json", ".txt"):
            return self._parse_json(file)
        raise ValueError(f"Unsupported file extension: {ext}")

    def _parse_csv(self, file: bytes) -> list[dict]:
        reader = csv.DictReader(io.StringIO(file.decode("utf-8")))
        return [row for row in reader]

    def _parse_json(self, file: bytes) -> list[dict]:
        return json.loads(file.decode("utf-8"))
