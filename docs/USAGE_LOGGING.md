# Logging

This repo includes a small helper at `utils/logging_config.py`.

Example usage:

```python
from utils.logging_config import configure_logging
configure_logging("logs/photo_fixer.log")
import logging
logging.getLogger(__name__).info("Starting processing")
# ... run processing ...
logging.getLogger(__name__).info("Finished processing: %d files processed", count)
```

The helper creates the logs directory, uses a rotating file handler, and prints to console as well.
