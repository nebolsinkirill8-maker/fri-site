const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, 'site');
http.createServer((req,res) => {
 const file = path.resolve(root, '.' + decodeURIComponent(new URL(req.url,'http://localhost').pathname).replace(/\/$/,'/index.html'));
 if (!file.startsWith(root + path.sep)) {res.writeHead(403).end(); return;}
 fs.readFile(file, (err, data) => {
  if(err) {res.writeHead(404).end(); return;}
  res.setHeader('Content-Type', ({'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.svg':'image/svg+xml','.webp':'image/webp','.ttf':'font/ttf'})[path.extname(file)] || 'application/octet-stream');
  if (path.extname(file) === '.mp3') {
    res.setHeader('Content-Type', 'audio/mpeg');
    res.setHeader('Accept-Ranges', 'bytes');
    const match = /^bytes=(\d+)-(\d*)$/.exec(req.headers.range || '');
    if (match) {
      const start = Number(match[1]);
      const end = Math.min(match[2] ? Number(match[2]) : data.length - 1, data.length - 1);
      if (start > end) { res.writeHead(416, {'Content-Range': `bytes */${data.length}`}).end(); return; }
      res.writeHead(206, {'Content-Range': `bytes ${start}-${end}/${data.length}`, 'Content-Length': end-start+1});
      res.end(data.subarray(start,end+1)); return;
    }
  }
  res.setHeader('Content-Length', data.length);
  res.end(data);
 });
}).listen(8139,'127.0.0.1',()=>console.log('http://127.0.0.1:8139/'));

