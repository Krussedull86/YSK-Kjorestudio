// Pure validation; no credentials or data access.
export function distributionPlan(value) {
 if(!value||typeof value!=='object'||Array.isArray(value))throw Error('Ugyldig distribusjonsplan.');
 const n=value.stop_count,t=value.expected_minutes,d=value.deadlines;
 if(!Number.isInteger(n)||n<0||n>30||typeof t!=='number'||!Number.isFinite(t)||t<0||t>1440||!Array.isArray(d)||d.length!==n||n===0&&t!==0||n>0&&t<=0)throw Error('Velg 0–30 stopp og forventet tid.');
 if(d.some((x,i)=>typeof x!=='number'||!Number.isFinite(x)||x<=0||x>t||i>0&&x<=d[i-1]))throw Error('Ugyldige stoppfrister.');
 return {stop_count:n,expected_minutes:t,deadlines:d};
}
export function validDistribution(value) {
 if(!value||value.version!==1||!Array.isArray(value.deadlines))throw Error('Ugyldig distribusjonslogg.');
 const p=distributionPlan({stop_count:value.deadlines.length,expected_minutes:value.expected_minutes,deadlines:value.deadlines});
 if(!p.stop_count||!Number.isInteger(value.started_at)||value.started_at<=0||value.started_at>1e15||!Array.isArray(value.events)||value.events.length>p.stop_count)throw Error('Ugyldig stopplogg.');
 let last=0;
 for(let i=0;i<value.events.length;i++){const e=value.events[i];if(!e||e.stop!==i+1||!['ramp','aborted'].includes(e.status)||typeof e.elapsed_minutes!=='number'||!Number.isFinite(e.elapsed_minutes)||e.elapsed_minutes<last||e.elapsed_minutes>43200||typeof e.reason!=='string'||e.reason.length>300)throw Error('Ugyldig distribusjonsstopp.');last=e.elapsed_minutes;}
 const f=value.finished_minutes;if(f!==null&&(typeof f!=='number'||!Number.isFinite(f)||f<last||f>43200||value.events.length!==p.stop_count))throw Error('Merk alle stopp før avslutning.');
 return value;
}
