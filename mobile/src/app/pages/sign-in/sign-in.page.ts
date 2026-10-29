import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, inject, input, signal } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import {
  IonButton,
  IonButtons,
  IonContent,
  IonHeader,
  IonInput,
  IonItem,
  IonLabel,
  IonList,
  IonListHeader,
  IonMenuButton,
  IonNote,
  IonText,
  IonTitle,
  IonToolbar,
} from '@ionic/angular';

import { Member } from '../../core/api.service';
import { SessionService } from '../../core/session.service';
import { SiteStore } from '../../core/site.store';

@Component({
  selector: 'app-sign-in',
  templateUrl: 'sign-in.page.html',
  imports: [
    ReactiveFormsModule,
    IonButton,
    IonButtons,
    IonContent,
    IonHeader,
    IonInput,
    IonItem,
    IonLabel,
    IonList,
    IonListHeader,
    IonMenuButton,
    IonNote,
    IonText,
    IonTitle,
    IonToolbar,
  ],
})
export class SignInPage {
  private readonly router = inject(Router);
  private readonly site = inject(SiteStore).site;
  protected readonly session = inject(SessionService);

  /** Where to go afterwards: the ?returnUrl= query parameter (component input binding). */
  readonly returnUrl = input<string | undefined>();
  readonly mode = computed(() => this.site().auth?.mode ?? 'off');
  readonly demoMembers = computed(() => this.site().auth?.demo_users ?? []);
  readonly error = signal<string | null>(null);
  readonly busy = signal(false);

  readonly form = new FormGroup({
    email: new FormControl('', {
      nonNullable: true,
      validators: [Validators.required, Validators.email],
    }),
    password: new FormControl('', { nonNullable: true, validators: [Validators.required] }),
  });

  constructor() {
    inject(SiteStore).pageTitle.set('Sign in');
  }

  /** A demo member's shortcut fills in their email; the shared password is still typed. */
  use(member: Member): void {
    this.form.patchValue({ email: member.email });
  }

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const { email, password } = this.form.getRawValue();
    this.busy.set(true);
    this.error.set(null);
    this.session.signIn(email.trim(), password).subscribe({
      next: () => {
        this.busy.set(false);
        this.form.reset();
        void this.router.navigateByUrl(safeReturn(this.returnUrl()));
      },
      error: (err: HttpErrorResponse) => {
        this.busy.set(false);
        this.error.set(describe(err));
      },
    });
  }
}

/** Only paths inside the app, so a crafted link cannot send a member elsewhere. */
export function safeReturn(url: string | undefined): string {
  return url && url.startsWith('/') && !url.startsWith('//') ? url : '/welcome';
}

function describe(err: HttpErrorResponse): string {
  if (err.status === 401) return 'Wrong email or password';
  if (err.status === 404) return 'Sign-on is off';
  return err.status ? `API error ${err.status}` : 'API unreachable';
}
