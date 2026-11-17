import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {score,defaultWeights,priority} from '../web/src/lib/ipiv.ts';
import {distanceMeters,proximityBounds} from '../web/src/lib/geo.ts';
import {parseHash} from '../web/src/lib/routes.ts';
test('IPIV no recupera dimensiones ocultas aunque peso cero',()=>{
 const c={frequency:50,mortality:null,injuries:20,trend:50,vulnerable:10};
 assert.equal(score(c,{frequency:100,mortality:0,injuries:0,trend:0,vulnerable:0}),null);
 assert.equal(score({...c,mortality:20},defaultWeights),31);
 assert.equal(priority(null),'No calculable');assert.equal(priority(75),'Muy alta');
});
test('Rutas de fichas persistentes y salto de contenido',()=>{
 assert.equal(parseHash('#content'),null);
 assert.equal(parseHash('#ficha/h3-r7-8748a28a8ffffff').section,'ficha');
 assert.equal(parseHash('#ficha/<script>').section,'notfound');
});
test('Proximidad usa cotas y no convierte centroides en eventos',()=>{
 assert.ok(distanceMeters([-100,25],[-100,25.01])>1000);
 const cell={properties:{cell:'x',crashes:20,municipality:'x',year:'2025'},geometry:{type:'Polygon',coordinates:[[[-.004,-.004],[.004,-.004],[.004,.004],[-.004,.004],[-.004,-.004]]]}};
 assert.deepEqual([proximityBounds([cell],[0,0],100).lower,proximityBounds([cell],[0,0],100).upper],[0,20]);
 assert.deepEqual([proximityBounds([cell],[0,0],2000).lower,proximityBounds([cell],[0,0],2000).upper],[20,20]);
 assert.throws(()=>proximityBounds([cell],[0,0],0));
});
test('Scores de la edición real coinciden con el cálculo materializado',()=>{
 const data=JSON.parse(readFileSync(new URL('../release/intelligence.json',import.meta.url),'utf8'));
 for(const z of data.zones){const value=score(z.normalized.minmax,defaultWeights);if(z.score===null)assert.equal(value,null);else assert.ok(Math.abs(value-z.score)<1e-6)}
 const z=data.zones.find(z=>z.score!==null);const before=score(z.normalized.minmax,defaultWeights);assert.equal(score([z][0].normalized.minmax,defaultWeights),before);
});
