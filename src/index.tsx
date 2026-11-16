import React from "react";
import {Composition, registerRoot} from "remotion";
import {DemoVideo, type DemoProps} from "./DemoVideo";
import source from "../demo/scenes.json";

const defaultProps: DemoProps = {
  title: source.title,
  scenes: source.scenes.map((scene) => ({
    ...scene,
    audio: "audio/" + scene.id + ".wav",
    durationInFrames: 180,
    audioDurationFrames: 168,
    wordTimings: scene.caption.split(/\s+/).map((text,index,words) => ({
      text,
      startFrame: Math.floor(index * 168 / words.length),
      endFrame: Math.floor((index + 1) * 168 / words.length),
    })),
  })),
};
const getDuration = (props: DemoProps) =>
  Math.max(1, props.scenes.reduce((sum, scene) => sum + scene.durationInFrames, 0));

const Root: React.FC = () => (
  <>
    <Composition id="DemoVertical" component={DemoVideo} width={1080} height={1920} fps={30}
      durationInFrames={getDuration(defaultProps)} defaultProps={defaultProps}
      calculateMetadata={({props}) => ({durationInFrames: getDuration(props as DemoProps)})} />
    <Composition id="DemoLandscape" component={DemoVideo} width={1920} height={1080} fps={30}
      durationInFrames={getDuration(defaultProps)} defaultProps={defaultProps}
      calculateMetadata={({props}) => ({durationInFrames: getDuration(props as DemoProps)})} />
    <Composition id="DemoSquare" component={DemoVideo} width={1080} height={1080} fps={30}
      durationInFrames={getDuration(defaultProps)} defaultProps={defaultProps}
      calculateMetadata={({props}) => ({durationInFrames: getDuration(props as DemoProps)})} />
    <Composition id="DemoPortrait" component={DemoVideo} width={1080} height={1350} fps={30}
      durationInFrames={getDuration(defaultProps)} defaultProps={defaultProps}
      calculateMetadata={({props}) => ({durationInFrames: getDuration(props as DemoProps)})} />
  </>
);
registerRoot(Root);
