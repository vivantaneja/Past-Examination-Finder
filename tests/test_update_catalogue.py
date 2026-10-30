import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('update_catalogue', Path(__file__).resolve().parents[1] / 'scripts/update_catalogue.py')
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)

# The SEC places controls/download rows in table markup outside the main form.
PAGE = '''<form id="MaterialArchive"></form>
<input type="hidden" name="MaterialArchive__noTable__sbh__SubjectSelect" value="id">
<select name="MaterialArchive__noTable__sbv__SubjectSelect"
 onChange=SubmitForm("111.113.94.102.97.95.112.102");>
<option value="">[Select Subject]</option>
<option value="3" selected>Mathematics</option>
<option value="14">Art &amp; Design</option></select>
<form action="post" name="fileDownload">
<input type='hidden' name='fileid' value='LC003ALP100EV.pdf'>
<tr><td class='materialbody'>Paper One / Higher Level (EV)</td>
<td class='materialbody'><a href=?fp=94.111.96.101 target='_blank'>Click Here</a>
<font class='size'>[475KB]</font></td></tr></form>'''


class ImportTests(unittest.TestCase):
    def test_reads_real_form_structure_and_exact_links(self):
        page = updater.ArchivePage(PAGE)
        self.assertEqual(page.options('SubjectSelect'), [('3', 'Mathematics'), ('14', 'Art & Design')])
        self.assertEqual(page.fields[updater.PREFIX + 'sbv__SubjectSelect'], '3')
        self.assertEqual(page.fields[updater.PREFIX + 'sbh__SubjectSelect'], 'id')
        self.assertEqual(page.actions[updater.PREFIX + 'sbv__SubjectSelect'], '111.113.94.102.97.95.112.102')
        entries = updater.validate_files(page, 'Exam Paper')
        self.assertEqual(entries, [{
            'url': 'LC003ALP100EV.pdf', 'details': 'Paper One / Higher Level (EV)',
            'href': updater.ARCHIVE_URL + '?fp=94.111.96.101', 'type': 'Exam Paper'
        }])

    def test_rejects_error_pages_and_incomplete_rows(self):
        for html in ['<html>Too many requests</html>', PAGE.replace("value='LC003ALP100EV.pdf'", "value=''"), PAGE.replace('</form>', '')]:
            with self.subTest(html=html):
                with self.assertRaises(updater.ArchiveError):
                    updater.validate_files(updater.ArchivePage(html), 'Exam Paper')
        with self.assertRaises(updater.ArchiveError):
            updater.ArchivePage('<html>Service unavailable</html>').options('YearSelect')

    def test_rejects_unexpected_download_hosts(self):
        page = updater.ArchivePage(PAGE.replace('?fp=94.111.96.101', 'https://example.com/paper.pdf'))
        with self.assertRaises(updater.ArchiveError):
            updater.validate_files(page, 'Exam Paper')

    def test_refresh_preserves_historical_years_and_adds_new_subjects(self):
        entry = updater.validate_files(updater.ArchivePage(PAGE), 'Exam Paper')[0]
        existing = {'lc': {'Mathematics': {'2025': [entry]}}, 'jc': {}, 'lb': {}}
        before = copy.deepcopy(existing)
        collected = {'2026': {'lc': {'Mathematics': [entry], 'New subject': [entry]}, 'jc': {}, 'lb': {}}}
        available = {'2026': {'Exam Paper': {'listed': True, 'entries': 2}}}
        result = updater.merge_catalogue(existing, collected, available, '2026-10-30T15:00:00+00:00')
        self.assertEqual(existing, before)
        self.assertEqual(result['lc']['Mathematics']['2025'], [entry])
        self.assertEqual(result['lc']['New subject']['2026'], [entry])
        self.assertEqual(result['_meta']['years']['2026']['materials'], available['2026'])
        again = updater.merge_catalogue(result, collected, available, '2026-10-30T15:00:00+00:00')
        self.assertEqual(result, again)

    def test_empty_year_and_missing_existing_category_do_not_overwrite_data(self):
        with self.assertRaises(updater.ArchiveError):
            updater.merge_catalogue({'lc': {}}, {'2027': {'lc': {}, 'jc': {}, 'lb': {}}}, {'2027': {}}, 'date')
        entry = {'type': 'Marking Scheme'}
        existing = {'lc': {'Mathematics': {'2026': [entry]}}}
        with self.assertRaises(updater.ArchiveError):
            updater.merge_catalogue(existing, {'2026': {'lc': {'Mathematics': [{'type': 'Exam Paper'}]}, 'jc': {}, 'lb': {}}},
                                    {'2026': {'Exam Paper': {'listed': True, 'entries': 1}, 'Marking Scheme': {'listed': False, 'entries': 0}}}, 'date')
        self.assertEqual(existing['lc']['Mathematics']['2026'], [entry])

    def test_atomic_save_writes_valid_json_without_temporary_files(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'data.json'
            updater.save_catalogue(path, {'lc': {'Gaeilge Chumarsáideach': {}}})
            self.assertEqual(json.loads(path.read_text()), {'lc': {'Gaeilge Chumarsáideach': {}}})
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_subject_encoding_repairs_keep_historical_years_together(self):
        catalogue = {'lb': {
            'Gaeilge ChumarsÃ¡ideach': {'2025': [{'url': 'old.pdf'}]},
            'Gaeilge Chumarsáideach': {'2026': [{'url': 'new.pdf'}]}
        }}
        updater.normalize_subjects(catalogue)
        self.assertEqual(list(catalogue['lb']), ['Gaeilge Chumarsáideach'])
        self.assertEqual(set(catalogue['lb']['Gaeilge Chumarsáideach']), {'2025', '2026'})


if __name__ == '__main__':
    unittest.main()
