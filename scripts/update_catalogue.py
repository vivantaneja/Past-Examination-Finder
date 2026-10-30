#!/usr/bin/env python3
"""Refresh selected years from the SEC's published archive (Python 3 + curl)."""

import argparse
import copy
import datetime
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode, urljoin, urlsplit

ARCHIVE_URL = 'https://www.examinations.ie/exammaterialarchive/'
TERMS_URL = 'https://www.examinations.ie/TermsConditions.html'
PREFIX = 'MaterialArchive__noTable__'
MATERIAL_TYPES = {
    'exampapers': 'Exam Paper',
    'markingschemes': 'Marking Scheme',
    'deferredexams': 'Deferred Exam Paper',
    'deferredmarkingschemes': 'Deferred Marking Scheme',
}
COURSES = {'lc', 'jc', 'lb'}
ROOT = Path(__file__).resolve().parents[1]


class ArchiveError(Exception):
    pass


class ArchivePage(HTMLParser):
    """Read the legacy HTML form, including controls outside the form element."""

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.fields = {}
        self.actions = {}
        self.selects = {}
        self.files = []
        self.select = None
        self.option = None
        self.file = None
        self.details = False
        self.file_count = 0
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        name = attrs.get('name', '')
        if name.startswith(PREFIX):
            if tag == 'input':
                self.fields[name] = attrs.get('value', '')
            action = attrs.get('onchange', attrs.get('onclick', ''))
            match = re.search(r'SubmitForm\(["\']([\d.]+)["\']\)', action)
            if match:
                self.actions[name] = match.group(1)
        if tag == 'select' and name.startswith(PREFIX):
            self.select = name
            self.selects[name] = []
            self.fields[name] = ''
        elif tag == 'option' and self.select:
            self.option = {'value': attrs.get('value', ''), 'text': []}
            if 'selected' in attrs:
                self.fields[self.select] = self.option['value']
        elif tag == 'form' and name == 'fileDownload':
            self.file = {'details': [], 'url': '', 'href': ''}
            self.file_count += 1
        elif self.file is not None:
            if tag == 'input' and name == 'fileid':
                self.file['url'] = attrs.get('value', '')
            elif tag == 'td':
                self.details = attrs.get('class') == 'materialbody' and not self.file['details']
            elif tag == 'a' and 'href' in attrs:
                self.file['href'] = urljoin(ARCHIVE_URL, attrs['href'])

    def handle_data(self, text):
        if self.option is not None:
            self.option['text'].append(text)
        if self.file is not None and self.details:
            self.file['details'].append(text)

    def handle_endtag(self, tag):
        if tag == 'option' and self.option is not None:
            self.selects[self.select].append((
                self.option['value'], ' '.join(''.join(self.option['text']).split())))
            self.option = None
        elif tag == 'select':
            self.select = None
        elif tag == 'td':
            self.details = False
        elif tag == 'form' and self.file is not None:
            self.file['details'] = ' '.join(''.join(self.file['details']).split())
            self.files.append(self.file)
            self.file = None

    def options(self, field):
        key = PREFIX + 'sbv__' + field
        if key not in self.selects:
            raise ArchiveError('Archive did not return the expected ' + field + ' selector.')
        return [(value, label) for value, label in self.selects[key] if value]


