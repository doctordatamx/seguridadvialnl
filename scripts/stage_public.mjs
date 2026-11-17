import {copyFileSync,mkdirSync,readdirSync,readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {resolve,dirname} from 'node:path';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const release=resolve(root,'release');
const manifest=JSON.parse(readFileSync(resolve(release,'manifest.json'),'utf8'));
if(manifest.mode!=='public_aggregate'||!manifest.release_approved)throw Error('Edición pública no aprobada');
mkdirSync(resolve(root,'web/public/data'),{recursive:true});
const allowed=new Set(['observatory.json','spatial.json','report.html','intelligence.json','temporal.json','methods.json','boundaries.json','institutions.json','atlas-metadata.json','mobility.json','spatial-quality.json']);
for(const name of Object.keys(manifest.sha256)){if(!allowed.has(name))throw Error('Recurso no permitido: '+name);copyFileSync(resolve(release,name),resolve(root,'web/public/data',name))}
