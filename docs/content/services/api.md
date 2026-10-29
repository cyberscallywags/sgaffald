# API

`src/app/api/main.py`: FastAPI, the only service that writes to the graph (besides
admin). Its endpoint docstrings become the OpenAPI descriptions, which feed both the live
Swagger UI at <http://localhost:8000/docs> and the [HTTP API](../reference/http-api.md)
reference.

| Endpoint | Purpose |
|---|---|
| `GET /health` | Liveness and Neo4j reachability; `degraded` when the graph is down |
| `GET /site` | The [site manifest](../site-manifest.md) for the web and mobile frontends |
| `GET /items`, `POST /items` | The example domain: items stored in Neo4j |
| `POST /ask` | A Pydantic AI agent that can read items from the graph |

## Graph access

`app.db.ItemRepo` wraps the async Neo4j driver. On start-up the API pings Neo4j and
creates a uniqueness constraint on `Item.id`. Swap `ItemRepo` and the `Item` models for
your own domain; the unit tests use an in-memory `FakeRepo` with the same methods.

## The agent

`app.agent.build_agent` builds a Pydantic AI agent with one tool, `list_item_names`.
`LLM_MODEL=test` selects the offline `TestModel`, which calls every tool and echoes the
results, so tests need no API key. For a real model see [Configuration](../reference/configuration.md).

## CORS

The web UI and the mobile web image reach the API server-side, so they need no CORS. A
native Capacitor build calls it directly from `capacitor://localhost`; list such origins in
`CORS_ORIGINS`.
