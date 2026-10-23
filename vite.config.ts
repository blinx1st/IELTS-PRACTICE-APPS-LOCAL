import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {buildFingerprint} from './scripts/build-state.mjs';
const root=fileURLToPath(new URL('.',import.meta.url));
const sourceFingerprint=buildFingerprint(root);
const logoSha256=createHash('sha256').update(readFileSync(new URL('./frontend/public/app-logo.png',import.meta.url))).digest('hex');
const logoUrl='/app-logo.png?v='+logoSha256.slice(0,16);
export default defineConfig({
 plugins: [react(),{
  name:'local-build-provenance',
  transformIndexHtml:html=>html.replace('href="/app-logo.png"',`href="${logoUrl}"`),
  generateBundle(){this.emitFile({type:'asset',fileName:'build-info.json',source:JSON.stringify({schemaVersion:1,sourceFingerprint,logoSha256},null,2)});},
 }],
 define:{__APP_LOGO_URL__:JSON.stringify(logoUrl)},
 root:'frontend',build:{outDir:'../dist',emptyOutDir:true},
 server:{proxy:{'/api':'http://127.0.0.1:8765','/library-assets':'http://127.0.0.1:8765','/library-audio':'http://127.0.0.1:8765'}},
});
