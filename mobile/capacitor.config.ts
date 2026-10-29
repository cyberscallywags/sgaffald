import type { CapacitorConfig } from '@capacitor/cli';

import meta from './src/app/core/meta.json'; // generated from brand.toml

const config: CapacitorConfig = {
  appId: meta.appId,
  appName: meta.name,
  webDir: 'www'
};

export default config;
