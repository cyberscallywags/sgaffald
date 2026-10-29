import { HttpErrorResponse } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';

import { ApiService } from '../../core/api.service';
import { SessionService } from '../../core/session.service';
import { SiteStore } from '../../core/site.store';
import { ADA, SITE, session } from '../../testing/site.fixture';
import { SignInPage, safeReturn } from './sign-in.page';

function setup(login = vi.fn(() => of(session()))) {
  localStorage.clear();
  TestBed.configureTestingModule({
    imports: [SignInPage],
    providers: [provideRouter([]), { provide: ApiService, useValue: { login, site: () => of(SITE) } }],
  });
  TestBed.inject(SiteStore).site.set(SITE);
  const fixture = TestBed.createComponent(SignInPage);
  fixture.detectChanges();
  const navigate = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
  return { fixture, page: fixture.componentInstance, session: TestBed.inject(SessionService), navigate, login };
}

describe('SignInPage', () => {
  it('signs in with email and password, then goes back where it came from', () => {
    const { fixture, page, session: s, navigate, login } = setup();
    fixture.componentRef.setInput('returnUrl', '/items');
    page.form.setValue({ email: 'ada@example.org', password: 'demo' });
    page.submit();
    expect(login).toHaveBeenCalledWith('ada@example.org', 'demo');
    expect(s.member()).toEqual(ADA);
    expect(navigate).toHaveBeenCalledWith('/items');
  });

  it('lists the demo members, and one fills in its email', () => {
    const { fixture, page } = setup();
    expect(fixture.nativeElement.querySelector('[data-testid="demo-members"]').innerHTML).toContain(ADA.name);
    page.use(ADA);
    expect(page.form.controls.email.value).toBe(ADA.email);
  });

  it('shows a wrong password', () => {
    const login = vi.fn(() => throwError(() => new HttpErrorResponse({ status: 401 })));
    const { fixture, page, session: s } = setup(login);
    page.form.setValue({ email: 'ada@example.org', password: 'nope' });
    page.submit();
    fixture.detectChanges();
    expect(s.member()).toBeNull();
    expect(fixture.nativeElement.textContent).toContain('Wrong email or password');
  });

  it('rejects an invalid email without calling the API', () => {
    const { page, login } = setup();
    page.form.setValue({ email: 'not-an-email', password: 'demo' });
    page.submit();
    expect(login).not.toHaveBeenCalled();
    expect(page.form.touched).toBe(true);
  });

  it('only returns to paths inside the app', () => {
    expect(safeReturn('/items')).toBe('/items');
    expect(safeReturn('//evil.example')).toBe('/welcome');
    expect(safeReturn('https://evil.example')).toBe('/welcome');
    expect(safeReturn(undefined)).toBe('/welcome');
  });
});
