import { DOCUMENT } from '@angular/common';
import { Injectable, effect, inject, signal } from '@angular/core';
import { Title } from '@angular/platform-browser';

import { ApiService, ContentPage, Site } from './api.service';
import meta from './meta.json';
import { FALLBACK_SITE } from './site.fallback';
import { applyTheme } from './theme';

const CACHE_KEY = `${meta.slug}.site`;

/** The site manifest from GET /site, cached on the device so the app opens offline. */
@Injectable({ providedIn: 'root' })
export class SiteStore {
  private readonly api = inject(ApiService);
  private readonly document = inject(DOCUMENT);
  private readonly title = inject(Title);

  readonly site = signal<Site>(readCache() ?? FALLBACK_SITE);
  /** Set by each page; the document title reads "{page} · {brand}", as on the web UI. */
  readonly pageTitle = signal<string | null>(null);

  constructor() {
    effect(() => applyTheme(this.site().theme, this.document.documentElement));
    effect(() => {
      const name = this.site().brand.name ?? meta.name; // the API fills it; the type allows null
      const page = this.pageTitle();
      this.title.setTitle(page ? `${page} · ${name}` : name);
    });
  }

  load(): void {
    this.api.site().subscribe({
      next: (site) => {
        this.site.set(site);
        writeCache(site);
      },
      error: () => undefined, // keep the cached or fallback manifest
    });
  }

  /** welcome, about, or one of the sidebar pages. */
  page(slug: string): ContentPage | undefined {
    const site = this.site();
    if (slug === 'welcome') return site.welcome;
    if (slug === 'about') return site.about;
    return site.pages.find((p) => p.slug === slug);
  }
}

function readCache(): Site | null {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    return raw ? (JSON.parse(raw) as Site) : null;
  } catch {
    return null;
  }
}

function writeCache(site: Site): void {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify(site));
  } catch {
    // storage full or blocked: the app still works from the network
  }
}
