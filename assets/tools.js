/* Freelance calculators. Runs 100% in the browser; nothing is sent anywhere.
   Inputs are remembered only in this browser's localStorage. */
(function () {
  "use strict";
  var LS = window.localStorage;
  function store(k, v) { try { LS.setItem("fn_" + k, JSON.stringify(v)); } catch (e) {} }
  function load(k) { try { var v = LS.getItem("fn_" + k); return v ? JSON.parse(v) : null; } catch (e) { return null; } }
  function $(id) { return document.getElementById(id); }
  function num(el) {
    var raw = String(el.value).replace(/[\s,]/g, "");
    if (raw === "") { el.setAttribute("aria-invalid", "true"); return NaN; }
    var n = Number(raw);
    var bad = !isFinite(n) || n < 0 ||
      (el.max !== "" && el.max !== undefined && n > Number(el.max)) ||
      (el.min !== "" && el.min !== undefined && n < Number(el.min));
    el.setAttribute("aria-invalid", bad ? "true" : "false");
    return bad ? NaN : n;
  }
  function fmt(n, cur, dp) {
    if (!isFinite(n)) return "—";
    dp = dp === undefined ? 2 : dp;
    if (!cur || cur === "NONE") return n.toLocaleString("en-US", { minimumFractionDigits: dp, maximumFractionDigits: dp });
    try { return n.toLocaleString("en-US", { style: "currency", currency: cur, minimumFractionDigits: dp, maximumFractionDigits: dp }); }
    catch (e) { return n.toFixed(dp); }
  }
  function set(id, txt) { var el = $(id); if (el) el.textContent = txt; }
  function copy(text, okEl) {
    function done() { if (okEl) { okEl.textContent = "Copied ✓"; setTimeout(function () { okEl.textContent = ""; }, 2500); } }
    if (navigator.clipboard && window.isSecureContext) { navigator.clipboard.writeText(text).then(done, fallback); } else { fallback(); }
    function fallback() {
      var ta = document.createElement("textarea"); ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0";
      document.body.appendChild(ta); ta.select(); try { document.execCommand("copy"); done(); } catch (e) {} document.body.removeChild(ta);
    }
  }
  window.FN = { fmt: fmt };

  /* ---------- Tool 1: hourly rate floor ---------- */
  var RF = ["rf_takehome", "rf_weeksoff", "rf_days", "rf_hours", "rf_billable", "rf_costs", "rf_tax", "rf_fee", "rf_buffer"];
  function rateFloor() {
    var v = {}, ok = true;
    RF.forEach(function (id) { v[id] = num($(id)); if (isNaN(v[id])) ok = false; });
    var cur = $("rf_currency").value;
    var saved = {}; RF.forEach(function (id) { saved[id] = $(id).value; }); saved.rf_currency = cur; store("rf", saved);
    var err = $("rf_error");
    if (!ok) { err.textContent = "Check the highlighted fields (numbers only, within the allowed range)."; return; }
    var weeks = 52 - v.rf_weeksoff;
    var hours = weeks * v.rf_days * v.rf_hours * (v.rf_billable / 100);
    var tax = v.rf_tax / 100, fee = v.rf_fee / 100;
    if (hours <= 0) { err.textContent = "You have zero billable hours. Lower weeks off or raise days, hours or billable share."; return; }
    if (tax >= 1 || fee >= 1) { err.textContent = "Tax set-aside and fees must be below 100%."; return; }
    err.textContent = "";
    var revenue = (v.rf_takehome / (1 - tax) + v.rf_costs) / (1 - fee);
    var floor = revenue / hours;
    var quote = floor * (1 + v.rf_buffer / 100);
    var naive = v.rf_takehome / 2080;
    set("rf_out_floor", fmt(floor, cur));
    set("rf_out_quote", fmt(quote, cur));
    set("rf_out_day", fmt(floor * v.rf_hours, cur));
    set("rf_out_hours", Math.round(hours).toLocaleString("en-US"));
    set("rf_out_revenue", fmt(revenue, cur, 0));
    set("rf_out_month", fmt(revenue / 12, cur, 0));
    set("rf_out_taxamt", fmt(revenue * (1 - fee) - v.rf_costs - v.rf_takehome, cur, 0));
    set("rf_out_feeamt", fmt(revenue * fee, cur, 0));
    set("rf_out_naive", fmt(naive, cur));
    set("rf_out_gap", naive > 0 ? (floor / naive).toFixed(1) + "×" : "—");
    store("floor", { floor: floor, quote: quote, cur: cur });
    $("rf_summary").dataset.text =
      "Rate floor: " + fmt(floor, cur) + "/billable hour\n" +
      "Quote at: " + fmt(quote, cur) + "/hour (+" + v.rf_buffer + "% buffer)\n" +
      "Day rate floor (" + v.rf_hours + " h): " + fmt(floor * v.rf_hours, cur) + "\n" +
      "Billable hours/year: " + Math.round(hours) + "\n" +
      "Revenue to invoice/year: " + fmt(revenue, cur, 0) + " (monthly " + fmt(revenue / 12, cur, 0) + ")";
  }
  if ($("rf_form")) {
    var s = load("rf");
    if (s) { Object.keys(s).forEach(function (k) { if ($(k) && s[k] !== "") $(k).value = s[k]; }); }
    $("rf_form").addEventListener("input", rateFloor);
    $("rf_form").addEventListener("submit", function (e) { e.preventDefault(); rateFloor(); });
    $("rf_reset").addEventListener("click", function () { try { LS.removeItem("fn_rf"); } catch (e) {} $("rf_form").reset(); rateFloor(); });
    $("rf_copy").addEventListener("click", function () { copy($("rf_summary").dataset.text || "", $("rf_copied")); });
    rateFloor();
  }

  /* ---------- Tool 2: project quote + payment fees ---------- */
  var DEFAULT_PHASES = [["Discovery & brief", 4], ["Design / first draft", 12], ["Build / production", 20], ["Revisions & handover", 6]];
  function phaseRow(name, hrs) {
    var tr = document.createElement("tr");
    tr.innerHTML = '<td><input type="text" class="ph-name" aria-label="Phase name" maxlength="80"></td>' +
      '<td style="width:110px"><input type="number" class="ph-hrs" aria-label="Estimated hours" min="0" max="10000" step="0.5" inputmode="decimal"></td>' +
      '<td class="x"><button type="button" class="icon-btn" aria-label="Remove phase" title="Remove phase">×</button></td>';
    tr.querySelector(".ph-name").value = name; tr.querySelector(".ph-hrs").value = hrs;
    tr.querySelector("button").addEventListener("click", function () { tr.remove(); quote(); });
    return tr;
  }
  var Q = ["q_rate", "q_buffer", "q_deposit", "q_feepct", "q_feefix", "q_fx", "q_floor"];
  function quote() {
    var v = {}, ok = true;
    Q.forEach(function (id) { v[id] = num($(id)); if (isNaN(v[id])) ok = false; });
    var cur = $("q_currency").value, gross = $("q_grossup").checked;
    var phases = [], hrs = 0;
    Array.prototype.forEach.call(document.querySelectorAll("#q_phases tbody tr"), function (tr) {
      var h = num(tr.querySelector(".ph-hrs")); if (isNaN(h)) { ok = false; h = 0; }
      var nm = tr.querySelector(".ph-name").value.trim() || "Phase";
      phases.push([nm, h]); hrs += h;
    });
    var saved = { phases: phases, cur: cur, gross: gross }; Q.forEach(function (id) { saved[id] = $(id).value; }); store("q", saved);
    var err = $("q_error");
    if (!ok) { err.textContent = "Check the highlighted fields (numbers only, within the allowed range)."; return; }
    var pct = v.q_feepct / 100, fx = v.q_fx / 100;
    if (pct + fx >= 1) { err.textContent = "Fees must add up to less than 100%."; return; }
    if (hrs <= 0) { err.textContent = "Add at least one phase with hours."; }
    else err.textContent = "";
    var labour = hrs * v.q_rate, buffer = labour * v.q_buffer / 100, quoteTotal = labour + buffer;
    var invoice = gross ? (quoteTotal + v.q_feefix) / (1 - pct - fx) : quoteTotal;
    var fees = quoteTotal > 0 ? invoice * (pct + fx) + v.q_feefix : 0;
    var net = invoice - fees;
    var effExpected = hrs > 0 ? net / hrs : NaN;
    var effWorst = hrs > 0 ? net / (hrs * (1 + v.q_buffer / 100)) : NaN;
    set("q_out_hours", hrs.toLocaleString("en-US", { maximumFractionDigits: 1 }));
    set("q_out_labour", fmt(labour, cur)); set("q_out_buffer", fmt(buffer, cur));
    set("q_out_quote", fmt(quoteTotal, cur)); set("q_out_invoice", fmt(invoice, cur));
    set("q_out_fees", fmt(fees, cur)); set("q_out_net", fmt(net, cur));
    set("q_out_deposit", fmt(invoice * v.q_deposit / 100, cur));
    set("q_out_balance", fmt(invoice * (1 - v.q_deposit / 100), cur));
    set("q_out_eff", fmt(effExpected, cur)); set("q_out_effworst", fmt(effWorst, cur));
    set("q_out_big", fmt(invoice, cur));
    var vd = $("q_verdict"), fl = v.q_floor;
    if (!(hrs > 0)) { vd.className = "verdict"; vd.textContent = ""; }
    else if (fl <= 0) { vd.className = "verdict warn"; vd.textContent = "Enter your rate floor to check this quote. (Use the hourly rate calculator if you don't know it.)"; }
    else if (effWorst >= fl) { vd.className = "verdict ok"; vd.textContent = "✔ Above your floor even if the whole buffer gets used (" + fmt(effWorst, cur) + "/h ≥ " + fmt(fl, cur) + "/h)."; }
    else if (effExpected >= fl) { vd.className = "verdict warn"; vd.textContent = "⚠ Above your floor only if the estimate holds. If the buffer gets used you earn " + fmt(effWorst, cur) + "/h, below your " + fmt(fl, cur) + "/h floor."; }
    else { vd.className = "verdict bad"; vd.textContent = "✖ Below your floor: " + fmt(effExpected, cur) + "/h after fees vs a " + fmt(fl, cur) + "/h floor. Raise the rate, cut scope, or pass the fees on."; }
    var lines = phases.map(function (p) { return "- " + p[0] + ": " + p[1] + " h × " + fmt(v.q_rate, cur) + " = " + fmt(p[1] * v.q_rate, cur); });
    $("q_summary").dataset.text = "Project quote\n" + lines.join("\n") +
      "\nContingency (" + v.q_buffer + "%): " + fmt(buffer, cur) +
      "\nProject total: " + fmt(quoteTotal, cur) +
      (gross ? "\nPayment processing: " + fmt(invoice - quoteTotal, cur) + "\nTotal to invoice: " + fmt(invoice, cur) : "") +
      (v.q_deposit > 0 ? "\nDeposit to start (" + v.q_deposit + "%): " + fmt(invoice * v.q_deposit / 100, cur) + "\nBalance on delivery: " + fmt(invoice * (1 - v.q_deposit / 100), cur) : "");
  }
  if ($("q_form")) {
    var tb = document.querySelector("#q_phases tbody");
    var sq = load("q"), fl = load("floor");
    (sq && sq.phases && sq.phases.length ? sq.phases : DEFAULT_PHASES).forEach(function (p) { tb.appendChild(phaseRow(p[0], p[1])); });
    if (sq) { Q.forEach(function (id) { if (sq[id] !== undefined && sq[id] !== "") $(id).value = sq[id]; }); $("q_currency").value = sq.cur || "USD"; $("q_grossup").checked = !!sq.gross; }
    else if (fl && fl.floor) {
      $("q_floor").value = fl.floor.toFixed(2); $("q_rate").value = Math.ceil(fl.quote); if (fl.cur) $("q_currency").value = fl.cur;
      $("q_floor_note").textContent = "Filled in from your hourly rate calculator result.";
    }
    $("q_add").addEventListener("click", function () { tb.appendChild(phaseRow("New phase", 1)); quote(); tb.lastChild.querySelector("input").select(); });
    $("q_form").addEventListener("input", quote);
    $("q_form").addEventListener("change", quote);
    $("q_form").addEventListener("submit", function (e) { e.preventDefault(); quote(); });
    $("q_reset").addEventListener("click", function () {
      try { LS.removeItem("fn_q"); } catch (e) {} $("q_form").reset(); tb.innerHTML = "";
      DEFAULT_PHASES.forEach(function (p) { tb.appendChild(phaseRow(p[0], p[1])); }); quote();
    });
    $("q_copy").addEventListener("click", function () { copy($("q_summary").dataset.text || "", $("q_copied")); });
    quote();
  }
})();
