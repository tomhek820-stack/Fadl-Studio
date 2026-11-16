import json, re, unittest, wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ARABIC=re.compile(r"[\u0600-\u06FF]")
LATIN=re.compile(r"[A-Za-z]")
METADATA=ROOT/"demo/generated/metadata.json"

class DemoScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/"demo/scenes.json").read_text(encoding="utf-8"))
    def test_exactly_five_scenes(self):
        self.assertEqual(len(self.data["scenes"]),5)
    def test_scene_ids_are_unique(self):
        ids=[s["id"] for s in self.data["scenes"]]
        self.assertEqual(len(ids),len(set(ids)))
    def test_scene_fields_are_present(self):
        required={"id","title","body","narration","caption","icon"}
        for scene in self.data["scenes"]:
            self.assertTrue(required.issubset(scene),scene["id"])
    def test_visible_copy_and_captions_are_arabic(self):
        for scene in self.data["scenes"]:
            for field in ("eyebrow","title","body","caption"):
                value=scene[field]
                self.assertRegex(value,ARABIC,scene["id"]+":"+field)
                self.assertIsNone(LATIN.search(value),"Unexpected Latin text: "+scene["id"]+":"+field)
    def test_narration_is_nonempty_and_sentence_sized(self):
        for scene in self.data["scenes"]:
            self.assertGreater(len(scene["narration"].strip()),12)
            self.assertLessEqual(len(scene["narration"]),180)
    def test_pronunciation_dictionary_exists(self):
        self.assertTrue((ROOT/"pronunciation.md").is_file())
    def test_social_video_speed_is_slightly_faster(self):
        self.assertAlmostEqual(self.data["speechSpeed"],1.08,places=2)
    def test_script_has_social_hook_and_follow_call(self):
        combined=" ".join(s["narration"] for s in self.data["scenes"])
        self.assertIn("هل تريد",combined)
        self.assertIn("تابعنا",combined)

    @unittest.skipUnless(METADATA.exists(),"Generated audio is not present; run scripts/generate_demo.py first.")
    def test_generated_wavs_and_word_timings_are_valid(self):
        metadata=json.loads(METADATA.read_text(encoding="utf-8"))
        self.assertEqual(metadata["durationSeconds"],30.0)
        self.assertAlmostEqual(metadata["speechSpeed"],1.08,places=2)
        props=json.loads((ROOT/"demo/generated/props.json").read_text(encoding="utf-8"))
        self.assertEqual(len(props["scenes"]),5)
        for scene in props["scenes"]:
            audio=ROOT/"public/audio"/(scene["id"]+".wav")
            self.assertTrue(audio.is_file(),str(audio))
            with wave.open(str(audio),"rb") as wav:
                duration=wav.getnframes()/wav.getframerate()
            self.assertGreater(duration,0)
            self.assertGreaterEqual(scene["durationInFrames"],scene["audioDurationFrames"])
            timings=scene["wordTimings"]
            self.assertGreater(len(timings),3)
            self.assertEqual(timings[0]["startFrame"],0)
            self.assertEqual(timings[-1]["endFrame"],scene["audioDurationFrames"])
            for previous,current in zip(timings,timings[1:]):
                self.assertEqual(previous["endFrame"],current["startFrame"])
                self.assertGreater(current["endFrame"],current["startFrame"])

if __name__=="__main__":
    unittest.main()
