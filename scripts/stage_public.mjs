import {copyFileSync,mkdirSync,readdirSync,readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {resolve,dirname} from 'node:path';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const release=resolve(root,'release');
const manifest=JSON.parse(readFileSync(resolve(release,'manifest.json'),'utf8'));
if(manifest.mode!=='public_aggregate'||!manifest.release_approved)throw Error('Edición pública no aprobada');
mkdirSync(resolve(root,'web/public/data'),{recursive:true});
for(const name of ['observatory.json','spatial.json','report.html'])copyFileSync(resolve(release,name),resolve(root,'web/public/data',name));
