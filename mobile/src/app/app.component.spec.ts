import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { AppComponent } from './app.component';
import { ApiService } from './core/api.service';
import { SessionService } from './core/session.service';
import { FEATURES } from './features';
import { SITE, session } from './testing/site.fixture';

function setup() {
  TestBed.configureTestingModule({
    imports: [AppComponent],
    providers: [provideRouter([]), { provide: ApiService, useValue: { site: () => of(SITE) } }],
  });
  const fixture = TestBed.createComponent(AppComponent);
  fixture.detectChanges();
  return fixture;
}

describe('AppComponent', () => {
  beforeEach(() => localStorage.clear());

  it('builds the side menu from the manifest, then the code-backed features', () => {
    const fixture = setup();
    expect(fixture.componentInstance.nav().map((e) => e.path)).toEqual([
      '/welcome',
      '/p/roadmap',
      ...FEATURES.map((f) => f.path), // Items, then any entity added with task new_entity
    ]);
    const menu: HTMLElement = fixture.nativeElement.querySelector('[data-testid="menu"]');
    expect(menu.textContent).toContain('Roadmap');
  });

  it('always links to About in the menu footer', () => {
    // innerHTML, not textContent: Stencil patches textContent on scoped Ionic elements.
    const el: HTMLElement = setup().nativeElement;
    const about = el.querySelector('ion-footer ion-item');
    expect(about?.getAttribute('href')).toBe('/about');
    expect(about?.innerHTML).toContain(SITE.about.title);
    expect(el.querySelector('ion-footer ion-note')?.innerHTML).toContain(
      `${SITE.brand.name} · a ${SITE.brand.collective} project`,
    );
  });

  it('links to the docs portal when the API provides a docs URL', () => {
    const el: HTMLElement = setup().nativeElement;
    const docs = el.querySelector('[data-testid="docs-link"]') as HTMLIonItemElement;
    expect(docs.href).toBe('http://localhost:8200'); // [href] binds the property
    expect(docs.target).toBe('_blank');
    expect(docs?.innerHTML).toContain('Documentation');
  });

  it('hides the docs link when there is no docs URL', () => {
    TestBed.configureTestingModule({
      imports: [AppComponent],
      providers: [
        provideRouter([]),
        { provide: ApiService, useValue: { site: () => of({ ...SITE, docs_url: null }) } },
      ],
    });
    const fixture = TestBed.createComponent(AppComponent);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[data-testid="docs-link"]')).toBeNull();
  });

  it('offers sign-in, then shows the signed-in member and their role', () => {
    const fixture = setup();
    const signOn = () =>
      (fixture.nativeElement.querySelector('[data-testid="sign-on"]') as HTMLElement).textContent;
    expect(signOn()).toContain('Sign in');
    TestBed.inject(SessionService).session.set(session());
    fixture.detectChanges();
    expect(signOn()).toContain('Ada Lovelace');
    expect(signOn()).toContain('admin');
  });

  it('hides sign-on when it is off', () => {
    TestBed.configureTestingModule({
      imports: [AppComponent],
      providers: [
        provideRouter([]),
        { provide: ApiService, useValue: { site: () => of({ ...SITE, auth: { mode: 'off', demo_users: [] } }) } },
      ],
    });
    const fixture = TestBed.createComponent(AppComponent);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[data-testid="sign-on"]')).toBeNull();
  });
});
