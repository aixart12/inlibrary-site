// Syllabus library: search the published plans and read their subjects and topics.
// Reads syllabus/v1/index.json, then every plan file, so subject and topic names are searchable.
// Only published plans are listed because the index contains only those. No third-party requests.

(function () {
  var CATEGORIES = [
    ['school', 'School'],
    ['entrance', 'Entrance'],
    ['central-govt', 'Central govt'],
    ['railways', 'Railways'],
    ['banking', 'Banking'],
    ['state-bihar', 'Bihar'],
    ['state-other', 'Other states'],
    ['defence', 'Defence'],
    ['teaching', 'Teaching'],
  ];
  var CATEGORY_LABEL = {};
  CATEGORIES.forEach(function (c) {
    CATEGORY_LABEL[c[0]] = c[1];
  });

  var $ = function (id) {
    return document.getElementById(id);
  };
  var listView = $('lib-list');
  var planView = $('lib-plan');
  var input = $('lib-q');
  var catBox = $('lib-cats');
  var statusEl = $('lib-status');
  var resultsEl = $('lib-results');

  var plans = []; // index entries
  var details = {}; // slug -> full plan, filled in as files arrive
  var activeCat = '';
  var query = '';

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function words(text) {
    return String(text || '')
      .toLowerCase()
      .split(/[^a-z0-9ऀ-ॿ]+/)
      .filter(Boolean);
  }

  // Every typed word must be the start of some word in the text.
  function matches(terms, text) {
    var hay = words(text);
    return terms.every(function (t) {
      return hay.some(function (w) {
        return w.indexOf(t) === 0;
      });
    });
  }

  function planText(p) {
    return [p.name, p.short_name].concat(p.aliases || []).join(' ');
  }

  function search() {
    var terms = words(query);
    var out = [];
    plans.forEach(function (p) {
      if (activeCat && p.category !== activeCat) return;
      var hit = { plan: p, topics: [], subjects: [] };
      if (!terms.length || matches(terms, planText(p))) {
        out.push(hit);
        return;
      }
      var d = details[p.slug];
      if (!d) return;
      d.subjects.forEach(function (s) {
        if (matches(terms, s.name)) hit.subjects.push(s.name);
        s.topics.forEach(function (t) {
          if (matches(terms, t.name)) hit.topics.push({ topic: t.name, subject: s.name });
        });
      });
      if (hit.subjects.length || hit.topics.length) out.push(hit);
    });
    return out;
  }

  function renderCats() {
    catBox.textContent = '';
    var present = {};
    plans.forEach(function (p) {
      present[p.category] = true;
    });
    var all = [['', 'All']].concat(
      CATEGORIES.filter(function (c) {
        return present[c[0]];
      })
    );
    all.forEach(function (c) {
      var b = el('button', 'lib-chip', c[1]);
      b.type = 'button';
      b.setAttribute('aria-pressed', String(activeCat === c[0]));
      b.addEventListener('click', function () {
        activeCat = c[0];
        renderCats();
        renderResults();
      });
      catBox.appendChild(b);
    });
  }

  function renderResults() {
    var found = search();
    resultsEl.textContent = '';
    var n = found.length;
    statusEl.textContent = n
      ? n + (n === 1 ? ' syllabus' : ' syllabi')
      : 'Nothing found. Try a shorter word, such as "ssc", "12" or "physics".';

    found.forEach(function (h) {
      var p = h.plan;
      var li = el('li');
      var a = el('a', 'lib-card');
      a.href = '#/' + encodeURIComponent(p.slug);
      var top = el('div', 'lib-card-top');
      top.appendChild(el('strong', null, p.name));
      top.appendChild(el('span', 'tag', CATEGORY_LABEL[p.category] || p.category));
      a.appendChild(top);
      a.appendChild(
        el('span', 'lib-meta', p.subject_count + ' subjects · ' + p.topic_count + ' chapters')
      );
      var shown = h.subjects.slice(0, 2).map(function (s) {
        return s + ' (subject)';
      });
      h.topics.slice(0, 3).forEach(function (t) {
        shown.push(t.topic + ' · ' + t.subject);
      });
      if (shown.length) {
        var more = h.subjects.length + h.topics.length - shown.length;
        a.appendChild(
          el('span', 'lib-hit', 'Matches: ' + shown.join('; ') + (more > 0 ? ' and ' + more + ' more' : ''))
        );
      }
      li.appendChild(a);
      resultsEl.appendChild(li);
    });
  }

  function renderPlan(slug) {
    var p = plans.filter(function (x) {
      return x.slug === slug;
    })[0];
    planView.textContent = '';
    var back = el('a', 'lib-back', '← All syllabi');
    back.href = '#/';
    planView.appendChild(back);

    if (!p) {
      planView.appendChild(el('h2', null, 'Syllabus not found'));
      planView.appendChild(el('p', 'lib-note', 'It may not be published yet. Go back and search again.'));
      return;
    }
    var d = details[slug];
    planView.appendChild(el('h2', 'lib-title', p.name));
    var meta = el('p', 'lib-meta', CATEGORY_LABEL[p.category] || p.category);
    meta.textContent += ' · ' + p.subject_count + ' subjects · ' + p.topic_count + ' chapters';
    planView.appendChild(meta);
    if (!d) {
      planView.appendChild(el('p', 'lib-note', 'Loading...'));
      return;
    }

    var tools = el('div', 'lib-tools');
    var filter = el('input');
    filter.type = 'search';
    filter.placeholder = 'Search inside this syllabus';
    filter.setAttribute('aria-label', 'Search inside this syllabus');
    var expand = el('button', 'btn btn-ghost', 'Expand all');
    expand.type = 'button';
    tools.appendChild(filter);
    tools.appendChild(expand);
    planView.appendChild(tools);

    var empty = el('p', 'lib-note', 'No chapter matches.');
    empty.hidden = true;
    var wrap = el('div', 'lib-subjects');
    var blocks = d.subjects.map(function (s) {
      var det = el('details', 'lib-subject');
      var sum = el('summary');
      sum.appendChild(el('span', null, s.name));
      sum.appendChild(el('small', null, s.topics.length + ' chapters'));
      det.appendChild(sum);
      var ol = el('ol');
      var items = s.topics.map(function (t) {
        var li = el('li', null, t.name);
        ol.appendChild(li);
        return { li: li, text: t.name };
      });
      det.appendChild(ol);
      wrap.appendChild(det);
      return { det: det, name: s.name, items: items };
    });
    planView.appendChild(wrap);
    planView.appendChild(empty);
    if (blocks.length === 1) blocks[0].det.open = true;

    var allOpen = false;
    expand.addEventListener('click', function () {
      allOpen = !allOpen;
      blocks.forEach(function (b) {
        if (!b.det.hidden) b.det.open = allOpen;
      });
      expand.textContent = allOpen ? 'Collapse all' : 'Expand all';
    });

    filter.addEventListener('input', function () {
      var terms = words(filter.value);
      var any = false;
      blocks.forEach(function (b) {
        var subjectHit = terms.length && matches(terms, b.name);
        var count = 0;
        b.items.forEach(function (it) {
          var ok = !terms.length || subjectHit || matches(terms, it.text);
          it.li.hidden = !ok;
          if (ok) count++;
        });
        b.det.hidden = count === 0;
        if (terms.length && count) b.det.open = true;
        if (count) any = true;
      });
      empty.hidden = any;
    });

    // Arriving from a search: open the subjects that matched.
    var terms = words(query);
    if (terms.length && !matches(terms, planText(p))) {
      filter.value = query;
      filter.dispatchEvent(new Event('input'));
    }
  }

  function route() {
    var m = /^#\/([^/]+)/.exec(location.hash);
    if (m) {
      var slug = decodeURIComponent(m[1]);
      listView.hidden = true;
      planView.hidden = false;
      renderPlan(slug);
      var p = plans.filter(function (x) {
        return x.slug === slug;
      })[0];
      document.title = (p ? p.name : 'Syllabus') + ' — InLibrary';
      window.scrollTo(0, 0);
    } else {
      planView.hidden = true;
      listView.hidden = false;
      document.title = 'Syllabus Library — InLibrary';
    }
  }

  function getJson(url) {
    return fetch(url).then(function (r) {
      if (!r.ok) throw new Error(url + ' ' + r.status);
      return r.json();
    });
  }

  input.addEventListener('input', function () {
    query = input.value;
    renderResults();
  });
  window.addEventListener('hashchange', route);

  getJson('syllabus/v1/index.json')
    .then(function (idx) {
      plans = (idx.plans || []).slice();
      renderCats();
      renderResults();
      route();
      // Fetch every plan so subjects and chapters become searchable.
      return Promise.all(
        plans.map(function (p) {
          return getJson('syllabus/v1/plans/' + encodeURIComponent(p.slug) + '.json')
            .then(function (d) {
              details[p.slug] = d;
            })
            .catch(function () {});
        })
      );
    })
    .then(function () {
      if (plans.length) {
        renderResults();
        route();
      }
    })
    .catch(function () {
      statusEl.textContent = 'Could not load the library. Check your connection and try again.';
    });
})();
