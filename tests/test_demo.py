import json, re, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ARABIC=re.compile(r"[\u0600-\u06FF]")
LATIN=re.compile(r"[A-Za-z]")
DIACRITICS=re.compile(r"[\u064B-\u065F\u0670]")
METADATA=ROOT/"demo/generated/metadata.json"

class DemoScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/"demo/scenes.json").read_text(encoding="utf-8"))
    def test_no_literal_escaped_newline_corruption(self):
        build=(ROOT/"scripts/build_demo.py").read_text(encoding="utf-8")
        video=(ROOT/"src/DemoVideo.tsx").read_text(encoding="utf-8")
        readme=(ROOT/"README.md").read_text(encoding="utf-8")
        self.assertNotIn("\\n    run(",build)
        self.assertNotIn("\\n    <",video)
        self.assertNotIn("\\n-",readme)

    def test_exactly_five_scenes(self):
        self.assertEqual(len(self.data["scenes"]),5)
    def test_scene_ids_are_unique(self):
        ids=[s["id"] for s in self.data["scenes"]]
        self.assertEqual(len(ids),len(set(ids)))
    def test_scene_fields_are_present(self):
        required={"id","eyebrow","title","body","narration","caption","icon","visual"}
        for scene in self.data["scenes"]:
            self.assertTrue(required.issubset(scene),scene["id"])
    def test_visible_copy_and_captions_are_arabic(self):
        for scene in self.data["scenes"]:
            for field in ("eyebrow","title","body","caption"):
                value=scene[field]
                self.assertRegex(value,ARABIC,scene["id"]+":"+field)
                self.assertIsNone(LATIN.search(value),"Unexpected Latin text: "+scene["id"]+":"+field)
    def test_narration_and_captions_are_fully_vocalized(self):
        for scene in self.data["scenes"]:
            for field in ("narration","caption","title","body","eyebrow"):
                words=re.findall(r"[\u0621-\u064A\u0671-\u0673][\u0621-\u064A\u0671-\u0673\u064B-\u065F\u0670]*",scene[field])
                self.assertTrue(words,scene["id"]+":"+field)
                missing=[word for word in words if not DIACRITICS.search(word)]
                self.assertEqual(missing,[],scene["id"]+":"+field+" has unvocalized words")
            self.assertEqual(scene["narration"],scene["caption"],scene["id"])
    def test_narration_is_nonempty_and_sentence_sized(self):
        for scene in self.data["scenes"]:
            self.assertGreater(len(scene["narration"].strip()),8)
            self.assertLessEqual(len(scene["narration"]),180)
    def test_pronunciation_dictionary_exists(self):
        self.assertTrue((ROOT/"pronunciation.md").is_file())
    def test_no_artificial_speedup(self):
        self.assertEqual(self.data["speechSpeed"],1.0)
    def test_each_scene_has_unique_art_direction(self):
        self.assertTrue(self.data.get("visualIdentity"))
        scenes=self.data["scenes"]
        self.assertEqual(len({s["icon"] for s in scenes}),len(scenes))
        self.assertEqual(len({s["visual"]["background"] for s in scenes}),len(scenes))
        self.assertEqual(len({s["visual"]["accent"] for s in scenes}),len(scenes))
        self.assertEqual(len({s["visual"]["motif"] for s in scenes}),len(scenes))
        allowed={"grid","dots","diagonal","rings","circuit"}
        for scene in scenes:
            visual=scene["visual"]
            self.assertIn(visual["motif"],allowed)
            self.assertRegex(visual["accent"],r"^#[0-9A-Fa-f]{6}$")
    def test_social_hook_and_follow_call(self):
        combined=" ".join(s["narration"] for s in self.data["scenes"])
        self.assertIn("هَلْ تَعْرِفُ مَنْ",combined)
        self.assertIn("أَبُو مُحَمَّدْ. تِكْ",combined)
        self.assertRegex(combined,r"أَبُو مُحَمَّدْ[.،؛…]+\\s*تِكْ[.،؛!?؟]")
        self.assertNotIn("خَمْسُ عَادَاتٍ لِهَاتِفٍ أَسْرَعَ",combined)
    def test_edge_retry_and_fallback_are_documented_in_engine(self):
        engine=(ROOT/"scripts/generate_demo.py").read_text(encoding="utf-8")
        self.assertIn("EDGE_RETRIES",engine)
        self.assertIn("synthesize_piper",engine)
        self.assertIn("switching to Piper fallback",engine)
    @unittest.skipUnless(METADATA.exists(),"Generated audio is not present; run scripts/generate_demo.py first.")
    def test_one_continuous_audio_track_and_valid_word_timings(self):
        metadata=json.loads(METADATA.read_text(encoding="utf-8"))
        props=json.loads((ROOT/"demo/generated/props.json").read_text(encoding="utf-8"))
        self.assertEqual(props["audio"],"audio/narration.wav")
        audio=ROOT/"public/audio/narration.wav"
        self.assertTrue(audio.is_file())
        self.assertGreater(audio.stat().st_size,2048)
        self.assertGreater(metadata["audioDurationSeconds"],0)
        self.assertLessEqual(metadata["audioDurationSeconds"],60)
        self.assertEqual(metadata["synthesisMode"],"single continuous narration track")
        self.assertEqual(len(props["scenes"]),5)
        for scene in props["scenes"]:
            timings=scene["wordTimings"]
            self.assertGreater(len(timings),2)
            self.assertEqual(timings[0]["startFrame"],0)
            self.assertEqual(timings[-1]["endFrame"],scene["audioDurationFrames"])
            for previous,current in zip(timings,timings[1:]):
                self.assertEqual(previous["endFrame"],current["startFrame"])
                self.assertGreater(current["endFrame"],current["startFrame"])

if __name__=="__main__":
    unittest.main()
