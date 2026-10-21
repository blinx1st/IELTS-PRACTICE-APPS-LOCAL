import {test,before,after} from 'node:test';
import assert from 'node:assert/strict';
import {readFile,readdir} from 'node:fs/promises';
import {createServer} from 'vite';
import {createElement} from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
let server,flow,columns,matching;
const noop=()=>{},render=(c,p)=>renderToStaticMarkup(createElement(c,p));
const props=group=>({group,attempt:{answers:{2:'old answer'},answerParts:{},annotations:[],flags:[2]},editable:true,results:{},onAnswer:noop,onAnswerPart:noop,onFlag:noop,onFocus:noop,onAnnotation:noop});
before(async()=>{server=await createServer({server:{middlewareMode:true,hmr:false},appType:'custom',optimizeDeps:{noDiscovery:true,include:[],entries:[]}});flow=await server.ssrLoadModule('/ListeningLayouts.tsx');columns=await server.ssrLoadModule('/ListeningColumns.tsx');matching=await server.ssrLoadModule('/ListeningMatching.tsx');});
after(async()=>{await server?.close();});

test('82 Reading text groups render all 414 controls inside their text and lock on submission',async()=>{
 let count=0,total=0,wordBanks=0;
 for(const name of await readdir('library/tests')){
  const test=JSON.parse(await readFile('library/tests/'+name,'utf8'));
  for(const g of test.passages.flatMap(p=>p.groups).filter(g=>g.layout?.kind==='flow')){
   const html=render(flow.ExtendedLayout,props(g));
   const numbers=[...html.matchAll(/<(?:input|select)[^>]+aria-label="Answer (\d+)/g)].map(m=>+m[1]);
   assert.deepEqual(numbers,g.questions.map(q=>q.number),g.id);
   assert.equal(html.includes('<img'),false,g.id);assert.equal(html.includes('answer-feedback correct'),false,g.id);
   const locked=render(flow.ExtendedLayout,{...props(g),editable:false});
   assert.equal((locked.match(/<(?:input|select)[^>]*disabled/g)||[]).length,numbers.length,g.id);
   if(g.type==='matching'){wordBanks++;assert.equal((html.match(/<select/g)||[]).length,numbers.length);for(const o of g.options)assert.ok(html.includes(o.label.replaceAll('&','&amp;')),g.id);}
   if(g.id==='cam18-t2-p1-g1'){assert.match(html,/value="old answer"/);assert.ok(html.indexOf('Answer 2')<html.indexOf('may have been arranged in deep pits'));}
   count++;total+=numbers.length;
  }
 }
 assert.equal(count,82);assert.equal(total,414);assert.equal(wordBanks,17);
});
test('column partition follows numeric and keyboard order and keeps odd extra question on the left',()=>{
 assert.deepEqual(columns.splitQuestions([1,2,3,4,5]),[[1,2,3],[4,5]]);
 const html=render(columns.QuestionColumns,{items:[1,2,3,4,5],split:true,render:n=>createElement('input',{key:n,'aria-label':'Answer '+n})});
 assert.equal((html.match(/class="question-column"/g)||[]).length,2);
 assert.deepEqual([...html.matchAll(/Answer (\d)/g)].map(m=>+m[1]),[1,2,3,4,5]);
 const g={type:'choice',questions:[1,2,3,4]};
 assert.equal(columns.canSplitQuestions(g,'auto'),true);assert.equal(columns.canSplitQuestions(g,'one'),false);
 assert.equal(columns.canSplitQuestions({...g,questions:[1,2,3]},'auto'),false);
 assert.equal(columns.canSplitQuestions({...g,questions:[1,2]},'two'),true);
 for(const kind of ['table','flow','diagram'])assert.equal(columns.canSplitQuestions({...g,layout:{kind}},'two'),false);
 assert.equal(columns.canSplitQuestions({...g,type:'multi'},'two'),false);
 assert.equal(columns.canSplitQuestions({...g,type:'matching',instructions:'Complete the flow-chart below.'},'two'),false);
});
test('split matching renders one shared option list above both columns and preserves locked answers',()=>{
 const group={id:'m',type:'matching',questions:[1,2,3,4,5].map(number=>({number,text:'Prompt '+number})),options:[{value:'A',label:'First option'},{value:'B',label:'Second option'}]};
 const p=props(group);p.attempt.answers={2:'B'};const html=render(matching.ListeningMatching,{...p,twoColumns:true});
 assert.equal((html.match(/List of options/g)||[]).length,1);assert.equal((html.match(/<select/g)||[]).length,5);
 assert.ok(html.indexOf('List of options')<html.indexOf('Prompt 1'));assert.match(html,/<option value="B" selected="">/);
 const locked=render(matching.ListeningMatching,{...p,twoColumns:true,editable:false});assert.equal((locked.match(/<select[^>]*disabled/g)||[]).length,5);
});
