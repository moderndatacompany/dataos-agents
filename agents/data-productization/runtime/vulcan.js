#!/usr/bin/env node
const http=require('http');
const data=JSON.stringify({args:process.argv.slice(2),cwd:process.cwd()});
const req=http.request({host:'127.0.0.1',port:9173,path:'/run',method:'POST',headers:{'Content-Type':'application/json','Content-Length':Buffer.byteLength(data)}},res=>{let b='';res.on('data',x=>b+=x);res.on('end',()=>{try{const r=JSON.parse(b);process.stdout.write(r.stdout||'');process.stderr.write(r.stderr||'');process.exitCode=r.code??1;}catch{console.error('Vulcan runtime returned an invalid response');process.exitCode=1;}})});
req.on('error',()=>{console.error('Vulcan runtime is not ready');process.exitCode=1});req.end(data);
