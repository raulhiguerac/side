import sys
from pathlib import Path

# Add src to path.
# Without this, unit tests only import `app` when the integration conftest
# happens to be collected first ("integration" sorts before "unit"), so running
# a single unit test file on its own would fail.
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))
