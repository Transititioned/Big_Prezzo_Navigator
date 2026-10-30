import json
import tempfile
import unittest
from pathlib import Path

from pptx import Presentation

from app import generate_outputs, review_presentation


class GradioWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.source = Path(self.temp.name) / "source.pptx"
        prs = Presentation()
        for title in ("Welcome", "Project plan", "Risks"):
            slide = prs.slides.add_slide(prs.slide_layouts[5])
            slide.shapes.title.text = title
        prs.slides[0].notes_slide.notes_text_frame.text = "Keep my notes."
        prs.save(self.source)
        self.original_bytes = self.source.read_bytes()

    def tearDown(self):
        self.temp.cleanup()

    def test_review_extracts_slides_and_editable_section_rows(self):
        preview, sections, status = review_presentation(str(self.source))
        self.assertEqual(len(preview), 3)
        self.assertEqual(preview[1][1], "Project plan")
        self.assertEqual(sections[0][2], False)
        self.assertIn("3 slides", status)

    def test_edited_boundary_and_name_are_in_generated_deck_and_manifest(self):
        _, sections, _ = review_presentation(str(self.source))
        sections[1][2] = True
        sections[1][3] = "Delivery plan"
        pptx_file, json_file, status = generate_outputs(
            str(self.source), sections, "Board update", "Agree next steps", "Executives")
        pptx_path, manifest_path = Path(pptx_file), Path(json_file)
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertTrue(manifest["slides"][1]["probable_section_boundary"])
            self.assertEqual(manifest["slides"][1]["section"], "Delivery plan")
            self.assertEqual(manifest["presentation_context"]["audience"], "Executives")
            deck = Presentation(pptx_path)
            entry = next(shape for shape in deck.slides[0].shapes if shape.name == "BigPrezo::TocEntry::2")
            self.assertIn("Delivery plan", entry.text)
            self.assertEqual(entry.click_action.target_slide.slide_id,
                             deck.slides[manifest["toc_slide_count"] + 1].slide_id)
            self.assertEqual(deck.slides[manifest["toc_slide_count"]].notes_slide.notes_text_frame.text,
                             "Keep my notes.")
            self.assertIn("not changed", status)
            self.assertEqual(self.source.read_bytes(), self.original_bytes)
        finally:
            pptx_path.unlink(missing_ok=True)
            manifest_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
