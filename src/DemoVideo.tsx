import React from "react";
import {Audio, Img, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig} from "remotion";
import "@fontsource/noto-sans-arabic/400.css";
import "@fontsource/noto-sans-arabic/600.css";
import "@fontsource/noto-sans-arabic/800.css";

type WordTiming = {text:string; startFrame:number; endFrame:number};
type VisualElement = {label:string; icon:string; image?:string; detail?:string};
type Scene = {
  id:string; eyebrow:string; title:string; body:string; narration:string;
  caption:string; icon:string;
  visual:{background:string;accent:string;motif:string;photo?:string;photoQuery?:string;subject:VisualElement;elements?:VisualElement[]};
  durationInFrames:number; audioDurationFrames:number; wordTimings:WordTiming[];
};
export type DemoProps = {title:string; audio:string; scenes:Scene[]};
const sceneNumbers=["٠١","٠٢","٠٣","٠٤","٠٥"];

const iconFiles:Record<string,string>={
  shield:"shield-check","refresh-cw":"refresh-cw",sliders:"sliders-horizontal",lock:"lock-keyhole",
  cloud:"cloud-upload",spark:"sparkles",script:"file-text",audio:"audio-lines",captions:"captions",
  export:"upload","hard-drive":"hard-drive","app-window":"app-window","trash-2":"trash-2",
  camera:"camera",mic:"mic",map:"map-pin",settings:"settings-2",smartphone:"smartphone",
  flashlight:"flashlight","contact-round":"contact-round",shieldCheck:"shield-check",
};
const motifStyle=(motif:string,color:string):React.CSSProperties=>{
  const soft=color+"24";
  const patterns:Record<string,string>={
    grid:`linear-gradient(${soft} 1px, transparent 1px),linear-gradient(90deg,${soft} 1px,transparent 1px)`,
    dots:`radial-gradient(${soft} 1.6px,transparent 1.6px)`,
    diagonal:`repeating-linear-gradient(135deg,${soft} 0 1px,transparent 1px 24px)`,
    rings:`repeating-radial-gradient(circle at 50% 50%,${soft} 0 1px,transparent 1px 34px)`,
    circuit:`linear-gradient(${soft} 1px,transparent 1px),linear-gradient(90deg,${soft} 1px,transparent 1px),radial-gradient(circle at 25% 25%,${soft} 0 3px,transparent 4px)`,
  };
  return {position:"absolute",inset:0,opacity:0.8,backgroundImage:patterns[motif]??patterns.grid,
    backgroundSize:motif==="dots"?"28px 28px":motif==="circuit"?"54px 54px,54px 54px,108px 108px":motif==="grid"?"66px 66px":"auto"};
};

const Icon:React.FC<{name:string}>=({name})=>{
  const file=iconFiles[name]??name;
  return <Img src={staticFile("icons/"+file+".svg")} style={{width:"100%",height:"100%",objectFit:"contain"}}/>;
};

const VisualSubject:React.FC<{item:VisualElement;color:string;compact?:boolean}>=({item,color,compact=false})=>{
  const size=compact?52:150;
  return <div style={{display:"flex",alignItems:"center",justifyContent:"center",gap:compact?12:20,
    flexDirection:compact?"row":"column",padding:compact?"10px 16px":"20px 28px",minWidth:compact?150:220,
    borderRadius:compact?18:30,background:"linear-gradient(145deg,rgba(7,12,22,.82),rgba(7,12,22,.58))",
    border:"1px solid "+color+"88",boxShadow:"0 12px 45px "+color+"22",backdropFilter:"blur(12px)"}}>
    <div style={{width:size,height:size,flexShrink:0,padding:compact?8:18,boxSizing:"border-box",
      borderRadius:compact?14:26,background:color+"18",border:"1px solid "+color+"55"}}>
      {item.image
        ? <Img src={staticFile(item.image)} style={{width:"100%",height:"100%",objectFit:"contain"}}/>
        : <Icon name={item.icon}/>}
    </div>
    <div dir="rtl" style={{textAlign:compact?"right":"center",maxWidth:compact?180:360}}>
      <div style={{fontSize:compact?23:34,fontWeight:800,color:"#FFFFFF"}}>{item.label}</div>
      {item.detail&&<div style={{fontSize:compact?16:22,lineHeight:1.5,color:"#C5D0DF",marginTop:6}}>{item.detail}</div>}
    </div>
  </div>;
};

