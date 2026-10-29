import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';

import { session } from '../testing/site.fixture';
import { authInterceptor } from './auth.interceptor';
import meta from './meta.json';
import { SessionService } from './session.service';

function setup(signedIn: boolean) {
  localStorage.clear();
  if (signedIn) localStorage.setItem(`${meta.slug}.session`, JSON.stringify(session()));
  TestBed.configureTestingModule({
    providers: [
      provideRouter([]),
      provideHttpClient(withInterceptors([authInterceptor])),
      provideHttpClientTesting(),
    ],
  });
  const navigate = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
  return {
    http: TestBed.inject(HttpClient),
    backend: TestBed.inject(HttpTestingController),
    session: TestBed.inject(SessionService),
    navigate,
  };
}

describe('authInterceptor', () => {
  it('sends the token to the API', () => {
    const { http, backend } = setup(true);
    http.get('/api/items').subscribe();
    expect(backend.expectOne('/api/items').request.headers.get('Authorization')).toBe('Bearer tok');
  });

  it('never sends the token anywhere else', () => {
    const { http, backend } = setup(true);
    http.get('https://elsewhere.example/x').subscribe();
    expect(backend.expectOne('https://elsewhere.example/x').request.headers.has('Authorization')).toBe(false);
  });

  it('sends nothing when signed out', () => {
    const { http, backend } = setup(false);
    http.get('/api/items').subscribe();
    expect(backend.expectOne('/api/items').request.headers.has('Authorization')).toBe(false);
  });

  it('signs out and goes to sign-in when the API says the session ended', () => {
    const { http, backend, session: s, navigate } = setup(true);
    http.post('/api/items', {}).subscribe({ error: () => undefined });
    backend.expectOne('/api/items').flush({ detail: 'Session expired' }, { status: 401, statusText: '' });
    expect(s.member()).toBeNull();
    expect(navigate).toHaveBeenCalledWith('/sign-in?returnUrl=%2F');
  });
});
