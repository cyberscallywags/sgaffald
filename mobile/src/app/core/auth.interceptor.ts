import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

import { environment } from '../../environments/environment';
import { SessionService } from './session.service';

/**
 * Sends the member's token to the API (and only the API). A 401 on a signed-in request means
 * the session ended, so it signs out and goes to sign-in, coming back afterwards.
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const session = inject(SessionService);
  const router = inject(Router);
  const token = session.token();
  const toApi = req.url.startsWith(environment.apiUrl);
  const request = token && toApi ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req;
  return next(request).pipe(
    catchError((err: unknown) => {
      if (err instanceof HttpErrorResponse && err.status === 401 && token && toApi) {
        session.signOut();
        void router.navigateByUrl(`/sign-in?returnUrl=${encodeURIComponent(router.url)}`);
      }
      return throwError(() => err);
    }),
  );
};
