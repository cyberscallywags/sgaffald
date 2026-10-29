import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpErrorResponse } from '@angular/common/http';
import { of, throwError } from 'rxjs';

import { provideRouter } from '@angular/router';

import { ApiService, Item } from '../../core/api.service';
import { SessionService } from '../../core/session.service';
import { SiteStore } from '../../core/site.store';
import { SITE, session } from '../../testing/site.fixture';
import { ItemsPage } from './items.page';

const existing: Item = { id: '1', name: 'existing', created_at: '2026-01-01T00:00:00Z' };

function setup(api: Partial<ApiService>): ComponentFixture<ItemsPage> {
  TestBed.configureTestingModule({
    imports: [ItemsPage],
    providers: [provideRouter([]), { provide: ApiService, useValue: api }],
  });
  const fixture = TestBed.createComponent(ItemsPage);
  fixture.detectChanges();
  return fixture;
}

describe('ItemsPage', () => {
  const stub = () => ({
    health: vi.fn(() => of({ status: 'ok', env: 'test', neo4j: true })),
    listItems: vi.fn(() => of([existing])),
    createItem: vi.fn((name: string) => of({ id: '2', name, created_at: '2026-01-02T00:00:00Z' })),
  });

  it('loads health and items from the API', () => {
    const api = stub();
    const fixture = setup(api);
    const text = fixture.nativeElement.textContent;
    expect(text).toContain('ok · test');
    expect(text).toContain('existing');
  });

  it('adds a created item to the top of the list', () => {
    const api = stub();
    const fixture = setup(api);
    fixture.componentInstance.name.setValue('  fresh  ');
    fixture.componentInstance.add();
    expect(api.createItem).toHaveBeenCalledWith('fresh');
    expect(fixture.componentInstance.items().map((i) => i.name)).toEqual(['fresh', 'existing']);
    expect(fixture.componentInstance.name.value).toBe('');
  });

  it('submits the form through Angular, not a native page load', () => {
    const api = stub();
    const fixture = setup(api);
    fixture.componentInstance.name.setValue('via form');
    const form: HTMLFormElement = fixture.nativeElement.querySelector('form');
    const submit = new Event('submit', { cancelable: true });
    form.dispatchEvent(submit);
    expect(submit.defaultPrevented).toBe(true);
    expect(api.createItem).toHaveBeenCalledWith('via form');
  });

  it('does not call the API for a blank name', () => {
    const api = stub();
    const fixture = setup(api);
    fixture.componentInstance.add();
    expect(api.createItem).not.toHaveBeenCalled();
  });

  it('shows the API validation message on rejection', () => {
    const api = stub();
    api.createItem.mockReturnValue(
      throwError(
        () =>
          new HttpErrorResponse({
            status: 422,
            error: { detail: [{ msg: 'String should have at most 200 characters' }] },
          }),
      ),
    );
    const fixture = setup(api);
    fixture.componentInstance.name.setValue('x');
    fixture.componentInstance.add();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('at most 200 characters');
  });

  it('shows offline when the API is unreachable', () => {
    const api = stub();
    api.health.mockReturnValue(throwError(() => new HttpErrorResponse({ status: 0 })));
    const fixture = setup(api);
    expect(fixture.nativeElement.textContent).toContain('offline');
  });

  it('asks for sign-in before adding when sign-on is mock', () => {
    localStorage.clear();
    TestBed.configureTestingModule({
      imports: [ItemsPage],
      providers: [provideRouter([]), { provide: ApiService, useValue: stub() }],
    });
    TestBed.inject(SiteStore).site.set(SITE);
    const fixture = TestBed.createComponent(ItemsPage);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('form')).toBeNull();
    expect(fixture.nativeElement.querySelector('[data-testid="sign-in-to-add"]')).not.toBeNull();
    TestBed.inject(SessionService).session.set(session());
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('form')).not.toBeNull();
  });
});
