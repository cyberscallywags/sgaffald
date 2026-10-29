"""Add an entity to every layer: its models, storage and routes (src/app/domain/<plural>.py),
its tests, a mobile page with its route and menu entry, and the mobile app's types. The web
UI gives it a page and the docs list its models without further code.

    uv run task new_entity Volunteer              # plural: Volunteers, path /volunteers
    uv run task new_entity Opportunity --plural Opportunities

The entity starts with one field, `name`, like the sample Item: add your fields to its
`<Name>In` model, then run `uv run task types`. Run it with `uv run`: it regenerates the types
with the project's own Python.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTES = Path("mobile/src/app/app.routes.ts")
FEATURES = Path("mobile/src/app/features.ts")

MODULE = '''"""{Plural}: added by `uv run task new_entity {Name}`. Yours to edit: the models,
the storage and the routes. The API includes `router`, the web UI shows a page at `PATH`, and
the docs and the mobile app's types include the models."""

from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from neo4j import AsyncDriver
from pydantic import BaseModel, Field

from app.api.auth import CurrentMember
from app.config import get_settings

TITLE = "{Plural}"
PATH = "/{path}"


class {Name}In(BaseModel):
    """What a client sends to add a {lower}."""

    name: str = Field(min_length=1, max_length=200)


class {Name}({Name}In):
    """A stored {lower}, as the API returns it."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_by: str | None = Field(None, description="`id` of the member who added it.")


MODEL, MODEL_IN = {Name}, {Name}In
MEMORY: list[{Name}] = []  # STORAGE=memory: this process's {plural_lower}, newest first


class {Name}Repo:
    """{Plural} in Neo4j, or in MEMORY when the API has no driver (STORAGE=memory)."""

    def __init__(self, driver: AsyncDriver | None, database: str) -> None:
        self.driver = driver
        self.database = database

    async def create(self, data: {Name}In, created_by: str) -> {Name}:
        row = {Name}(**data.model_dump(), created_by=created_by)
        if self.driver is None:
            MEMORY.insert(0, row)
        else:
            await self.driver.execute_query(
                "CREATE (n:{Name} $props)", props=row.model_dump(), database_=self.database
            )
        return row

    async def list(self, limit: int) -> list[{Name}]:
        if self.driver is None:
            return MEMORY[:limit]
        records, _, _ = await self.driver.execute_query(
            "MATCH (n:{Name}) RETURN n ORDER BY n.created_at DESC LIMIT $limit",
            limit=limit,
            database_=self.database,
        )
        return [
            {Name}(**{{**r["n"], "created_at": r["n"]["created_at"].to_native()}}) for r in records
        ]


def get_repo(request: Request) -> {Name}Repo:
    driver = getattr(request.app.state, "driver", None)
    return {Name}Repo(driver, get_settings().neo4j_database)


Repo = Annotated[{Name}Repo, Depends(get_repo)]
router = APIRouter(prefix=PATH, tags=["{plural_lower}"])


@router.get("", response_model=list[{Name}])
async def list_{snake_plural}(repo: Repo, limit: int = 100) -> list[{Name}]:
    """The most recent {plural_lower} first, at most `limit` of them."""
    return await repo.list(limit)


@router.post("", response_model={Name}, status_code=201)
async def add_{snake}(data: {Name}In, repo: Repo, member: CurrentMember) -> {Name}:
    """Add a {lower} for the signed-in member. Needs a bearer token unless sign-on is off."""
    return await repo.create(data, created_by=member.id)
'''

TESTS = '''"""{Plural} (added by `uv run task new_entity {Name}`): the API and the web UI page."""

import httpx
import pytest

from app.api.auth import demo_members
from app.api.main import app
from app.config import get_settings
from app.domain import {snake_plural} as entity
from app.ui import main as ui


@pytest.fixture
async def client(mock_sign_on):
    entity.MEMORY.clear()  # no lifespan here, so no driver: the module stores in memory
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://api") as c:
        yield c


async def sign_in(client) -> str:
    member = demo_members()[0]
    password = get_settings().auth_demo_password.get_secret_value()
    r = await client.post("/auth/login", json={{"email": member.email, "password": password}})
    return r.json()["token"]


async def test_add_then_list(client):
    token = await sign_in(client)
    headers = {{"Authorization": f"Bearer {{token}}"}}
    r = await client.post(entity.PATH, json={{"name": "Ada"}}, headers=headers)
    assert r.status_code == 201
    assert r.json()["created_by"] == demo_members()[0].id
    assert [row["name"] for row in (await client.get(entity.PATH)).json()] == ["Ada"]


async def test_adding_needs_a_member(client):
    assert (await client.post(entity.PATH, json={{"name": "Ada"}})).status_code == 401


async def test_the_web_ui_lists_them(client, monkeypatch):
    monkeypatch.setattr(
        ui,
        "api",
        lambda token=None: httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://api"
        ),
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=ui.app), base_url="http://ui"
    ) as web:
        r = await web.get(f"/api{{entity.PATH}}")
    assert r.status_code == 200
    assert entity.TITLE in r.text
'''

PAGE_TS = """import {{ DatePipe }} from '@angular/common';
import {{ Component, OnInit, computed, inject, signal }} from '@angular/core';
import {{ FormControl, FormGroup, ReactiveFormsModule, Validators }} from '@angular/forms';
import {{ RouterLink }} from '@angular/router';
import {{
  IonButton,
  IonButtons,
  IonContent,
  IonHeader,
  IonInput,
  IonItem,
  IonLabel,
  IonList,
  IonMenuButton,
  IonNote,
  IonRouterLink,
  IonText,
  IonTitle,
  IonToolbar,
}} from '@ionic/angular';

