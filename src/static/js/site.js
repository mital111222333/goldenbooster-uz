(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  // ---- nav: transparent over dark openings, compact rail after scroll
  var nav = $("#nav");
  var opening = $(".hero, .dark-open");
  if (!opening) nav.classList.add("solid");
  function onScroll() {
    var limit = opening ? opening.offsetHeight - 90 : 40;
    nav.classList.toggle("scrolled", window.scrollY > limit);
  }
  addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  // ---- mobile menu
  var mm = $("#mmenu");
  $$("[data-menu]").forEach(function (b) {
    b.addEventListener("click", function () {
      var open = !mm.classList.contains("open");
      mm.classList.toggle("open", open);
      document.body.style.overflow = open ? "hidden" : "";
      $$("[data-menu]").forEach(function (x) { x.setAttribute("aria-expanded", open); });
    });
  });
  $$("#mmenu a").forEach(function (a) { a.addEventListener("click", function () { mm.classList.remove("open"); document.body.style.overflow = ""; }); });

  // ---- rails (selected card expands; arrows move selection)
  $$("[data-rail-id]").forEach(function (r) {
    var cards = Array.prototype.slice.call(r.children);
    function sel(i, scroll) {
      cards.forEach(function (c, j) { c.classList.toggle("sel", i === j); });
      if (scroll) setTimeout(function () {
        r.scrollTo({ left: cards[i].offsetLeft - r.offsetLeft - (innerWidth > 768 ? 48 : 16), behavior: "smooth" });
      }, 80);
    }
    cards.forEach(function (c, i) {
      c.addEventListener("click", function (e) {
        if (!c.classList.contains("sel")) { e.preventDefault(); sel(i, true); }
      });
    });
    $$('[data-rail="' + r.dataset.railId + '"]').forEach(function (b) {
      b.addEventListener("click", function () {
        var cur = cards.findIndex(function (c) { return c.classList.contains("sel"); });
        sel(Math.max(0, Math.min(cards.length - 1, cur + Number(b.dataset.d))), true);
      });
    });
  });

  // ---- reading statement darkens phrase by phrase
  var rp = $("#readP");
  if (rp) {
    var spans = $$("span", rp);
    var lit = function () {
      var r = rp.getBoundingClientRect();
      var prog = (innerHeight * 0.8 - r.top) / (r.height + innerHeight * 0.3);
      spans.forEach(function (s, i) { s.classList.toggle("lit", prog > i / spans.length); });
    };
    addEventListener("scroll", lit, { passive: true }); lit();
  }

  // ---- particle arch
  var ps = $("#particles");
  if (ps) {
    var ns = "http://www.w3.org/2000/svg", seed = 7;
    var rnd = function () { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
    for (var i = 0; i < 900; i++) {
      var t = rnd(), x = 60 + t * 1080, crown = Math.sin(t * Math.PI);
      var y = 230 - crown * 170 + (rnd() - 0.5) * (30 + 60 * crown) * rnd();
      if (rnd() > 0.25 + crown * 0.75) continue;
      var c = document.createElementNS(ns, "circle");
      c.setAttribute("cx", x.toFixed(1)); c.setAttribute("cy", y.toFixed(1));
      c.setAttribute("r", (0.6 + rnd() * 1.3).toFixed(2));
      c.setAttribute("fill", rnd() < 0.12 ? "#c9861f" : "#1a1714");
      c.setAttribute("opacity", (0.15 + crown * 0.6 * rnd()).toFixed(2));
      ps.appendChild(c);
    }
    [[20, 200], [1180, 200], [20, 120], [1180, 120]].forEach(function (p) {
      var l = document.createElementNS(ns, "path");
      l.setAttribute("d", "M" + (p[0] - 8) + " " + p[1] + " H" + (p[0] + 8));
      l.setAttribute("stroke", "#b1aca6"); ps.appendChild(l);
    });
  }

  // ---- catalog filter + search
  var cat = $("#catalog");
  if (cat) {
    var chips = $$(".chip", cat), q = $("#q"), blocks = $$(".cat-block", cat), cards = $$(".pcard", cat);
    var countEl = $("#count"), empty = $("#empty"), active = "all";
    var norm = function (s) { return (s || "").toLowerCase().replace(/[\s\-–]+/g, ""); };
    function apply() {
      var term = norm(q.value), n = 0;
      cards.forEach(function (c) {
        var ok = (active === "all" || c.dataset.cat === active) && (!term || norm(c.dataset.search).indexOf(term) !== -1);
        c.hidden = !ok; if (ok) n++;
      });
      blocks.forEach(function (b) { b.hidden = !$$(".pcard", b).some(function (c) { return !c.hidden; }); });
      countEl.textContent = n; empty.hidden = n > 0;
    }
    chips.forEach(function (ch) {
      ch.addEventListener("click", function () {
        active = ch.dataset.cat;
        chips.forEach(function (x) { x.classList.toggle("on", x === ch); x.setAttribute("aria-pressed", x === ch); });
        history.replaceState(null, "", active === "all" ? location.pathname : "#" + active);
        apply();
      });
    });
    q.addEventListener("input", apply);
    var h = location.hash.slice(1);
    var start = chips.filter(function (c) { return c.dataset.cat === h; })[0];
    if (start) start.click(); else apply();
  }

  // ---- contact form
  var form = $("#lead");
  if (form) {
    var params = new URLSearchParams(location.search);
    if (params.get("product")) form.product.value = params.get("product");
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var msg = $(".msg", form);
      var data = new FormData(form);
      var text = [form.dataset.subject, "", "Ism/Имя: " + data.get("name"), "Tel: " + data.get("phone"),
        "Shahar/Город: " + (data.get("city") || "-"), "Turi/Тип: " + (data.get("type") || "-"),
        "Mahsulot/Продукт: " + (data.get("product") || "-"), "", data.get("message") || ""].join("\n");
      var endpoint = form.dataset.endpoint, tg = form.dataset.telegram;
      if (endpoint) {
        fetch(endpoint, { method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify(Object.fromEntries(data.entries())) })
          .then(function (r) { if (!r.ok) throw 0; msg.textContent = form.dataset.ok; form.reset(); })
          .catch(function () { msg.textContent = form.dataset.err; });
      } else if (tg) {
        msg.textContent = form.dataset.fallback;
        window.open("https://t.me/" + tg + "?text=" + encodeURIComponent(text), "_blank", "noopener");
      } else {
        msg.textContent = form.dataset.err;
      }
    });
  }
})();
