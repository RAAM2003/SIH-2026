Raw downloads belong under each language's `raw/` directory. Cleaning and
validation must produce separate files under `cleaned/` and `validated/`.

Run the downloader from the application directory after installing the
requirements:

```bash
python ml/gather_datasets.py
```

The script downloads Adi Vaani (Santali and Mundari) when its repository is
available, plus the source-reviewed Hindi-Santali education file from
`coild-aikosh/Education_v2`. A failed or gated download is reported and does
not prevent the other source from being attempted.

Keep source cards, URLs, access conditions, and license details with any
future cleaned or validated release. Do not redistribute CIIL primers or
competition data until their usage terms have been checked.
