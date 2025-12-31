import pandas as pd
from pathlib import Path
from typing import Sequence, Optional
import csv


def read_csv_flexible(path: Path | str, encodings: Optional[Sequence[str]] = None, **kwargs) -> pd.DataFrame:
	"""Read a CSV trying a list of encodings and falling back to replace invalid bytes.

	Tries the encodings in order (default: utf-8, latin-1, cp1252). If all attempts
	fail with a UnicodeDecodeError, opens the file with `errors='replace'` and
	reads it as UTF-8 so that problematic bytes are replaced instead of failing.
	Other exceptions (e.g., parsing errors) are propagated.
	"""
	if encodings is None:
		encodings = ("utf-8", "latin-1", "cp1252")

	last_exc: Optional[Exception] = None
	for enc in encodings:
		try:
			# first attempt: default parser with this encoding
			return pd.read_csv(path, encoding=enc, **kwargs)
		except UnicodeDecodeError as e:
			last_exc = e
			continue
		except pd.errors.ParserError:
			# try to sniff delimiter from a small sample, then retry
			try:
				with open(path, "r", encoding=enc, errors="replace") as fh:
					sample = fh.read(4096)
				sniffer = csv.Sniffer()
				dialect = sniffer.sniff(sample)
				delim = dialect.delimiter
				return pd.read_csv(path, encoding=enc, sep=delim, engine="python", **kwargs)
			except Exception:
				# try common separators as fallbacks
				for sep in [",", ";", "\t", "|"]:
					try:
						return pd.read_csv(path, encoding=enc, sep=sep, engine="python", **kwargs)
					except Exception as e2:
						last_exc = e2
				# move to next encoding
				continue
		except Exception:
			# other errors likely indicate real issues; re-raise
			raise

	# Last resort: open with replacement of invalid bytes and use python engine
	with open(path, "r", encoding="utf-8", errors="replace") as fh:
		return pd.read_csv(fh, engine="python", sep=None, **kwargs)
