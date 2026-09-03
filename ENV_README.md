# Environment configuration

Copy `.env.example` to `.env` for local configuration. Never commit `.env`
or place Hugging Face tokens in it. Authenticate separately with:

```bash
source venv/bin/activate
hf auth login
```

## Application variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_NAME` | `BHASHA SETU` | Application name used by settings. |
| `ENVIRONMENT` | `development` | Runtime label such as `development` or `production`. |
| `ALLOWED_ORIGINS` | `[*]` | JSON list of browser origins allowed by CORS. |
| `TESTING` | unset/`false` | Set to `true` to use the test SQLite database. |

## Model variables

| Variable | Default | Options |
| --- | --- | --- |
| `BHASHA_MODEL_BACKEND` | `indictrans2` | `indictrans2` for the primary model; `backup` only for experimental loading/error tests. |
| `BHASHA_MODEL_NAME` | `ai4bharat/indictrans2-indic-indic-dist-320M` | Hugging Face repository for the primary IndicTrans2 model. |
| `BHASHA_BACKUP_MODEL_NAME` | `google/madlad400-3b-mt` | Hugging Face repository for the public MADLAD fallback. |

The primary model is gated and requires approval for the logged-in Hugging
Face account. Model weights are downloaded lazily on first use and cached in
`~/.cache/huggingface/hub/`.

The backup is the public Google MADLAD-400 model. It uses the `<2sat>` target
tag for Santali and does not require gated access. It is a 3B-parameter model,
so the first download is large and CPU inference may be slow on a laptop.

## Examples

Use the primary model:

```bash
source venv/bin/activate
python -m uvicorn main:app --reload
```

Use the experimental backup:

```bash
BHASHA_MODEL_BACKEND=backup python -m uvicorn main:app --reload
```

Shell variables override `.env` values. Restart the server after changing
model variables because the model backend is selected when the process starts.

The web translator can override this default per request with its model
dropdown. API clients can do the same by sending `model_backend` as either
`indictrans2` or `backup` in `POST /api/translate`.