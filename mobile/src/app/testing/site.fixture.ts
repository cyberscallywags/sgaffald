import { Member, Session, Site } from '../core/api.service';
import { FALLBACK_SITE } from '../core/site.fallback';

/** A small manifest shaped like content/site.json, for specs. */
export const SITE: Site = {
  ...FALLBACK_SITE,
  brand: { ...FALLBACK_SITE.brand, tagline: 'Plan it, ship it' },
  welcome: {
    slug: 'welcome',
    title: 'Welcome',
    icon: 'home-outline',
    summary: 'Plan the application',
    sections: [{ kind: 'steps', heading: 'Planning', items: [{ title: 'Name the domain' }] }],
  },
  about: {
    slug: 'about',
    title: `About ${FALLBACK_SITE.brand.collective}`,
    icon: 'people-outline',
    sections: [{ kind: 'text', heading: 'Who we are', body: 'A collective', items: [] }],
  },
  docs_url: 'http://localhost:8200',
  auth: { mode: 'mock', demo_users: [] },
  pages: [
    {
      slug: 'roadmap',
      title: 'Roadmap',
      icon: 'map-outline',
      sections: [{ kind: 'cards', items: [{ title: 'Release', icon: 'rocket-outline' }] }],
    },
  ],
};

export const ADA: Member = { id: 'ada', name: 'Ada Lovelace', email: 'ada@example.org', role: 'admin' };
SITE.auth!.demo_users = [ADA];

/** A session for ADA that lasts an hour from now (or ended a minute ago). */
export function session(expired = false): Session {
  const ms = expired ? -60_000 : 3_600_000;
  return { token: 'tok', member: ADA, expires_at: new Date(Date.now() + ms).toISOString() };
}
