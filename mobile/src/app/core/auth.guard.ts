import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { SessionService } from './session.service';
import { SiteStore } from './site.store';

/** Lets a member through; sends anyone else to sign-in, coming back afterwards. */
export const authGuard: CanActivateFn = (_route, state) => {
  if (inject(SiteStore).site().auth?.mode !== 'mock' || inject(SessionService).member()) {
    return true;
  }
  return inject(Router).createUrlTree(['/sign-in'], { queryParams: { returnUrl: state.url } });
};
