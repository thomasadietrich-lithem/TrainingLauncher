"""Point d'entrée gelé par PyInstaller (NeuroVision.exe). Voir nvs_lanceur/__main__.py."""
import sys

from nvs_lanceur.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
