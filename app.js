(function () {
  'use strict';

  const BASE_URL = 'https://www.examinations.ie/archive/exampapers';
  const COURSES = {
    jc: 'Junior Certificate',
    lc: 'Leaving Certificate',
    lb: 'Leaving Certificate Applied'
  };
  const LEVELS_ORDER = ['Higher', 'Ordinary', 'Foundation', 'Common'];
  const LANGUAGES = { EV: 'English', IV: 'Irish' };
  const MATERIAL_TYPES_ORDER = [
    'Exam Paper',
    'Marking Scheme',
    'Deferred Exam Paper',
    'Deferred Marking Scheme',
    'Audio'
  ];

  let data = null;

  function getCourses() {
    return Object.keys(COURSES).filter(function (key) {
      return data && data[key] && typeof data[key] === 'object' && !Array.isArray(data[key]);
    });
  }

  function getSubjects(course) {
    if (!data || !course || !data[course]) return [];
    return Object.keys(data[course]).sort(function (a, b) {
      return a.localeCompare(b);
    });
  }

  function getYears(course, subjectName) {
    if (!data || !data[course] || !data[course][subjectName]) return [];
    return Object.keys(data[course][subjectName]).sort(function (a, b) {
      return parseInt(b, 10) - parseInt(a, 10);
    });
  }

  function getEntriesForYear(course, subjectName, year) {
    if (!data || !data[course] || !data[course][subjectName] || !data[course][subjectName][year]) {
      return [];
    }
    return data[course][subjectName][year] || [];
  }

  function getLevelsFromEntries(entries) {
    const levels = new Set();
    LEVELS_ORDER.forEach(function (lvl) {
      if (entries.some(function (e) { return e.details && e.details.indexOf(lvl) !== -1; })) {
        levels.add(lvl);
      }
    });
    return LEVELS_ORDER.filter(function (l) { return levels.has(l); });
  }

  function getLanguagesFromEntries(entries) {
    const codes = new Set();
    entries.forEach(function (e) {
      const url = (e.url || '').toUpperCase();
      if (url.endsWith('EV.PDF') || url.endsWith('EV.MP3')) codes.add('EV');
      if (url.endsWith('IV.PDF') || url.endsWith('IV.MP3')) codes.add('IV');
    });
    return Object.keys(LANGUAGES).filter(function (code) { return codes.has(code); });
  }

  function filterEntriesByLevel(entries, level) {
    return entries.filter(function (e) { return e.details && e.details.indexOf(level) !== -1; });
  }

  function filterEntriesByLanguage(entries, langCode) {
    const upper = (langCode || '').toUpperCase();
    return entries.filter(function (e) {
      const url = (e.url || '').toUpperCase();
      return url.endsWith(upper + '.PDF') || url.endsWith(upper + '.MP3');
    });
  }

  function classifyMaterialType(entry) {
    const t = (entry.type || '').trim();
    const details = entry.details || '';
    const url = entry.url || '';
    const urlUpper = url.toUpperCase();
    const detailsUpper = details.toUpperCase();

    if (urlUpper.endsWith('.MP3') || detailsUpper.indexOf('SOUND FILE') !== -1) {
      return 'Audio';
    }
    if (t === 'Exam Paper') return 'Exam Paper';
    if (t === 'Marking Scheme') return 'Marking Scheme';
    if (t === 'Deferred Exam Paper') return 'Deferred Exam Paper';
    if (t === 'Deferred Marking Scheme') return 'Deferred Marking Scheme';

    return '';
  }

  function getEntries(course, subjectName, year, level, langCode, materialType) {
    let entries = getEntriesForYear(course, subjectName, year);
    entries = filterEntriesByLevel(entries, level);
    entries = filterEntriesByLanguage(entries, langCode);
    if (materialType) {
      entries = entries.filter(function (e) {
        return classifyMaterialType(e) === materialType;
      });
    }
    return entries;
  }

  function buildPaperUrl(year, url) {
    return BASE_URL + '/' + encodeURIComponent(year) + '/' + encodeURIComponent(url);
  }

  function showLoading(show) {
    var el = document.getElementById('results-loading');
    if (el) el.classList.toggle('hidden', !show);
  }

  function showEmpty(show) {
    var el = document.getElementById('results-empty');
    if (el) el.classList.toggle('hidden', !show);
  }

  function showList(show) {
    var el = document.getElementById('results-list');
    if (el) el.classList.toggle('hidden', !show);
  }

  function renderPapers(papers, year) {
    var list = document.getElementById('papers-list');
    if (!list) return;
    list.innerHTML = '';
    papers.forEach(function (p) {
      var li = document.createElement('li');
      var a = document.createElement('a');
      a.href = buildPaperUrl(year, p.url);
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
      a.textContent = p.details || p.url;
      li.appendChild(a);
      list.appendChild(li);
    });
  }

  function updateResults() {
    var course = document.getElementById('course').value;
    var subjectName = document.getElementById('subject').value;
    var year = document.getElementById('year').value;
    var level = document.getElementById('level').value;
    var langCode = document.getElementById('language').value;
    var materialType = document.getElementById('materialType').value;

    showLoading(false);
    showEmpty(false);
    showList(false);

    if (!course || !subjectName || !year || !level || !langCode || !materialType) {
      return;
    }

    var papers = getEntries(course, subjectName, year, level, langCode, materialType);
    if (papers.length === 0) {
      showEmpty(true);
    } else {
      renderPapers(papers, year);
      showList(true);
    }
  }

  function populateSubjects() {
    var course = document.getElementById('course').value;
    var select = document.getElementById('subject');
    var currentSubject = select.value;
    select.innerHTML = '<option value="" disabled>Select subject</option>';
    select.disabled = !course;
    if (!course) {
      select.value = '';
      populateYears();
      return;
    }
    var subjects = getSubjects(course);
    subjects.forEach(function (id) {
      var opt = document.createElement('option');
      opt.value = id;
      opt.textContent = id;
      select.appendChild(opt);
    });
    select.value = subjects.indexOf(currentSubject) !== -1 ? currentSubject : '';
    populateYears();
  }

  function populateYears() {
    var course = document.getElementById('course').value;
    var subjectName = document.getElementById('subject').value;
    var select = document.getElementById('year');
    var currentYear = select.value;
    select.innerHTML = '<option value="" disabled>Select year</option>';
    select.disabled = !course || !subjectName;
    if (!course || !subjectName) {
      select.value = '';
      populateLevels();
      return;
    }
    var years = getYears(course, subjectName);
    years.forEach(function (y) {
      var opt = document.createElement('option');
      opt.value = y;
      opt.textContent = y;
      select.appendChild(opt);
    });
    select.value = years.indexOf(currentYear) !== -1 ? currentYear : '';
    populateLevels();
  }

  function populateLevels() {
    var course = document.getElementById('course').value;
    var subjectName = document.getElementById('subject').value;
    var year = document.getElementById('year').value;
    var select = document.getElementById('level');
    var currentLevel = select.value;
    select.innerHTML = '<option value="" disabled>Select level</option>';
    select.disabled = !course || !subjectName || !year;
    if (!course || !subjectName || !year) {
      select.value = '';
      populateLanguages();
      return;
    }
    var entries = getEntriesForYear(course, subjectName, year);
    var levels = getLevelsFromEntries(entries);
    levels.forEach(function (l) {
      var opt = document.createElement('option');
      opt.value = l;
      opt.textContent = l;
      select.appendChild(opt);
    });
    select.value = levels.indexOf(currentLevel) !== -1 ? currentLevel : '';
    populateLanguages();
  }

  function populateLanguages() {
    var course = document.getElementById('course').value;
    var subjectName = document.getElementById('subject').value;
    var year = document.getElementById('year').value;
    var level = document.getElementById('level').value;
    var select = document.getElementById('language');
    var currentLang = select.value;
    select.innerHTML = '<option value="" disabled>Select language</option>';
    select.disabled = !course || !subjectName || !year || !level;
    if (!course || !subjectName || !year || !level) {
      select.value = '';
      populateMaterialTypes();
      return;
    }
    /* If level was cleared (invalid for new course/subject/year), clear language and below */
    if (!level) {
      select.value = '';
      populateMaterialTypes();
      return;
    }
    var entries = getEntriesForYear(course, subjectName, year);
    entries = filterEntriesByLevel(entries, level);
    var codes = getLanguagesFromEntries(entries);
    codes.forEach(function (code) {
      var opt = document.createElement('option');
      opt.value = code;
      opt.textContent = LANGUAGES[code] || code;
      select.appendChild(opt);
    });
    select.value = codes.indexOf(currentLang) !== -1 ? currentLang : '';
    populateMaterialTypes();
  }

  function populateMaterialTypes() {
    var course = document.getElementById('course').value;
    var subjectName = document.getElementById('subject').value;
    var year = document.getElementById('year').value;
    var level = document.getElementById('level').value;
    var langCode = document.getElementById('language').value;
    var select = document.getElementById('materialType');
    var currentType = select.value;

    select.innerHTML = '<option value="" disabled>Select material type</option>';
    select.disabled = !course || !subjectName || !year || !level || !langCode;

    if (!course || !subjectName || !year || !level || !langCode) {
      select.value = '';
      updateResults();
      return;
    }

    var entries = getEntries(course, subjectName, year, level, langCode, null);
    var types = new Set();
    entries.forEach(function (e) {
      var t = classifyMaterialType(e);
      if (t) types.add(t);
    });

    MATERIAL_TYPES_ORDER.forEach(function (label) {
      if (types.has(label)) {
        var opt = document.createElement('option');
        opt.value = label;
        opt.textContent = label;
        select.appendChild(opt);
      }
    });

    select.value = types.has(currentType) ? currentType : '';
    updateResults();
  }

  function bindFilters() {
    ['course', 'subject', 'year', 'level', 'language', 'materialType'].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) {
        el.addEventListener('change', function () {
          if (id === 'course') {
            // Once an examination has been chosen, prevent going back to the placeholder
            if (el.value !== '') {
              var placeholder = el.querySelector('option[value=\"\"]');
              if (placeholder) {
                placeholder.disabled = true;
              }
            }
            populateSubjects();
          }
          else if (id === 'subject') populateYears();
          else if (id === 'year') populateLevels();
          else if (id === 'level') populateLanguages();
          else if (id === 'language') populateMaterialTypes();
          else if (id === 'materialType') updateResults();
        });
      }
    });
  }

  function init() {
    showLoading(true);
    fetch('data.json')
      .then(function (r) { return r.json(); })
      .then(function (json) {
        data = json;
        showLoading(false);
        populateSubjects();
        bindFilters();
      })
      .catch(function (err) {
        showLoading(false);
        var empty = document.getElementById('results-empty');
        if (empty) {
          empty.innerHTML = '<p>Failed to load data. Serve this page from a local server (e.g. <code>python3 -m http.server</code>) so <code>data.json</code> can be loaded.</p>';
          empty.classList.remove('hidden');
        }
        console.error(err);
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
