import {test,before,after} from 'node:test';
import assert from 'node:assert/strict';
import {createServer} from 'vite';
import {createElement} from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {readFile,readdir} from 'node:fs/promises';

let server,layouts,player,table,matching;
before(async()=>{
 server=await createServer({server:{middlewareMode:true,hmr:false},appType:'custom',optimizeDeps:{noDiscovery:true,include:[],entries:[]}});
 layouts=await server.ssrLoadModule('/ListeningLayouts.tsx');player=await server.ssrLoadModule('/ListeningPlayer.tsx');
 table=await server.ssrLoadModule('/QuestionLayouts.tsx');matching=await server.ssrLoadModule('/ListeningMatching.tsx');
});
after(async()=>{await server?.close();});
const noop=()=>{};
const props=g=>({group:g,attempt:{answers:{1:'first'},answerParts:{},annotations:[],flags:[]},editable:true,results:{},onAnswer:noop,onAnswerPart:noop,onFlag:noop,onFocus:noop,onAnnotation:noop});
const render=(c,p)=>renderToStaticMarkup(createElement(c,p));

test('Listening timeline respects trimmed audio boundaries and final checking time',()=>{
 const a={player:{part:2,position:5,phase:'audio',reviewRemaining:120},test:{passages:[1,2,3,4].map(number=>({number,audio:{duration:100,start:3,end:13}}))}};
 assert.equal(player.listeningRemaining(a),148);
 assert.equal(player.listeningRemaining({...a,player:{...a.player,phase:'check',reviewRemaining:17}}),17);
 assert.equal(player.clockText(0),'00:00');assert.equal(player.clockText(3601),'1:00:01');
});

test('Flow completion places editable inputs inside text, and locks them after submission',()=>{
 const g={id:'g',heading:'Questions 1–2',questions:[{number:1},{number:2}],layout:{kind:'flow',blocks:[{tag:'h3',content:['Form']},{tag:'p',content:['Name ',{number:1},' address ',{number:2}]}]}};
 const p=props(g);let html=render(layouts.ExtendedLayout,p);
 assert.equal((html.match(/<input/g)||[]).length,2);assert.match(html,/value="first"/);
 assert.equal(html.includes('answer-feedback correct'),false);assert.equal(html.includes('<img'),false);
 p.editable=false;p.results={1:{status:'correct',accepted:['first']}};
 html=render(layouts.ExtendedLayout,p);assert.equal((html.match(/<input[^>]*disabled/g)||[]).length,2);assert.match(html,/answer-feedback correct/);
});

test('Diagram labels are positioned in the diagram and retain answer numbers',()=>{
 const p=props({id:'map',heading:'Map',questions:[{number:1}],layout:{kind:'diagram',image:{url:'/library-assets/map.webp',page:1},labels:[{number:1,x:.3,y:.4,width:.2}]}});
 const html=render(layouts.ExtendedLayout,p);
 assert.match(html,/left:30%;top:40%;width:20%/);assert.match(html,/aria-label="Answer 1"/);assert.match(html,/map.webp/);
});

test('Start screen distinguishes simulation, full practice and Part practice',()=>{
 const html=render(player.ListeningStartModal,{test:{book:20,test:1,passages:[]},onClose:noop,onStart:noop});
 for(const label of ['Thi sát thật','Luyện cả đề','Luyện từng Part','nghe một lần','2 phút'])assert.ok(html.includes(label),label);
});

test('all local Listening completions and diagrams render their numbered controls, with no grading feedback',async()=>{
 let count=0;
 for(const file of await readdir('library/listening/tests')){
  const test=JSON.parse(await readFile('library/listening/tests/'+file,'utf8'));
  for(const part of test.parts)for(const g of part.groups){
   if(!g.layout&&g.type!=='matching')continue;
   const component=g.layout?.kind==='table'?table.InteractiveTable:g.layout?layouts.ExtendedLayout:matching.ListeningMatching;
   const html=render(component,props(g));
   const numbers=[...new Set([...html.matchAll(/(?:<input|<select)[^>]+aria-label="Answer (\d+)/g)].map(m=>+m[1]))].sort((a,b)=>a-b);
   assert.deepEqual(numbers,g.questions.map(q=>q.number),g.id);
   assert.equal(html.includes('answer-feedback correct'),false,g.id);
   const locked=render(component,{...props(g),editable:false});
   assert.equal((locked.match(/<(?:input|select)[^>]*disabled/g)||[]).length,(html.match(/<(?:input|select)/g)||[]).length,g.id);
   count++;
  }
 }
 assert.equal(count,127);
});
