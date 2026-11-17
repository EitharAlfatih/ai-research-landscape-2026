"""Offline tests. Run from the repository root with unittest discovery."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from urllib.error import URLError
from urllib.parse import parse_qs, urlsplit
import xml.etree.ElementTree as ET

from arxiv_collection import (
    build_url, fetch_xml, parse_feed, month_ranges, validate_records, collect_month,
)


# Synthetic metadata: no real papers and no network connection needed.
FEED = b'''<feed xmlns="http://www.w3.org/2005/Atom"
    xmlns:arxiv="http://arxiv.org/schemas/atom"
    xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">
  <opensearch:totalResults>100</opensearch:totalResults>
  <entry>
    <id>http://arxiv.org/abs/2201.00001v2</id>
    <title> A title\nwith a line break </title>
    <summary>Abstract with $x$ &amp; symbols.\nSecond line.</summary>
    <published>2022-01-01T12:00:00Z</published>
    <updated>2026-11-01T12:00:00Z</updated>
    <arxiv:primary_category term="q-bio.GN"/>
    <category term="q-bio.GN"/><category term="cs.AI"/>
    <author><name>Author One</name></author>
    <author><name>Author Two</name></author>
  </entry>
  <entry><id>http://arxiv.org/abs/2201.00002v1</id></entry>
</feed>'''


class BuildUrlTests(unittest.TestCase):
    def test_page_offset_is_included(self):
        url = build_url(["cs.AI"], "202201010000", "202201312359", start=500)
        self.assertEqual(parse_qs(urlsplit(url).query)["start"], ["500"])
        with self.assertRaises(ValueError):
            build_url(["cs.AI"], "202201010000", "202201312359", start=-1)

    def test_query_keeps_all_categories_and_exact_date_bounds(self):
        url = build_url(["cs.AI", "cs.LG"], "202201010000", "202610312359", 20)
        parsed = urlsplit(url)
        self.assertEqual((parsed.scheme, parsed.netloc, parsed.path),
                         ("https", "export.arxiv.org", "/api/query"))
        self.assertEqual(parse_qs(parsed.query), {
            "search_query": ["(cat:cs.AI OR cat:cs.LG) AND submittedDate:[202201010000 TO 202610312359]"],
            "start": ["0"], "max_results": ["20"],
            "sortBy": ["submittedDate"], "sortOrder": ["ascending"],
        })

    def test_invalid_settings_raise(self):
        cases = [
            ([], "202201010000", "202610312359", 20),
            (["cs.AI"], "202202300000", "202610312359", 20),
            (["cs.AI"], "2022-01-01", "202610312359", 20),
            (["cs.AI"], "202611010000", "202610312359", 20),
            (["cs.AI"], "202201010000", "202610312359", 0),
        ]
        for settings in cases:
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                build_url(*settings)


class FetchXmlTests(unittest.TestCase):
    @patch("arxiv_collection.urlopen")
    def test_returns_response_bytes_and_closes_response(self, mocked_open):
        response = mocked_open.return_value.__enter__.return_value
        response.read.return_value = FEED
        url = "https://export.arxiv.org/api/query?max_results=20"
        self.assertEqual(fetch_xml(url, timeout=12), FEED)
        args, kwargs = mocked_open.call_args
        self.assertEqual(args[0].full_url, url)
        self.assertEqual(kwargs["timeout"], 12)
        mocked_open.return_value.__exit__.assert_called_once()

    @patch("arxiv_collection.urlopen", side_effect=URLError("connection failed"))
    def test_network_failure_is_not_an_empty_result(self, mocked_open):
        with self.assertRaises(URLError):
            fetch_xml("https://export.arxiv.org/api/query")


class ParseFeedTests(unittest.TestCase):
    def test_preserves_text_dates_cross_listings_and_authors(self):
        result = parse_feed(FEED)
        self.assertEqual(result["total_results"], 100)
        self.assertEqual(len(result["records"]), 2)
        self.assertEqual(result["records"][0], {
            "arxiv_id": "2201.00001v2",
            "title": " A title\nwith a line break ",
            "abstract": "Abstract with $x$ & symbols.\nSecond line.",
            "submitted_at": "2022-01-01T12:00:00Z",
            "updated_at": "2026-11-01T12:00:00Z",
            "primary_category": "q-bio.GN",
            "categories": ["q-bio.GN", "cs.AI"],
            "authors": ["Author One", "Author Two"],
        })

    def test_missing_fields_remain_visible(self):
        record = parse_feed(FEED)["records"][1]
        self.assertEqual(record["arxiv_id"], "2201.00002v1")
        for field in ["title", "abstract", "submitted_at", "updated_at", "primary_category"]:
            self.assertEqual(record[field], "")
        self.assertEqual(record["categories"], [])
        self.assertEqual(record["authors"], [])

    def test_empty_feed_is_an_explicit_empty_result(self):
        xml = '<feed xmlns="http://www.w3.org/2005/Atom"/>'
        self.assertEqual(parse_feed(xml), {"records": [], "total_results": None})

    def test_api_error_raises_instead_of_becoming_a_paper(self):
        for scheme in ["http", "https"]:
            xml = f'''<feed xmlns="http://www.w3.org/2005/Atom"><entry>
                <id>{scheme}://arxiv.org/api/errors#bad_query</id>
                <summary>Invalid query</summary></entry></feed>'''
            with self.subTest(scheme=scheme), self.assertRaisesRegex(RuntimeError, "Invalid query"):
                parse_feed(xml)

    def test_malformed_xml_raises(self):
        with self.assertRaises(ET.ParseError):
            parse_feed("<feed>")

    def test_non_atom_document_raises(self):
        with self.assertRaisesRegex(ValueError, "Atom feed"):
            parse_feed("<html><body>Service unavailable</body></html>")


def sample_record(number, **changes):
    """Synthetic parsed record for testing collection, not a real paper."""
    record = {
        "arxiv_id": f"2201.{number:05d}v1", "title": " Title unchanged ",
        "abstract": "Abstract\nunchanged", "submitted_at": "2022-01-01T00:00:00Z",
        "updated_at": "2026-11-01T00:00:00Z", "primary_category": "cs.LG",
        "categories": ["cs.LG", "cs.AI"], "authors": ["Test Author"],
    }
    record.update(changes)
    return record


class MonthRangeTests(unittest.TestCase):
    def test_year_boundary(self):
        self.assertEqual(month_ranges("2022-12", "2023-01"), [
            ("202212010000", "202212312359"),
            ("202301010000", "202301312359"),
        ])

    def test_leap_year(self):
        self.assertEqual(month_ranges("2024-02", "2024-02"), [
            ("202402010000", "202402292359"),
        ])

    def test_project_period_has_58_months(self):
        ranges = month_ranges("2022-01", "2026-10")
        self.assertEqual(len(ranges), 58)
        self.assertEqual(ranges[0][0], "202201010000")
        self.assertEqual(ranges[-1][1], "202610312359")

    def test_reversed_range_raises(self):
        with self.assertRaises(ValueError):
            month_ranges("2026-10", "2022-01")


class ValidationTests(unittest.TestCase):
    def test_cutoff_includes_last_minute_and_excludes_next_month(self):
        records = [
            sample_record(1, submitted_at="2022-01-31T23:59:59Z"),
            sample_record(2, submitted_at="2022-02-01T00:00:00Z"),
            sample_record(3, submitted_at="not-a-date"),
        ]
        checks = validate_records(records, ["cs.AI"], "202201010000", "202201312359")
        self.assertEqual(checks["outside_date_range"], 1)
        self.assertEqual(checks["invalid_submission_dates"], 1)

    def test_duplicate_versions_missing_ids_and_wrong_category(self):
        records = [sample_record(1), sample_record(1, arxiv_id="2201.00001v2"),
                   sample_record(2, arxiv_id="", categories=["cs.CV"])]
        checks = validate_records(records, ["cs.AI"], "202201010000", "202201312359")
        self.assertEqual(checks["duplicate_ids"], 1)
        self.assertEqual(checks["missing_ids"], 1)
        self.assertEqual(checks["without_requested_category"], 1)


class CollectionTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.folder = Path(directory.name)
        # Patch every network call and delay. The parser is tested separately above.
        for name in ["fetch_xml", "parse_feed", "time.sleep"]:
            patcher = patch("arxiv_collection." + name)
            mocked = patcher.start()
            self.addCleanup(patcher.stop)
            setattr(self, name.split(".")[-1], mocked)

    def collect(self, **changes):
        settings = dict(categories=["cs.AI"], start_date="202201010000",
                        end_date="202201312359", output_dir=self.folder, page_size=2)
        settings.update(changes)
        return collect_month(**settings)

    def test_multiple_pages_are_saved_with_counts_and_provenance(self):
        self.parse_feed.side_effect = [
            {"records": [sample_record(1), sample_record(2)], "total_results": 3},
            {"records": [sample_record(3)], "total_results": 3},
        ]
        manifest = self.collect()
        saved = [json.loads(line) for line in (self.folder / manifest["data_file"]).read_text().splitlines()]
        self.assertEqual(saved, [sample_record(1), sample_record(2), sample_record(3)])
        self.assertEqual(manifest["api_total"], 3)
        self.assertEqual(manifest["retrieved_count"], 3)
        self.assertEqual(manifest["status"], "complete")
        self.assertEqual(manifest["validation"]["duplicate_ids"], 0)
        offsets = [parse_qs(urlsplit(call.args[0]).query)["start"] for call in self.fetch_xml.call_args_list]
        self.assertEqual(offsets, [["0"], ["2"]])
        self.assertEqual(len(manifest["requests"]), 2)
        self.assertEqual(self.sleep.call_count, 2)
        self.sleep.assert_called_with(3)

    def test_incomplete_download_does_not_create_completion_marker(self):
        self.parse_feed.side_effect = [
            {"records": [sample_record(1)], "total_results": 2},
            {"records": [], "total_results": 2},
        ]
        with self.assertRaisesRegex(RuntimeError, "Incomplete download"):
            self.collect()
        self.assertEqual(list(self.folder.glob("*.manifest.json")), [])

    def test_network_failure_does_not_create_completion_marker(self):
        self.fetch_xml.side_effect = URLError("connection failed")
        with self.assertRaises(URLError):
            self.collect()
        self.assertEqual(list(self.folder.glob("*.manifest.json")), [])

    def test_completed_window_is_reused_without_requests(self):
        self.parse_feed.return_value = {"records": [sample_record(1)], "total_results": 1}
        first = self.collect()
        self.fetch_xml.reset_mock()
        self.assertEqual(self.collect(), first)
        self.fetch_xml.assert_not_called()

    def test_changed_saved_file_is_not_reused(self):
        self.parse_feed.return_value = {"records": [sample_record(1)], "total_results": 1}
        manifest = self.collect()
        (self.folder / manifest["data_file"]).write_text("changed")
        with self.assertRaisesRegex(RuntimeError, "missing or changed"):
            self.collect()

    def test_different_categories_do_not_reuse_a_checkpoint(self):
        self.parse_feed.return_value = {"records": [sample_record(1)], "total_results": 1}
        self.collect()
        with self.assertRaisesRegex(RuntimeError, "settings do not match"):
            self.collect(categories=["cs.LG"])

    def test_duplicate_pages_do_not_create_completion_marker(self):
        self.parse_feed.side_effect = [
            {"records": [sample_record(1)], "total_results": 2},
            {"records": [sample_record(1, arxiv_id="2201.00001v2")], "total_results": 2},
        ]
        with self.assertRaisesRegex(RuntimeError, "validation failed"):
            self.collect()
        self.assertEqual(list(self.folder.glob("*.manifest.json")), [])

    def test_changed_api_total_stops_collection(self):
        self.parse_feed.side_effect = [
            {"records": [sample_record(1)], "total_results": 2},
            {"records": [sample_record(2)], "total_results": 3},
        ]
        with self.assertRaisesRegex(RuntimeError, "total changed"):
            self.collect()

    def test_large_window_and_missing_total_raise(self):
        for total in [30001, None]:
            self.parse_feed.return_value = {"records": [], "total_results": total}
            with self.subTest(total=total), self.assertRaises(RuntimeError):
                self.collect()

    def test_zero_match_window_can_complete(self):
        self.parse_feed.return_value = {"records": [], "total_results": 0}
        manifest = self.collect()
        self.assertEqual(manifest["retrieved_count"], 0)
        self.assertEqual((self.folder / manifest["data_file"]).read_bytes(), b"")

    def test_blank_text_is_saved_and_flagged_for_cleaning(self):
        self.parse_feed.return_value = {"records": [sample_record(1, abstract=" ")], "total_results": 1}
        manifest = self.collect()
        self.assertEqual(manifest["validation"]["blank_abstracts"], 1)
        self.assertEqual(json.loads((self.folder / manifest["data_file"]).read_text())["abstract"], " ")


if __name__ == "__main__":
    unittest.main()