import {{ ApiService, {Name} }} from '../../core/api.service';
import {{ SessionService }} from '../../core/session.service';
import {{ SiteStore }} from '../../core/site.store';
import {{ AccountMenuComponent }} from '../../shared/account-menu.component';

/** {Plural}: added by `uv run task new_entity {Name}`. Yours to edit. */
@Component({{
  selector: 'app-{kebab_plural}',
  templateUrl: '{kebab_plural}.page.html',
  imports: [
    AccountMenuComponent,
    DatePipe,
    ReactiveFormsModule,
    RouterLink,
    IonButton,
    IonButtons,
    IonContent,
    IonHeader,
    IonInput,
    IonItem,
    IonLabel,
    IonList,
    IonMenuButton,
    IonNote,
    IonRouterLink,
    IonText,
    IonTitle,
    IonToolbar,
  ],
}})
export class {Plural}Page implements OnInit {{
  private readonly api = inject(ApiService);
  private readonly store = inject(SiteStore);
  private readonly session = inject(SessionService);

  readonly rows = signal<{Name}[]>([]);
  readonly error = signal<string | null>(null);
  readonly canAdd = computed(
    () => this.store.site().auth?.mode !== 'mock' || this.session.member() !== null,
  );
  readonly name = new FormControl('', {{
    nonNullable: true,
    validators: [Validators.required, Validators.maxLength(200)],
  }});
  readonly form = new FormGroup({{ name: this.name }});

  ngOnInit(): void {{
    this.store.pageTitle.set('{Plural}');
    this.api.list<{Name}>('/{path}').subscribe({{
      next: (rows) => this.rows.set(rows),
      error: () => this.error.set('API unreachable'),
    }});
  }}

  add(): void {{
    const name = this.name.value.trim();
    if (!name || this.name.invalid) {{
      this.name.markAsTouched();
      return;
    }}
    this.api.create<{Name}>('/{path}', {{ name }}).subscribe({{
      next: (row) => {{
        this.rows.update((rows) => [row, ...rows]);
        this.name.reset();
      }},
      error: (err) => this.error.set(err.status ? `API error ${{err.status}}` : 'API unreachable'),
    }});
  }}
}}
"""

PAGE_HTML = """<ion-header [translucent]="true">
  <ion-toolbar color="primary">
    <ion-buttons slot="start">
      <ion-menu-button></ion-menu-button>
    </ion-buttons>
    <ion-title>{Plural}</ion-title>
    <ion-buttons slot="end">
      <app-account-menu></app-account-menu>
    </ion-buttons>
  </ion-toolbar>
</ion-header>

