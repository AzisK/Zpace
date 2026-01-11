#!/usr/bin/env python
import time
from zpace.main import main

if __name__ == "__main__":
    start = time.time()
    main()
    elapsed = time.time() - start
    print(f"Scan completed in {elapsed:.2f}s")
