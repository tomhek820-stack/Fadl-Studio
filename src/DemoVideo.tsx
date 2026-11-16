import React from "react";
import {Audio, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig} from "remotion";
import "@fontsource/noto-sans-arabic/400.css";
import "@fontsource/noto-sans-arabic/600.css";
import "@fontsource/noto-sans-arabic/800.css";

type WordTiming = {text:string; startFrame:number; endFrame:number};
type Scene = {
  id:string; eyebrow:string; title:string; body:string; narration:string;
  caption:string; icon:string; audio:string; durationInFrames:number;
  audioDurationFrames:number; wordTimings:WordTiming[];
};
export type DemoProps = {title:string; scenes:Scene[]};
const palette=["#00D4FF","#9B8CFF","#35E0B2","#FFB86B","#65A7FF"];
const sceneNumbers=["٠١","٠٢","٠٣","٠٤","٠٥"];

const Icon:React.FC<{name:string;color:string}>=({name,color})=>{
  const common={fill:"none",stroke:color,strokeWidth:7,strokeLinecap:"round" as const,strokeLinejoin:"round" as const};
  const paths:Record<string,React.ReactNode>={
    spark:<><path {...common} d="M50 5 61 39 95 50 61 61 50 95 39 61 5 50 39 39Z"/><path {...common} d="m82 8 4 12 12 4-12 4-4 12-4-12-12-4 12-4Z"/></>,
    script:<><path {...common} d="M20 12h45l15 15v61H20Z"/><path {...common} d="M65 12v18h15M34 47h32M34 62h32M34 77h22"/></>,
    audio:<><path {...common} d="M14 58V42h18l25-20v56L32 58Z"/><path {...common} d="M70 39q18 11 0 22M80 25q32 25 0 50"/></>,
    captions:<><rect {...common} x="10" y="18" width="80" height="64" rx="10"/><path {...common} d="M25 43h50M25 59h38"/></>,
    export:<><path {...common} d="M50 10v53M31 29l19-19 19 19M18 62v24h64V62"/></>,
  };
  return <svg viewBox="0 0 100 100" width="100%" height="100%" aria-hidden="true">{paths[name]??paths.spark}</svg>;
};

const WordCaptions:React.FC<{scene:Scene;frame:number;landscape:boolean;color:string}>=({scene,frame,landscape,color})=>{
  const active=scene.wordTimings.findIndex(w=>frame>=w.startFrame&&frame<w.endFrame);
  return <div dir="rtl" style={{display:"flex",flexDirection:"row-reverse",flexWrap:"wrap",justifyContent:"center",
    alignItems:"center",columnGap:landscape?12:16,rowGap:landscape?9:12}}>
    {scene.wordTimings.map((word,index)=>{
      const highlighted=index===active;
      return <span key={index} dir="rtl" style={{fontSize:landscape?27:37,lineHeight:1.7,fontWeight:800,
        color:highlighted?"#07111D":"#F4F7FC",background:highlighted?color:"transparent",
        borderRadius:9,padding:highlighted?"0px 8px":"0px 2px",
        textShadow:highlighted?"none":"0 2px 10px #0008",transition:"none"}}>
        {word.text}
      </span>;
    })}
  </div>;
};

const SceneCard:React.FC<{scene:Scene;index:number;color:string}>=({scene,index,color})=>{
  const frame=useCurrentFrame();
  const {fps,width,height}=useVideoConfig();
  const enter=spring({frame,fps,config:{damping:16,stiffness:90}});
  const landscape=width>height;
  const scale=0.92+enter*0.08;
  const translate=(1-enter)*42;
  const captionOpacity=frame<scene.audioDurationFrames?1:0;
  return <div style={{width:"100%",height:"100%",position:"relative",overflow:"hidden",
    background:"radial-gradient(ellipse at 50% 25%, #14243b 0%, #090e19 48%, #05070d 100%)",
    color:"#F4F7FC",fontFamily:"'Noto Sans Arabic', sans-serif",display:"flex",flexDirection:"column",
    alignItems:"center",justifyContent:landscape?"center":"space-between",
    padding:landscape?"7% 10%":"10% 8%",boxSizing:"border-box",direction:"rtl"}}>
    <div style={{position:"absolute",inset:0,opacity:0.15,backgroundImage:"linear-gradient(rgba(255,255,255,.06) 1px, transparent 1px),linear-gradient(90deg,rgba(255,255,255,.06) 1px,transparent 1px)",backgroundSize:"72px 72px"}}/>
    <div style={{position:"absolute",width:"70%",height:"32%",top:"-12%",left:"15%",borderRadius:"50%",background:color,filter:"blur(120px)",opacity:0.2}}/>
    <div style={{zIndex:1,width:"100%",display:"flex",justifyContent:"space-between",alignItems:"center"}}>
      <div style={{fontSize:landscape?25:30,fontWeight:800}}>فَضْل ستوديو</div>
      <div dir="ltr" style={{fontSize:landscape?20:24,color:"#9CAEC4"}}>{sceneNumbers[index]} / ٠٥</div>
    </div>
    <div style={{zIndex:1,width:"100%",display:"flex",flex:1,flexDirection:"column",alignItems:"center",
      justifyContent:"center",gap:landscape?26:48,transform:"translateY("+translate+"px) scale("+scale+")",opacity:enter}}>
      <div style={{width:landscape?130:190,height:landscape?130:190,padding:28,borderRadius:42,
        boxSizing:"border-box",background:"rgba(255,255,255,.055)",border:"2px solid "+color+"66",
        boxShadow:"0 0 70px "+color+"22"}}><Icon name={scene.icon} color={color}/></div>
      <div dir="rtl" style={{fontSize:landscape?25:34,color,fontWeight:600,textAlign:"center"}}>{scene.eyebrow}</div>
      <div dir="rtl" style={{fontSize:landscape?64:76,fontWeight:800,lineHeight:1.35,textAlign:"center",
        maxWidth:"92%",textShadow:"0 8px 35px #0008"}}>{scene.title}</div>
      <div dir="rtl" style={{fontSize:landscape?30:38,lineHeight:1.8,color:"#C5D0DF",
        textAlign:"center",maxWidth:"85%"}}>{scene.body}</div>
    </div>
    <div style={{zIndex:2,width:"100%",minHeight:landscape?105:155,borderRadius:26,
      padding:landscape?"18px 28px":"24px 30px",background:"rgba(5,10,18,.91)",
      border:"1px solid rgba(255,255,255,.16)",boxSizing:"border-box",textAlign:"center",
      display:"flex",alignItems:"center",justifyContent:"center",backdropFilter:"blur(12px)",opacity:captionOpacity}}>
      <WordCaptions scene={scene} frame={frame} landscape={landscape} color={color}/>
    </div>
    <div style={{position:"absolute",bottom:0,left:0,height:8,width:"100%",background:"#FFFFFF18"}}>
      <div style={{height:"100%",width:(((index+(frame/Math.max(1,scene.durationInFrames)))/5)*100)+"%",background:color}}/>
    </div>
  </div>;
};

export const DemoVideo:React.FC<DemoProps>=({scenes})=>{
  let from=0;
  return <div style={{width:"100%",height:"100%",background:"#05070D"}}>
    {scenes.map((scene,index)=>{
      const start=from; from+=scene.durationInFrames;
      return <Sequence key={scene.id} from={start} durationInFrames={scene.durationInFrames}>
        <SceneCard scene={scene} index={index} color={palette[index%palette.length]}/>
        <Audio src={staticFile(scene.audio)}/>
      </Sequence>;
    })}
  </div>;
};
