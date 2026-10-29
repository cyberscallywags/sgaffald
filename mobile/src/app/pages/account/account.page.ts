import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import {
  IonButton,
  IonButtons,
  IonContent,
  IonHeader,
  IonItem,
  IonLabel,
  IonList,
  IonMenuButton,
  IonTitle,
  IonToolbar,
} from '@ionic/angular';

import { SessionService } from '../../core/session.service';
import { SiteStore } from '../../core/site.store';

/** Who is signed in. authGuard keeps signed-out visitors away. */
import { AccountMenuComponent } from '../../shared/account-menu.component';

@Component({
  selector: 'app-account',
  templateUrl: 'account.page.html',
  imports: [
    AccountMenuComponent,
    IonButton,
    IonButtons,
    IonContent,
    IonHeader,
    IonItem,
    IonLabel,
    IonList,
    IonMenuButton,
    IonTitle,
    IonToolbar,
  ],
})
export class AccountPage {
  private readonly router = inject(Router);
  protected readonly session = inject(SessionService);

  constructor() {
    inject(SiteStore).pageTitle.set('Account');
  }

  signOut(): void {
    this.session.signOut();
    void this.router.navigateByUrl('/welcome');
  }
}