<ion-content [fullscreen]="true">
  @if (canAdd()) {{
    <form [formGroup]="form" (ngSubmit)="add()">
      <ion-list inset>
        <ion-item>
          <ion-input
            label="Name"
            labelPlacement="stacked"
            [formControl]="name"
            errorText="Name is required"
          ></ion-input>
        </ion-item>
      </ion-list>
      <div class="ion-padding-horizontal">
        <ion-button type="submit" expand="block">Add</ion-button>
      </div>
    </form>
  }} @else {{
    <div class="ion-padding-horizontal">
      <ion-button
        routerLink="/sign-in"
        [queryParams]="{{ returnUrl: '/{path}' }}"
        expand="block"
        fill="outline"
      >
        Sign in to add one
      </ion-button>
    </div>
  }}

  @if (error(); as message) {{
    <ion-text color="danger" role="alert">
      <p class="ion-padding-horizontal">{{{{ message }}}}</p>
    </ion-text>
  }}

  <ion-list inset data-testid="{kebab_plural}">
    @for (row of rows(); track row.id) {{
      <ion-item>
        <ion-label>{{{{ row.name }}}}</ion-label>
        <ion-note slot="end">{{{{ row.created_at | date: 'short' }}}}</ion-note>
      </ion-item>
    }} @empty {{
      <ion-item>
        <ion-label color="medium">No {plural_lower} yet</ion-label>
      </ion-item>
    }}
  </ion-list>
</ion-content>
"""

ROUTE = """  {{
    path: '{path}',
    loadComponent: () =>
      import('./pages/{kebab_plural}/{kebab_plural}.page').then((m) => m.{Plural}Page),
  }},
"""
FEATURE = "  {{ title: '{Plural}', path: '/{path}', icon: 'list-outline' }},\n"


def words(name: str) -> list[str]:
    return re.findall(r"[A-Z][a-z0-9]*", name)


def names(name: str, plural: str | None) -> dict[str, str]:
    plural = plural or (name[:-1] + "ies" if name.endswith("y") else name + "s")
    snake = "_".join(w.lower() for w in words(name))
    snake_plural = "_".join(w.lower() for w in words(plural))
    return {
        "Name": name,
        "Plural": plural,
        "lower": " ".join(w.lower() for w in words(name)),
        "plural_lower": " ".join(w.lower() for w in words(plural)),
        "snake": snake,
        "snake_plural": snake_plural,
        "kebab_plural": snake_plural.replace("_", "-"),
        "path": snake_plural.replace("_", "-"),
    }


def insert_before(path: Path, marker: str, text: str) -> None:
    source = path.read_text()
    if marker not in source:
        raise SystemExit(f"{path}: the '{marker}' marker is missing; add the entry by hand")
    index = source.index(marker)
    line_start = source.rindex("\n", 0, index) + 1
    path.write_text(source[:line_start] + text + source[line_start:])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("name", help="singular, in PascalCase, e.g. Volunteer")
    parser.add_argument("--plural", help="default: the name + s (or -y → -ies)")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    if not re.fullmatch(r"(?:[A-Z][a-z0-9]*)+", args.name):
        parser.error(f"{args.name!r}: PascalCase, e.g. Volunteer or VolunteerRole")
    n = names(args.name, args.plural)
    root = args.root
    files = {
        Path(f"src/app/domain/{n['snake_plural']}.py"): MODULE.format(**n),
        Path(f"tests/unit/test_{n['snake_plural']}.py"): TESTS.format(**n),
        Path(f"mobile/src/app/pages/{n['kebab_plural']}/{n['kebab_plural']}.page.ts"): (
            PAGE_TS.format(**n)
        ),
        Path(f"mobile/src/app/pages/{n['kebab_plural']}/{n['kebab_plural']}.page.html"): (
            PAGE_HTML.format(**n)
        ),
    }
    if clash := [str(p) for p in files if (root / p).exists()]:
        print(f"already there, nothing written: {', '.join(clash)}", file=sys.stderr)
        return 1
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text)
        print(f"wrote {rel}")
    insert_before(root / ROUTES, "// new_entity: routes", ROUTE.format(**n))
    insert_before(root / FEATURES, "// new_entity: features", FEATURE.format(**n))
    print(f"added {n['Plural']} to {ROUTES} and {FEATURES}")
    subprocess.run([sys.executable, "-m", "app.typegen", "--root", str(root)], cwd=root, check=True)  # noqa: S603
    print(
        f"\nNext: add fields to {n['Name']}In in src/app/domain/{n['snake_plural']}.py, run "
        "`uv run task types`, and `uv run task test` and `uv run task test_mobile`."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
