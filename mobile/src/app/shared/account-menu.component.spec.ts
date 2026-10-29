import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { ApiService } from '../core/api.service';
import meta from '../core/meta.json';
import { SessionService } from '../core/session.service';
import { SiteStore } from '../core/site.store';
import { SITE, session } from '../testing/site.fixture';
import { AccountMenuComponent, initials } from './account-menu.component';

function setup(signedIn: boolean, mode: 'mock' | 'off' = 'mock') {
  localStorage.clear();
  if (signedIn) localStorage.setItem(`${meta.slug}.session`, JSON.stringify(session()));
  TestBed.configureTestingModule({
    imports: [AccountMenuComponent],
    providers: [provideRouter([]), { provide: ApiService, useValue: { site: () => of(SITE) } }],
  });
  TestBed.inject(SiteStore).site.set({ ...SITE, auth: { mode, demo_users: [] } });
  const fixture = TestBed.createComponent(AccountMenuComponent);
  fixture.detectChanges();
  const button = () => fixture.nativeElement.querySelector('[data-testid="account-button"]');
  return { fixture, button };
}

describe('AccountMenuComponent', () => {
  it("shows the member's initials and opens the menu", () => {
    const { fixture, button } = setup(true);
    expect(button().innerHTML).toContain('AL');
    fixture.componentInstance.show(new Event('click'));
    expect(fixture.componentInstance.open()).toBe(true);
  });

  it('signs out from the menu and goes home', () => {
    const { fixture } = setup(true);
    const navigate = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
    fixture.componentInstance.signOut();
    expect(TestBed.inject(SessionService).member()).toBeNull();
    expect(navigate).toHaveBeenCalledWith('/welcome');
  });

  it('offers sign-in when signed out', () => {
    const { button } = setup(false);
    expect(button().innerHTML).toContain('Sign in');
  });

  it('shows nothing when sign-on is off', () => {
    expect(setup(false, 'off').button()).toBeNull();
  });

  it('takes the first letters of up to two names', () => {
    expect(initials('Ada Lovelace')).toBe('AL');
    expect(initials('grace')).toBe('G');
    expect(initials('Alan Mathison Turing')).toBe('AM');
  });
});
