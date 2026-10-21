export type QuestionFilter='all'|'unanswered'|'review';
export function filterQuestions(numbers:number[],answers:Record<string,string>,flags:number[],filter:QuestionFilter){
  return numbers.filter(n=>filter==='all'||(filter==='review'?flags.includes(n):!answers[n]?.trim()));
}
export function adjacentQuestion(numbers:number[],current:number,direction:-1|1):number|undefined{
  return direction===1?numbers.find(n=>n>current):[...numbers].reverse().find(n=>n<current);
}
