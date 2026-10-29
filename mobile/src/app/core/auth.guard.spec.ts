import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, RouterStateSnapshot, UrlTree, provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { SITE, session } from '../testing/site.fixture';
import { ApiService } from './api.service';
import { authGuard } from './auth.guard';
import meta from './meta.json';
import { SiteStore } from './site.store';

function run(signedIn: boolean, mode: 'mock' | 'off' = 'mock') {
  localStorage.clear();
  if (signedIn) localStorage.setItem(`${meta.slug}.session`, JSON.stringify(session()));
  TestBed.configureTestingModule({
    providers: [provideRouter([]), { provide: ApiService, useValue: { site: () => of(SITE) } }],
  });
  TestBed.inject(SiteStore).site.set({ ...SITE, auth: { mode, demo_users: [] } });
  return TestBed.runInInjectionContext(() =>
    authGuard({} as ActivatedRouteSnapshot, { url: '/account' } as RouterStateSnapshot),
  );
}

describe('authGuard', () => {
  it('lets a member through', () => {
    expect(run(true)).toBe(true);
  });

  it('sends anyone else to sign-in, coming back afterwards', () => {
    const result = run(false) as UrlTree;
    expect(result.toString()).toBe('/sign-in?returnUrl=%2Faccount');
  });

  it('lets everyone through when sign-on is off', () => {
    expect(run(false, 'off')).toBe(true);
  });
});
