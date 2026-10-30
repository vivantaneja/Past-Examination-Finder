(function (root, factory) {
  'use strict';
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.ExamCatalogue = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const LEVELS_ORDER = ['Higher', 'Ordinary', 'Foundation', 'Common', 'All levels'];
  const LANGUAGES = { EV: 'English', IV: 'Irish', BV: 'Bilingual', UN: 'Not specified' };
  const ARCHIVES = {
    'Exam Paper': 'exampapers',
    'Marking Scheme': 'markingschemes',
    'Deferred Exam Paper': 'deferredexams',
    'Deferred Marking Scheme': 'deferredmarkingschemes'
  };
  const MATERIAL_TYPES_ORDER = [
    'Exam Paper', 'Marking Scheme', 'Deferred Exam Paper', 'Deferred Marking Scheme',
    'Audio', 'Deferred Audio', 'Video', 'Deferred Video'
  ];

  function entryLevels(entry) {
    return LEVELS_ORDER.slice(0, -1).filter(function (level) {
      return (entry.details || '').indexOf(level) !== -1;
    });
  }

  function getLevelsFromEntries(entries) {
    return LEVELS_ORDER.filter(function (level) {
      return entries.some(function (entry) {
        const levels = entryLevels(entry);
        return level === 'All levels' ? levels.length === 0 : levels.indexOf(level) !== -1;
      });
    });
  }

  function filterEntriesByLevel(entries, level) {
    return entries.filter(function (entry) {
      const levels = entryLevels(entry);
      // Unlabelled sound files/maps accompany the subject's papers at every level.
      return level === 'All levels' || levels.length === 0 || levels.indexOf(level) !== -1;
    });
  }

  function entryLanguage(entry) {
    const filename = (entry.url || '').split(/[?#]/)[0];
    const match = filename.match(/(EV|IV|BV)\s*\.[^.\/]+$/i)
      || (entry.details || '').match(/\((EV|IV|BV)\)/i);
    return match ? match[1].toUpperCase() : 'UN';
  }

  function getLanguagesFromEntries(entries) {
    const codes = new Set(entries.map(entryLanguage));
    return Object.keys(LANGUAGES).filter(function (code) { return codes.has(code); });
  }

  function filterEntriesByLanguage(entries, language) {
    return entries.filter(function (entry) {
      const code = entryLanguage(entry);
      return code === language || (code === 'BV' && (language === 'EV' || language === 'IV'));
    });
  }

  function classifyMaterialType(entry) {
    const filename = (entry.url || '').split(/[?#]/)[0];
    const details = entry.details || '';
    const prefix = /^Deferred /.test(entry.type || '') ? 'Deferred ' : '';
    if (/\.(mp3|wav|m4a|ogg)$/i.test(filename) || /sound file/i.test(details)) return prefix + 'Audio';
    if (/\.(mp4|mov|avi|webm)$/i.test(filename) || /audio visual|video/i.test(details)) return prefix + 'Video';
    return Object.prototype.hasOwnProperty.call(ARCHIVES, entry.type) ? entry.type : '';
  }

  function officialUrl(value) {
    try {
      const parsed = new URL(value);
      if (parsed.protocol === 'https:' && parsed.hostname === 'www.examinations.ie'
          && !parsed.username && !parsed.password && !parsed.port
          && (parsed.pathname.startsWith('/archive/') || parsed.pathname === '/exammaterialarchive/')) {
        return parsed.href;
      }
    } catch (_) { /* Legacy entries contain filenames, not full URLs. */ }
    return null;
  }

  function buildPaperUrl(year, entry) {
    // New imports retain the actual published link, including deferred resources.
    if (entry.href) return officialUrl(entry.href);
    const absolute = officialUrl(entry.url);
    if (absolute) return absolute;
    const archive = ARCHIVES[entry.type];
    if (!archive || !/^\d{4}$/.test(year) || !entry.url || /[\/\\]/.test(entry.url)) return null;
    return 'https://www.examinations.ie/archive/' + archive + '/' + year + '/' + encodeURIComponent(entry.url);
  }

  return {
    LEVELS_ORDER: LEVELS_ORDER,
    LANGUAGES: LANGUAGES,
    MATERIAL_TYPES_ORDER: MATERIAL_TYPES_ORDER,
    getLevelsFromEntries: getLevelsFromEntries,
    filterEntriesByLevel: filterEntriesByLevel,
    getLanguagesFromEntries: getLanguagesFromEntries,
    filterEntriesByLanguage: filterEntriesByLanguage,
    classifyMaterialType: classifyMaterialType,
    buildPaperUrl: buildPaperUrl
  };
});