const WordCaptions:React.FC<{scene:Scene;frame:number;landscape:boolean;color:string}>=({scene,frame,landscape,color})=>{
  const active=scene.wordTimings.findIndex(w=>frame>=w.startFrame&&frame<w.endFrame);
  return <div dir="rtl" style={{display:"flex",flexDirection:"row-reverse",flexWrap:"wrap",justifyContent:"center",alignItems:"center",
    columnGap:landscape?12:16,rowGap:landscape?9:12}}>
    {scene.wordTimings.map((word,index)=>{
      const highlighted=index===active;
      return <span key={index} dir="rtl" style={{fontSize:landscape?27:37,lineHeight:1.7,fontWeight:800,
        color:highlighted?"#07111D":"#F4F7FC",background:highlighted?color:"transparent",opacity:index<=active?1:0,
        borderRadius:9,padding:highlighted?"0px 8px":"0px 2px",textShadow:highlighted?"none":"0 2px 10px #0008",transition:"none"}}>
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
  const progress=Math.min(1,frame/Math.max(1,scene.durationInFrames-1));
  const photoScale=1.04+progress*0.16;
  const photoX=(index%2===0?-1:1)*progress*1.8;
  const photoY=(index%2===0?1:-1)*progress*1.2;
  const elements=scene.visual.elements??[];
  return <div style={{width:"100%",height:"100%",position:"relative",overflow:"hidden",background:scene.visual.background,
    color:"#F4F7FC",fontFamily:"'Noto Sans Arabic', sans-serif",display:"flex",flexDirection:"column",
    alignItems:"center",justifyContent:landscape?"center":"space-between",padding:landscape?"7% 10%":"10% 8%",
    boxSizing:"border-box",direction:"rtl"}}>
    {scene.visual.photo&&<Img src={staticFile(scene.visual.photo)} style={{position:"absolute",inset:"-7%",width:"114%",height:"114%",objectFit:"cover",transform:`scale(${photoScale}) translate(${photoX}%,${photoY}%)`,filter:"saturate(.88) contrast(1.06)",opacity:.54}}/>}
    <div style={{position:"absolute",inset:0,background:"linear-gradient(180deg,rgba(3,7,14,.58),rgba(3,7,14,.36) 42%,rgba(3,7,14,.88))"}}/>
    <div style={motifStyle(scene.visual.motif,color)}/>
    <Img src={staticFile("icons/hexagon.svg")} style={{position:"absolute",width:"34%",height:"34%",right:"-8%",top:"17%",opacity:0.07,filter:"drop-shadow(0 0 18px "+color+")"}}/>
    <Img src={staticFile("icons/orbit.svg")} style={{position:"absolute",width:"30%",height:"30%",left:"-8%",bottom:"18%",opacity:0.06}}/>
    <div style={{position:"absolute",width:"72%",height:"38%",top:"-14%",left:"14%",borderRadius:"50%",background:color,filter:"blur(130px)",opacity:0.22}}/>
    <div style={{zIndex:1,width:"100%",display:"flex",justifyContent:"space-between",alignItems:"center"}}>
      <div style={{fontSize:landscape?25:30,fontWeight:800}}>أبو محمد تك</div>
      <div dir="ltr" style={{fontSize:landscape?20:24,color:"#9CAEC4"}}>{sceneNumbers[index]} / ٠٥</div>
    </div>
    <div style={{zIndex:1,width:"100%",display:"flex",flex:1,flexDirection:"column",alignItems:"center",
      justifyContent:"center",gap:landscape?18:24,transform:"translateY("+translate+"px) scale("+scale+")",opacity:enter}}>
      <VisualSubject item={scene.visual.subject} color={color}/>
      {elements.length>0&&<div style={{display:"flex",flexWrap:"wrap",justifyContent:"center",gap:12,maxWidth:"100%"}}>
        {elements.slice(0,3).map((item,i)=><VisualSubject key={item.label+"-"+i} item={item} color={color} compact/>)}
      </div>}
      <div dir="rtl" style={{fontSize:landscape?25:34,color,fontWeight:600,textAlign:"center"}}>{scene.eyebrow}</div>
      <div dir="rtl" style={{fontSize:landscape?64:76,fontWeight:800,lineHeight:1.35,textAlign:"center",maxWidth:"92%",textShadow:"0 8px 35px #0008"}}>{scene.title}</div>
      <div dir="rtl" style={{fontSize:landscape?30:38,lineHeight:1.8,color:"#C5D0DF",textAlign:"center",maxWidth:"85%"}}>{scene.body}</div>
    </div>
    <div style={{zIndex:2,width:"100%",minHeight:landscape?105:155,borderRadius:26,padding:landscape?"18px 28px":"24px 30px",
      background:"rgba(5,10,18,.91)",border:"1px solid rgba(255,255,255,.16)",boxSizing:"border-box",textAlign:"center",
      display:"flex",alignItems:"center",justifyContent:"center",backdropFilter:"blur(12px)",opacity:captionOpacity}}>
      <WordCaptions scene={scene} frame={frame} landscape={landscape} color={color}/>
    </div>
    <div style={{position:"absolute",bottom:0,left:0,height:8,width:"100%",background:"#FFFFFF18"}}>
      <div style={{height:"100%",width:(((index+(frame/Math.max(1,scene.durationInFrames)))/5)*100)+"%",background:color}}/>
    </div>
  </div>;
};

export const DemoVideo:React.FC<DemoProps>=({scenes,audio})=>{
  let from=0;
  return <div style={{width:"100%",height:"100%",background:"#05070D"}}>
    <Audio src={staticFile(audio)}/>
    {scenes.map((scene,index)=>{
      const start=from; from+=scene.durationInFrames;
      return <Sequence key={scene.id} from={start} durationInFrames={scene.durationInFrames}>
        <SceneCard scene={scene} index={index} color={scene.visual.accent}/>
      </Sequence>;
    })}
  </div>;
};
