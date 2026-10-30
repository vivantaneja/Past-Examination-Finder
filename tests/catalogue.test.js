const test = require('node:test');
const assert = require('node:assert/strict');
const catalogue = require('../catalogue.js');
const data = require('../data.json');

test('2026 contains official papers and schemes for all three examinations', function () {
  const counts = {};
  for (const course of ['lc', 'jc', 'lb']) {
    const entries = Object.values(data[course]).flatMap(function (years) { return years['2026'] || []; });
    assert.ok(entries.some(function (entry) { return entry.type === 'Exam Paper'; }), course);
    assert.ok(entries.some(function (entry) { return entry.type === 'Marking Scheme'; }), course);
    entries.forEach(function (entry) {
      assert.ok(entry.href.startsWith('https://www.examinations.ie/'), entry.url);
      counts[entry.type] = (counts[entry.type] || 0) + 1;
    });
  }
  for (const [type, status] of Object.entries(data._meta.years['2026'].materials)) {
    assert.equal(counts[type] || 0, status.entries, type);
    if (!status.listed) assert.equal(counts[type] || 0, 0, type);
  }
});

test('legacy deferred papers, schemes and audio use their actual archive folders', function () {
  const cases = [
    ['Exam Paper', 'exampapers'], ['Marking Scheme', 'markingschemes'],
    ['Deferred Exam Paper', 'deferredexams'], ['Deferred Marking Scheme', 'deferredmarkingschemes']
  ];
  cases.forEach(function ([type, folder]) {
    const entry = { type, url: 'LC003ALP000EV.pdf', details: 'Higher Level (EV)' };
    assert.equal(catalogue.buildPaperUrl('2025', entry), 'https://www.examinations.ie/archive/' + folder + '/2025/LC003ALP000EV.pdf');
  });
  const audio = { type: 'Deferred Exam Paper', url: 'LC001ZLP017IV.mp3', details: 'Sound File (IV)' };
  assert.equal(catalogue.classifyMaterialType(audio), 'Deferred Audio');
  assert.match(catalogue.buildPaperUrl('2026', audio), /\/deferredexams\/2026\//);
});

test('published download links take precedence over reconstructed filenames', function () {
  const href = 'https://www.examinations.ie/exammaterialarchive/?fp=94.111.96.101';
  assert.equal(catalogue.buildPaperUrl('2026', { href, url: 'paper.pdf', type: 'Exam Paper' }), href);
  assert.equal(catalogue.buildPaperUrl('2026', { href: 'https://example.com/paper.pdf' }), null);
  assert.equal(catalogue.buildPaperUrl('2026', { href: 'javascript:alert(1)' }), null);
});

test('shared audio is accessible with higher and ordinary papers', function () {
  const entries = [
    { details: 'Higher Level (IV)', url: 'LC001ALP000IV.pdf', type: 'Exam Paper' },
    { details: 'Ordinary Level (IV)', url: 'LC001GLP000IV.pdf', type: 'Exam Paper' },
    { details: 'Sound File (IV)', url: 'LC001ZLP017IV.mp3', type: 'Exam Paper' }
  ];
  for (const level of ['Higher', 'Ordinary']) {
    assert.equal(catalogue.filterEntriesByLevel(entries, level).length, 2);
  }
  assert.deepEqual(catalogue.getLevelsFromEntries([entries[2]]), ['All levels']);
  assert.equal(catalogue.filterEntriesByLevel(entries, 'All levels').length, 3);
});

test('bilingual audio, video and image resources are reachable through language filters', function () {
  const bilingual = { details: 'Sound File (BV)', url: 'LC012ZLP017BV.mp3', type: 'Exam Paper' };
  for (const language of ['EV', 'IV', 'BV']) {
    assert.equal(catalogue.filterEntriesByLanguage([bilingual], language).length, 1);
  }
  assert.deepEqual(catalogue.getLanguagesFromEntries([bilingual]), ['BV']);
  const video = { details: 'Audio Visual DVD / Common Level (EV)', url: 'LC462CLP031EV.mov', type: 'Exam Paper' };
  assert.equal(catalogue.classifyMaterialType(video), 'Video');
  assert.deepEqual(catalogue.getLanguagesFromEntries([video]), ['EV']);
  assert.deepEqual(catalogue.getLanguagesFromEntries([{ url: 'mapIV.tif' }]), ['IV']);
});

test('every catalogue entry has an accessible level, language, material type and official link', function () {
  for (const course of ['lc', 'jc', 'lb']) {
    for (const [subject, years] of Object.entries(data[course])) {
      for (const [year, entries] of Object.entries(years)) {
        for (const entry of entries) {
          const label = course + ' / ' + subject + ' / ' + year + ' / ' + entry.url;
          assert.ok(catalogue.buildPaperUrl(year, entry), label);
          assert.ok(catalogue.MATERIAL_TYPES_ORDER.includes(catalogue.classifyMaterialType(entry)), label);
          const levels = catalogue.getLevelsFromEntries([entry]);
          const languages = catalogue.getLanguagesFromEntries([entry]);
          assert.ok(levels.length && languages.length, label);
          assert.ok(catalogue.filterEntriesByLevel([entry], levels[0]).includes(entry), label);
          assert.ok(catalogue.filterEntriesByLanguage([entry], languages[0]).includes(entry), label);
        }
      }
    }
  }
});
