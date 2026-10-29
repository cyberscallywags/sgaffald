import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';

/** Mirrors app.models: keep in step with the Pydantic contract. */
export interface Item {
  id: string;
  name: string;
  created_at: string;
}

export interface Health {
  status: string;
  env: string;
  neo4j: boolean;
}

export interface Theme {
  primary: string;
  secondary: string;
  tertiary: string;
  font_family: string;
}

export interface Brand {
  name: string;
  tagline: string;
  collective: string;
  collective_url: string | null;
}

export interface SectionItem {
  title: string;
  body?: string | null;
  icon?: string | null;
  url?: string | null;
}

export interface Section {
  kind: 'text' | 'list' | 'steps' | 'cards';
  heading?: string | null;
  body?: string | null;
  items: SectionItem[];
}

export interface ContentPage {
  slug: string;
  title: string;
  icon: string;
  summary?: string | null;
  sections: Section[];
}

/** GET /site: brand, theme and pages, shared with the FastUI frontend. */
export interface Site {
  brand: Brand;
  theme: Theme;
  welcome: ContentPage;
  about: ContentPage;
  pages: ContentPage[];
  /** Docs portal URL from the API's DOCS_URL setting; null hides the menu link. */
  docs_url?: string | null;
}

/** The app's only way to reach data: HTTP to the API, never Neo4j. */
@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiUrl;

  health(): Observable<Health> {
    return this.http.get<Health>(`${this.base}/health`);
  }

  site(): Observable<Site> {
    return this.http.get<Site>(`${this.base}/site`);
  }

  listItems(limit = 100): Observable<Item[]> {
    return this.http.get<Item[]>(`${this.base}/items`, { params: { limit } });
  }

  createItem(name: string): Observable<Item> {
    return this.http.post<Item>(`${this.base}/items`, { name });
  }
}
