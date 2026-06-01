import csv
import io
import os


class PropertyFileParser:
    def parse(self, *, file: bytes, filename: str) -> list[dict]:
        _, ext = os.path.splitext(filename.lower())
        if ext == ".csv":
            return self._parse_csv(file)
        raise ValueError(f"Unsupported file extension: {ext}")

    def _parse_csv(self, file: bytes) -> list[dict]:
        reader = csv.DictReader(io.StringIO(file.decode("utf-8")))
        return [row for row in reader]