class ArchiveClient:
    def __init__(self, delay=1.0, cache_dir=None):
        self.delay = delay
        self.last_request = 0
        self.cache_dir = cache_dir
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch(self, url=ARCHIVE_URL, fields=None):
        cache_path = None
        if self.cache_dir:
            # The numeric action tokens vary; the posted selections identify a page.
            key = json.dumps(fields, sort_keys=True).encode('utf-8')
            cache_path = self.cache_dir / (hashlib.sha256(key).hexdigest() + '.html')
            if cache_path.exists():
                return ArchivePage(cache_path.read_text(encoding='utf-8'))
        time.sleep(max(0, self.delay - (time.monotonic() - self.last_request)))
        command = ['curl', '--silent', '--show-error', '--fail', '--location',
                   '--proto', '=https', '--proto-redir', '=https', '--max-time', '60',
                   '--retry', '2']
        if fields is not None:
            command += ['--data', urlencode(fields)]
        try:
            result = subprocess.run(command + [url], check=True, capture_output=True)
        except (OSError, subprocess.CalledProcessError) as exc:
            reason = exc.stderr.decode('utf-8', errors='replace').strip() if isinstance(exc, subprocess.CalledProcessError) else str(exc)
            raise ArchiveError('Could not retrieve the SEC archive. Existing data is unchanged. ' + reason) from exc
        self.last_request = time.monotonic()
        # The SEC advertises Latin-1 but some catalogue pages contain UTF-8 names.
        try:
            html = result.stdout.decode('utf-8')
        except UnicodeDecodeError:
            html = result.stdout.decode('iso-8859-1')
        page = ArchivePage(html)
        if not page.actions:
            raise ArchiveError('The SEC returned an unexpected page. Existing data is unchanged.')
        if cache_path:
            cache_path.write_text(html, encoding='utf-8')
        return page

    def accept_terms(self):
        page = self.fetch()
        key = PREFIX + 'cbv__AgreeCheck'
        if key not in page.actions:
            raise ArchiveError('Archive terms form was not found.')
        fields = dict(page.fields)
        fields[key] = 'Y'
        return self.fetch(ARCHIVE_URL + '?i=' + page.actions[key], fields)

    def choose(self, page, field, value):
        key = PREFIX + 'sbv__' + field
        if value not in dict(page.options(field)) or key not in page.actions:
            raise ArchiveError('Archive option is not available: ' + field + '=' + value)
        fields = dict(page.fields)
        fields[key] = value
        result = self.fetch(ARCHIVE_URL + '?i=' + page.actions[key], fields)
        if result.fields.get(key) != value:
            raise ArchiveError('Archive did not retain the selected ' + field + '.')
        return result


def validate_files(page, material_type):
    if not page.files or page.file_count != len(page.files):
        raise ArchiveError('An advertised subject returned no complete download rows.')
    entries = []
    seen = set()
    for file in page.files:
        parsed = urlsplit(file['href'])
        if (not file['url'] or not file['details'] or parsed.scheme != 'https'
                or parsed.netloc != 'www.examinations.ie'
                or not (parsed.path.startswith('/archive/') or
                        (parsed.path == '/exammaterialarchive/' and parsed.query.startswith('fp=')))):
            raise ArchiveError('Unexpected download row; refusing to save an incomplete catalogue.')
        key = (file['url'], material_type)
        if key not in seen:
            entries.append(dict(file, type=material_type))
            seen.add(key)
    return entries


def collect(client, years):
    accepted = client.accept_terms()
    offered_types = dict(accepted.options('ViewType'))
    if set(offered_types) != set(MATERIAL_TYPES):
        raise ArchiveError('The SEC material types changed; update the importer before refreshing.')
    collected = {year: {course: {} for course in sorted(COURSES)} for year in years}
    availability = {year: {} for year in years}
    for archive_type, label in MATERIAL_TYPES.items():
        type_page = client.choose(accepted, 'ViewType', archive_type)
        offered_years = dict(type_page.options('YearSelect'))
        for year in years:
            if year not in offered_years:
                availability[year][label] = {'listed': False, 'entries': 0}
                continue
            year_page = client.choose(type_page, 'YearSelect', year)
            total = 0
            for course, _ in year_page.options('ExaminationSelect'):
                if course not in COURSES:
                    raise ArchiveError('Unexpected examination code: ' + course)
                course_page = client.choose(year_page, 'ExaminationSelect', course)
                for subject_code, subject in course_page.options('SubjectSelect'):
                    subject_page = client.choose(course_page, 'SubjectSelect', subject_code)
                    entries = validate_files(subject_page, label)
                    collected[year][course].setdefault(subject, []).extend(entries)
                    total += len(entries)
                    print(f'{year} {course} {label}: {subject} ({len(entries)})', flush=True)
            availability[year][label] = {'listed': True, 'entries': total}
    return collected, availability


