import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { ApiService } from '../../core/api.service';
import { SiteStore } from '../../core/site.store';
import { SITE } from '../../testing/site.fixture';
import { ContentPage } from './content.page';

function render(slug: string): HTMLElement {
  TestBed.configureTestingModule({
    imports: [ContentPage],
    providers: [provideRouter([]), { provide: ApiService, useValue: { site: () => of(SITE) } }],
  });
  TestBed.inject(SiteStore).load();
  const fixture = TestBed.createComponent(ContentPage);
  fixture.componentRef.setInput('slug', slug);
  fixture.detectChanges();
  return fixture.nativeElement;
}

describe('ContentPage', () => {
  beforeEach(() => localStorage.clear());

  it('shows the brand hero and planning steps on welcome', () => {
    const el = render('welcome');
    expect(el.querySelector('.hero h1')?.textContent).toBe(SITE.brand.name);
    expect(el.textContent).toContain('Plan it, ship it');
    expect(el.textContent).toContain('Name the domain');
  });

  it('renders the About page for the collective', () => {
    expect(render('about').textContent).toContain(SITE.about.title);
  });

  it('renders a sidebar page by slug', () => {
    expect(render('roadmap').querySelector('[data-testid="page-roadmap"]')).toBeTruthy();
  });

  it('says so when the slug is not in the manifest', () => {
    expect(render('nope').textContent).toContain('not in the site manifest');
  });
});
