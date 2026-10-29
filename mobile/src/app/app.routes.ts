import { Routes } from '@angular/router';

const content = () => import('./pages/content/content.page').then((m) => m.ContentPage);

// Reserved paths (welcome, about, items, sign-in) mirror RESERVED_SLUGS in app/models.py.
export const routes: Routes = [
  { path: 'welcome', loadComponent: content, data: { slug: 'welcome' } },
  { path: 'about', loadComponent: content, data: { slug: 'about' } },
  { path: 'p/:slug', loadComponent: content },
  {
    path: 'items',
    loadComponent: () => import('./pages/items/items.page').then((m) => m.ItemsPage),
  },
  {
    path: 'sign-in',
    loadComponent: () => import('./pages/sign-in/sign-in.page').then((m) => m.SignInPage),
  },
  { path: '', redirectTo: 'welcome', pathMatch: 'full' },
  { path: '**', redirectTo: 'welcome' },
];
