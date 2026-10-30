import tempfile
import unittest
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches

from big_prezo import extract_manifest_file, process_presentation, probable_section_boundary


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "source.pptx"
        self._make_deck(self.source)

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def _make_deck(path: Path):
        prs = Presentation()
        title_layout = prs.slide_layouts[5]
        blank = prs.slide_layouts[6]
        slide = prs.slides.add_slide(title_layout)
        slide.shapes.title.text = "Quarterly update"
        box = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(5), Inches(1))
        box.text = "Original opening content"
        slide.notes_slide.notes_text_frame.text = "Presenter note: preserve this exactly."

        slide = prs.slides.add_slide(title_layout)
        slide.shapes.title.text = "Part 1 — Delivery"
        box = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(5), Inches(1))
        box.text = "Section divider"

        slide = prs.slides.add_slide(blank)  # intentionally empty / titleless
        slide = prs.slides.add_slide(title_layout)
        slide.shapes.title.text = "Risks and next steps"
        box = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(5), Inches(1))
        box.text = "Detailed original slide text\nwith a second line"
        prs.save(path)

    def test_content_order_and_text_are_preserved(self):
        output = self.root / "navigable.pptx"
        manifest = process_presentation(self.source, output)
        result = Presentation(output)
        source = Presentation(self.source)
        toc_count = manifest["toc_slide_count"]
        self.assertEqual(len(result.slides), len(source.slides) + toc_count)
        for i, original in enumerate(source.slides):
            generated = result.slides[toc_count + i]
            self.assertEqual(
                [s.text for s in generated.shapes if s.has_text_frame and s.text.strip() and not s.name.startswith("BigPrezo::")],
                [s.text for s in original.shapes if s.has_text_frame and s.text.strip()],
            )
        self.assertEqual([r["title"] for r in manifest["slides"]],
                         ["Quarterly update", "Part 1 — Delivery", "", "Risks and next steps"])
        self.assertEqual([r["output_slide_number"] for r in manifest["slides"]],
                         [toc_count + n for n in range(1, 5)])
        self.assertEqual(result.slides[toc_count].notes_slide.notes_text_frame.text,
                         source.slides[0].notes_slide.notes_text_frame.text)

    def test_toc_and_home_links_target_slide_objects(self):
        output = self.root / "linked.pptx"
        manifest = process_presentation(self.source, output)
        result = Presentation(output)
        toc_count = manifest["toc_slide_count"]
        toc_targets = []
        for toc_slide in list(result.slides)[:toc_count]:
            for shape in toc_slide.shapes:
                if shape.name.startswith("BigPrezo::TocEntry::"):
                    toc_targets.append(shape.click_action.target_slide.slide_id)
        content_ids = [slide.slide_id for slide in list(result.slides)[toc_count:]]
        self.assertEqual(toc_targets, content_ids)
        for i, slide in enumerate(list(result.slides)[toc_count:], 1):
            buttons = [s for s in slide.shapes if s.name == f"BigPrezo::Home::{i}"]
            self.assertEqual(len(buttons), 1)
            self.assertEqual(buttons[0].click_action.target_slide.slide_id,
                             result.slides[0].slide_id)

    def test_section_detection_and_no_section_fallback(self):
        self.assertTrue(probable_section_boundary("Part 2 — Delivery", "Part 2 — Delivery | divider"))
        self.assertFalse(probable_section_boundary("Quarterly update", "Quarterly update | five bullets"))
        plain = self.root / "plain.pptx"
        prs = Presentation()
        slide = prs.slides.add_slide(prs.slide_layouts[5])
        slide.shapes.title.text = "Welcome"
        slide = prs.slides.add_slide(prs.slide_layouts[5])
        slide.shapes.title.text = "Metrics"
        prs.save(plain)
        output = self.root / "plain_nav.pptx"
        manifest = process_presentation(plain, output)
        self.assertFalse(any(r["probable_section_boundary"] for r in manifest["slides"]))
        self.assertTrue(manifest["section_detection"]["all_slides_fallback"])
        linked_rows = [s for slide in list(Presentation(output).slides)[:manifest["toc_slide_count"]]
                       for s in slide.shapes if s.name.startswith("BigPrezo::TocEntry::")]
        self.assertEqual(len(linked_rows), 2)

    def test_manifest_command_writes_json_and_creates_parent(self):
        output = self.root / "nested" / "manifest.json"
        manifest = extract_manifest_file(self.source, output)
        self.assertTrue(output.is_file())
        self.assertEqual(manifest["source_slide_count"], 4)

    def test_extract_manifest_omits_generated_contents_and_home_shapes(self):
        generated = self.root / "generated.pptx"
        manifest_path = self.root / "generated_manifest.json"
        process_presentation(self.source, generated)

        manifest = extract_manifest_file(generated, manifest_path)

        self.assertTrue(manifest_path.is_file())
        self.assertEqual(manifest["source_slide_count"], 4)
        self.assertEqual([record["title"] for record in manifest["slides"]],
                         ["Quarterly update", "Part 1 — Delivery", "", "Risks and next steps"])
        extracted_text = " ".join(record["compact_text"] for record in manifest["slides"])
        self.assertNotIn("HOME / TOC", extracted_text)
        self.assertNotIn("Contents", extracted_text)

    def test_rows_per_toc_rejects_invalid_values(self):
        for value in (0, -1, 1.5, "3", True, None):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "rows_per_toc must be a positive integer"):
                    process_presentation(self.source, self.root / "invalid.pptx",
                                         rows_per_toc=value)

    def test_reprocessing_does_not_accumulate_navigation(self):
        first = self.root / "first.pptx"
        second = self.root / "second.pptx"
        first_manifest = process_presentation(self.source, first)
        second_manifest = process_presentation(first, second)
        self.assertEqual(second_manifest["source_slide_count"], 4)
        self.assertEqual(second_manifest["toc_slide_count"], first_manifest["toc_slide_count"])
        output = Presentation(second)
        self.assertEqual(len(output.slides), 4 + second_manifest["toc_slide_count"])
        home_shapes = [shape for slide in output.slides for shape in slide.shapes
                       if shape.name.startswith("BigPrezo::Home::")]
        self.assertEqual(len(home_shapes), 4)
        self.assertEqual(sum(any(s.name == "BigPrezo::GeneratedToc" for s in slide.shapes)
                             for slide in output.slides), second_manifest["toc_slide_count"])

    def test_multiple_contents_pages_link_to_each_other(self):
        output = self.root / "paged.pptx"
        manifest = process_presentation(self.source, output, rows_per_toc=2)
        result = Presentation(output)
        self.assertEqual(manifest["toc_slide_count"], 2)
        first, second = list(result.slides)[:2]
        next_link = next(s for s in first.shapes if s.name == "BigPrezo::TocNext")
        previous_link = next(s for s in second.shapes if s.name == "BigPrezo::TocPrevious")
        self.assertEqual(next_link.click_action.target_slide.slide_id, second.slide_id)
        self.assertEqual(previous_link.click_action.target_slide.slide_id, first.slide_id)

    def test_empty_and_title_only_slides_are_safe(self):
        odd = self.root / "odd.pptx"
        prs = Presentation()
        prs.slides.add_slide(prs.slide_layouts[6])
        slide = prs.slides.add_slide(prs.slide_layouts[5])
        slide.shapes.title.text = "Appendix"
        prs.save(odd)
        output = self.root / "odd_nav.pptx"
        manifest = process_presentation(odd, output)
        self.assertEqual(manifest["source_slide_count"], 2)
        self.assertEqual(manifest["slides"][0]["title"], "")
        self.assertTrue(manifest["slides"][1]["probable_section_boundary"])
        self.assertEqual(len(Presentation(output).slides), 3)


if __name__ == "__main__":
    unittest.main()
