import { Routes } from '@angular/router';

import { authGuard } from './core/auth.guard';

const content = () => import('./pages/content/content.page').then((m) => m.ContentPage);

// Reserved paths (welcome, about, items, sign-in, account) mirror RESERVED_SLUGS in app/models.py.
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
  {
    path: 'account',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/account/account.page').then((m) => m.AccountPage),
  },
  { path: '', redirectTo: 'welcome', pathMatch: 'full' },
  { path: '**', redirectTo: 'welcome' },
];
