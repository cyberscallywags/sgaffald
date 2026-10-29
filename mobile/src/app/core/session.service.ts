import { Injectable, InjectionToken, computed, inject, signal } from '@angular/core';
import { Observable, map, tap } from 'rxjs';

import { ApiService, Member, Session } from './api.service';
import meta from './meta.json';

/**
 * Where the session is kept. localStorage for now; a native build can provide
 * `@capacitor/preferences` or a secure-storage plugin here without touching any caller.
 */
export interface SessionStore {
  read(): Session | null;
  write(session: Session): void;
  clear(): void;
}

const KEY = `${meta.slug}.session`;

export const SESSION_STORE = new InjectionToken<SessionStore>('SESSION_STORE', {
  providedIn: 'root',
  factory: (): SessionStore => ({
    read: () => {
      try {
        const raw = localStorage.getItem(KEY);
        return raw ? (JSON.parse(raw) as Session) : null;
      } catch {
        return null;
      }
    },
    write: (session) => {
      try {
        localStorage.setItem(KEY, JSON.stringify(session));
      } catch {
        // not persisted; the session lasts until reload
      }
    },
    clear: () => {
      try {
        localStorage.removeItem(KEY);
      } catch {
        // nothing stored
      }
    },
  }),
});

/**
 * Mock sign-on (see the handbook's Sign-on page): POST /auth/login returns a token that
 * authInterceptor sends with every API call. A real identity provider would replace signIn
 * with its own flow and keep the same signals.
 */
@Injectable({ providedIn: 'root' })
export class SessionService {
  private readonly api = inject(ApiService);
  private readonly store = inject(SESSION_STORE);

  readonly session = signal<Session | null>(unexpired(this.store.read()));
  readonly member = computed<Member | null>(() => this.current()?.member ?? null);
  readonly token = computed<string | null>(() => this.current()?.token ?? null);

  signIn(email: string, password: string): Observable<Member> {
    return this.api.login(email, password).pipe(
      tap((session) => {
        this.session.set(session);
        this.store.write(session);
      }),
      map((session) => session.member),
    );
  }

  signOut(): void {
    this.session.set(null);
    this.store.clear();
  }

  /** The session, unless its token has expired: an expired session reads as signed out. */
  private current(): Session | null {
    return unexpired(this.session());
  }
}

function unexpired(session: Session | null): Session | null {
  return session && Date.parse(session.expires_at) > Date.now() ? session : null;
}
