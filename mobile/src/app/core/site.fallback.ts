import { Site } from './api.service';
import meta from './meta.json';

/**
 * Shown until GET /site answers (and when the API is unreachable on first launch). Brand and
 * theme come from meta.json, generated from brand.toml and site.json by `uv run task sync`,
 * like src/theme/_brand.scss, so the first paint matches.
 */
export const FALLBACK_SITE: Site = {
  brand: meta.brand,
  theme: { font_family: "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif", ...meta.theme },
  welcome: { slug: 'welcome', title: 'Welcome', icon: 'home-outline', sections: [] },
  about: { slug: 'about', title: 'About', icon: 'people-outline', sections: [] },
  pages: [],
};
