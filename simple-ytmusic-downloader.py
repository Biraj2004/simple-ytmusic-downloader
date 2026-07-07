import sys
from pathlib import Path

# Add the 'src' directory to Python's module search path
src_dir = Path(__file__).resolve().parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Import and run the main GUI application
from main import main

if __name__ == "__main__":
    main()
