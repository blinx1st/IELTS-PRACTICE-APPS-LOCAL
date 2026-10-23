import {createHash} from 'node:crypto';
import {readFileSync,readdirSync,existsSync} from 'node:fs';
import {join,relative,extname} from 'node:path';

const text=new Set(['.ts','.tsx','.css','.html','.json','.py','.mjs','.txt']);
const allowed=new Set([...text,'.png','.svg','.wav','.ttf']);
export function buildFingerprint(root){
 const files=[];
 function walk(folder){for(const item of readdirSync(folder,{withFileTypes:true})){const path=join(folder,item.name);if(item.isDirectory())walk(path);else if(allowed.has(extname(path)))files.push(path);}}
 walk(join(root,'frontend'));
 for(const name of ['package.json','package-lock.json','tsconfig.json','vite.config.ts','scripts/build_state.py','scripts/build-state.mjs'])if(existsSync(join(root,name)))files.push(join(root,name));
 const name=p=>relative(root,p).replaceAll('\\','/');
 files.sort((a,b)=>name(a)<name(b)?-1:name(a)>name(b)?1:0);
 const hash=createHash('sha256');
 for(const path of files){let data=readFileSync(path);if(text.has(extname(path)))data=Buffer.from(data.toString('utf8').replaceAll('\r\n','\n'));hash.update(name(path)+'\0');hash.update(data);hash.update('\0');}
 return hash.digest('hex');
}
