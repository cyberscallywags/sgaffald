import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { ADA, session } from '../testing/site.fixture';
import meta from './meta.json';
import { SessionService } from './session.service';

const KEY = `${meta.slug}.session`;

function setup() {
  TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
  return { session: TestBed.inject(SessionService), http: TestBed.inject(HttpTestingController) };
}

describe('SessionService', () => {
  beforeEach(() => localStorage.clear());

  it('signs in through the API and keeps the session across restarts', () => {
    const { session: s, http } = setup();
    let member;
    s.signIn('ada@example.org', 'demo').subscribe((m) => (member = m));
    const req = http.expectOne('/api/auth/login');
    expect(req.request.body).toEqual({ email: 'ada@example.org', password: 'demo' });
    req.flush(session());
    expect(member).toEqual(ADA);
    expect(s.token()).toBe('tok');

    TestBed.resetTestingModule();
    expect(setup().session.member()?.name).toBe('Ada Lovelace');
  });

  it('forgets the session on sign-out', () => {
    localStorage.setItem(KEY, JSON.stringify(session()));
    const { session: s } = setup();
    s.signOut();
    expect(s.member()).toBeNull();
    expect(localStorage.getItem(KEY)).toBeNull();
  });

  it('treats an expired session as signed out', () => {
    localStorage.setItem(KEY, JSON.stringify(session(true)));
    const { session: s } = setup();
    expect(s.member()).toBeNull();
    expect(s.token()).toBeNull();
  });
});
