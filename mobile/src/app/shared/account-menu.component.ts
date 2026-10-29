import { Component, computed, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import {
  IonButton,
  IonIcon,
  IonItem,
  IonLabel,
  IonList,
  IonPopover,
  IonRouterLink,
} from '@ionic/angular';

import { iconName } from '../core/icons';
import { SessionService } from '../core/session.service';
import { SiteStore } from '../core/site.store';

/**
 * The toolbar's account button: the member's initials, opening a popover with who they are
 * and Sign out; "Sign in" when signed out; nothing when sign-on is off. The mobile twin of
 * the web UI's navbar account panel.
 */
@Component({
  selector: 'app-account-menu',
  templateUrl: 'account-menu.component.html',
  styleUrls: ['account-menu.component.scss'],
  imports: [RouterLink, IonButton, IonIcon, IonItem, IonLabel, IonList, IonPopover, IonRouterLink],
})
export class AccountMenuComponent {
  private readonly router = inject(Router);
  protected readonly session = inject(SessionService);
  protected readonly iconName = iconName;
  protected readonly initials = initials;

  private readonly site = inject(SiteStore).site;
  readonly enabled = computed(() => this.site().auth?.mode === 'mock');
  readonly open = signal(false);
  protected trigger: Event | undefined;

  show(event: Event): void {
    this.trigger = event;
    this.open.set(true);
  }

  signOut(): void {
    this.open.set(false);
    this.session.signOut();
    void this.router.navigateByUrl('/welcome');
  }
}

/** "Ada Lovelace" → "AL". */
export function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join('');
}
