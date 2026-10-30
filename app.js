(function () {
  'use strict';

  const catalogue = window.ExamCatalogue;
  const COURSES = {
    jc: 'Junior Cycle / Junior Certificate',
    lc: 'Leaving Certificate',
    lb: 'Leaving Certificate Applied'
  };
  const LANGUAGES = catalogue.LANGUAGES;
  const MATERIAL_TYPES_ORDER = catalogue.MATERIAL_TYPES_ORDER;
  const getLevelsFromEntries = catalogue.getLevelsFromEntries;
  const getLanguagesFromEntries = catalogue.getLanguagesFromEntries;
  const filterEntriesByLevel = catalogue.filterEntriesByLevel;
  const filterEntriesByLanguage = catalogue.filterEntriesByLanguage;
  const classifyMaterialType = catalogue.classifyMaterialType;
  const buildPaperUrl = catalogue.buildPaperUrl;

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
      var href = buildPaperUrl(year, p);
      if (!href) return;
      var li = document.createElement('li');
      var a = document.createElement('a');
      a.href = href;
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
    fetch('data.json', { cache: 'no-cache' })
      .then(function (r) {
        if (!r.ok) throw new Error('Could not load the exam catalogue (' + r.status + ').');
        return r.json();
      })
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