def normalize_subjects(catalogue):
    # Repair names in the original Latin-1-decoded snapshot so a new UTF-8 name
    # does not split the same subject into separate historical/current filters.
    for course in COURSES:
        subjects = catalogue.setdefault(course, {})
        normalized = {}
        for subject, years in subjects.items():
            try:
                corrected = subject.encode('iso-8859-1').decode('utf-8')
            except (UnicodeEncodeError, UnicodeDecodeError):
                corrected = subject
            if corrected not in normalized:
                normalized[corrected] = {year: list(entries) for year, entries in years.items()}
                continue
            target = normalized[corrected]
            for year, entries in years.items():
                combined = target.setdefault(year, [])
                combined.extend(entry for entry in entries if entry not in combined)
        catalogue[course] = normalized


def merge_catalogue(existing, collected, availability, checked_at):
    result = copy.deepcopy(existing)
    normalize_subjects(result)
    for year, courses in collected.items():
        # Never erase an existing year because a remote category was missing/empty.
        # A successful full-year refresh replaces only that year's entries.
        count = sum(len(entries) for subjects in courses.values() for entries in subjects.values())
        if not count:
            raise ArchiveError(f'No materials are currently listed for {year}; existing data is unchanged.')
        for course in COURSES:
            subjects = result.setdefault(course, {})
            for subject in list(subjects):
                old = subjects[subject].get(year, [])
                for entry in old:
                    status = availability[year].get(entry['type'], {})
                    if not status.get('listed') or not status.get('entries'):
                        raise ArchiveError(f'{year} {entry["type"]} disappeared; existing data is unchanged.')
                subjects[subject].pop(year, None)
                if not subjects[subject]:
                    del subjects[subject]
            for subject, entries in courses[course].items():
                subjects.setdefault(subject, {})[year] = entries
    metadata = result.setdefault('_meta', {})
    metadata['source'] = ARCHIVE_URL
    metadata.setdefault('years', {}).update({
        year: {'checkedAt': checked_at, 'materials': availability[year]} for year in collected
    })
    return result


def save_catalogue(path, catalogue):
    # Do not touch the working snapshot unless every requested page was parsed.
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent,
                                         prefix='.catalogue-', suffix='.json', delete=False) as output:
            temp_path = Path(output.name)
            json.dump(catalogue, output, ensure_ascii=False, indent=2)
            output.write('\n')
        temp_path.chmod(path.stat().st_mode & 0o777 if path.exists() else 0o644)
        temp_path.replace(path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--year', action='append', required=True, help='Year to refresh; repeat for multiple years.')
    parser.add_argument('--accept-terms', action='store_true', help='Accept the SEC archive terms: ' + TERMS_URL)
    parser.add_argument('--data', type=Path, default=ROOT / 'data.json')
    parser.add_argument('--cache-dir', type=Path, help='Optional response cache for resuming this import; use a fresh directory for a new refresh.')
    parser.add_argument('--delay', type=float, default=1.0, help='Minimum seconds between requests (default: 1).')
    args = parser.parse_args()
    if not args.accept_terms:
        parser.error('Read ' + TERMS_URL + ' and supply --accept-terms to use the archive.')
    if any(not re.fullmatch(r'\d{4}', year) for year in args.year) or args.delay < 0:
        parser.error('Use four-digit years and a non-negative request delay.')
    try:
        existing = json.loads(args.data.read_text(encoding='utf-8'))
        collected, availability = collect(ArchiveClient(args.delay, args.cache_dir), sorted(set(args.year)))
        checked_at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
        catalogue = merge_catalogue(existing, collected, availability, checked_at)
        save_catalogue(args.data, catalogue)
    except (ArchiveError, OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    count = sum(status['entries'] for types in availability.values() for status in types.values())
    print(f'Saved {count} official entries for {", ".join(sorted(collected))} to {args.data}.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
