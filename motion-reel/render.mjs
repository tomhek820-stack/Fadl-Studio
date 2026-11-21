import puppeteer from "puppeteer";
import {mkdir,rm,readFile} from "node:fs/promises";
import {createServer} from "node:http";
import {spawn} from "node:child_process";
import path from "node:path";
const root=path.dirname(new URL(import.meta.url).pathname),out=path.join(root,"output"),frames=path.join(out,"frames");
await rm(out,{recursive:true,force:true});await mkdir(frames,{recursive:true});
const server=createServer(async(req,res)=>{
 let pathname=decodeURIComponent(new URL(req.url,"http://localhost").pathname);
 if(pathname==="/")pathname="/index.html";
 const file=path.resolve(root,"."+pathname);
 if(!file.startsWith(root)){res.writeHead(403);return res.end("forbidden")}
 try{const data=await readFile(file),ext=path.extname(file),types={".html":"text/html; charset=utf-8",".js":"text/javascript; charset=utf-8",".json":"application/json",".css":"text/css; charset=utf-8",".woff2":"font/woff2",".woff":"font/woff"};res.writeHead(200,{"content-type":types[ext]||"application/octet-stream"});res.end(data)}
 catch{res.writeHead(404);res.end("not found")}
});
await new Promise(ok=>server.listen(4173,"127.0.0.1",ok));
const browser=await puppeteer.launch({headless:true,args:["--no-sandbox","--disable-setuid-sandbox","--disable-dev-shm-usage"]});
try{
 const page=await browser.newPage({viewport:{width:1080,height:1920},deviceScaleFactor:1});
 page.on("console",m=>{if(m.type()==="error")console.error("BROWSER",m.text())});
 page.on("pageerror",e=>console.error("PAGEERROR",e.stack||e.message));
 await page.goto("http://127.0.0.1:4173/",{waitUntil:"networkidle0"});
 await page.evaluate(()=>document.fonts.ready);
 await page.addStyleTag({content:"html,body{width:1080px!important;height:1920px!important;min-height:1920px!important;margin:0!important;padding:0!important;overflow:hidden!important;display:block!important;background:#F2EFE9!important}.app{width:1080px!important;max-width:none!important;display:block!important}.screen{width:1080px!important;height:1920px!important;max-width:none!important;margin:0!important;border-radius:0!important;box-shadow:none!important}.screen canvas{width:1080px!important;height:1920px!important}.controls{display:none!important}"});
 await page.waitForFunction(()=>typeof window.setTime==="function",{timeout:15000});
 for(let f=0;f<1200;f++){
  await page.evaluate(n=>window.setTime(n/30),f);
  const shot=await (await page.$("#stage")).screenshot({path:path.join(frames,String(f).padStart(5,"0")+".png")});
  if(f===0 && (shot.length<10000)) throw Error("Unexpectedly small 1080x1920 frame");
  if(f%100===0)console.log("Rendered",f,"/1199");
 }
}finally{await browser.close();await new Promise(ok=>server.close(ok))}
await new Promise((ok,no)=>{
 const p=spawn("ffmpeg",["-y","-framerate","30","-i",path.join(frames,"%05d.png"),"-frames:v","1200","-c:v","libx264","-pix_fmt","yuv420p","-crf","18","-movflags","+faststart",path.join(out,"reel.mp4")],{stdio:"inherit"});
 p.on("exit",n=>n===0?ok():no(Error("ffmpeg "+n)));
});
