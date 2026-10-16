/* Freelance Numbers: small calculators for the programmatic pages. Runs locally in the browser; nothing is sent anywhere. */
(function () {
  "use strict";
  function $(id) { return document.getElementById(id); }
  function n(id) { var el = $(id); if (!el) return 0; var v = parseFloat(String(el.value).replace(/[, $%]/g, "")); return isNaN(v) ? 0 : v; }
  function r2(x) { return Math.round((x + Number.EPSILON) * 100) / 100; }
  function usd(x) { var s = x < 0 ? "−" : ""; return s + "$" + Math.abs(x).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
  function usd0(x) { var s = x < 0 ? "−" : ""; return s + "$" + Math.round(Math.abs(x)).toLocaleString("en-US"); }
  function pct(x) { return (Math.round(x * 10) / 10).toFixed(1) + "%"; }
  function set(id, t) { var el = $(id); if (el) el.textContent = t; }
  function bind(form, fn) { if (!form) return; form.addEventListener("input", fn); form.addEventListener("submit", function (e) { e.preventDefault(); fn(); }); fn(); }

  /* Etsy fee calculator */
  function etsy() {
    var p = n("e_price"), s = n("e_ship"), t = n("e_tax"), q = Math.max(1, Math.round(n("e_qty")) || 1), c = n("e_cost"), ads = $("e_ads").value;
    var gross = p * q + s;
    var listing = 0.20 * q;                 /* first listing + $0.20 per additional quantity sold */
    var trans = r2(gross * 0.065);
    var proc = r2((gross + t) * 0.03 + 0.25);
    var off = 0; if (ads !== "0") { off = Math.min(r2(gross * parseFloat(ads) / 100), 100); }
    var fees = r2(listing + trans + proc + off);
    var net = r2(gross - fees);
    var profit = r2(net - c);
    set("e_o_listing", usd(listing)); set("e_o_trans", usd(trans)); set("e_o_proc", usd(proc)); set("e_o_off", usd(off));
    set("e_o_fees", usd(fees)); set("e_o_net", usd(net)); set("e_o_profit", usd(profit));
    set("e_o_share", gross > 0 ? pct(fees / gross * 100) + " of what the buyer paid you" : "");
    set("e_o_margin", gross > 0 ? pct(profit / gross * 100) : "–");
  }

  /* Freelance rate calculator */
  function rate() {
    var inc = n("r_income"), cost = n("r_costs"), ben = n("r_benefits"), hrs = n("r_hours"), fee = n("r_fee") / 100, day = n("r_day");
    var se = $("r_se").checked ? inc * 0.0648 : 0;  /* 15.3% x 92.35% = 14.13% vs 7.65% an employee pays */
    var need = inc + se + cost + ben;
    var gross = fee < 1 ? need / (1 - fee) : need;
    var h = hrs > 0 ? gross / hrs : 0;
    set("r_o_rate", hrs > 0 ? usd(h) : "–"); set("r_o_day", hrs > 0 ? usd(h * day) : "–");
    set("r_o_year", usd0(gross)); set("r_o_month", usd0(gross / 12)); set("r_o_se", usd0(se));
    set("r_o_week", hrs > 0 ? (Math.round(hrs / 46 * 10) / 10) + " billable h/week over 46 working weeks" : "");
  }

  /* Landlord: Schedule E expense totals */
  function exp() {
    var ids = ["x5","x6","x7","x8","x9","x10","x11","x12","x13","x14","x15","x16","x17","x19"], tot = 0;
    ids.forEach(function (i) { tot += n(i); });
    var dep = n("x18"), rent = n("x_rent");
    set("x_o_cash", usd0(tot)); set("x_o_all", usd0(tot + dep)); set("x_o_net", usd0(rent - tot - dep)); set("x_o_before", usd0(rent - tot));
  }

  /* Landlord: residential rental depreciation (27.5 years, straight line, mid-month) */
  function dep() {
    var price = n("d_price"), land = n("d_land"), add = n("d_add"), m = Math.min(12, Math.max(1, Math.round(n("d_month")) || 1));
    var basis = Math.max(0, price - land + add);
    var annual = basis / 27.5, y1 = basis * (12 - m + 0.5) / 12 / 27.5;
    set("d_o_basis", usd0(basis)); set("d_o_y1", usd(y1)); set("d_o_full", usd(annual)); set("d_o_month", usd(annual / 12));
    set("d_o_y1pct", ((12 - m + 0.5) / 12 / 27.5 * 100).toFixed(3) + "%");
  }

  /* Landlord: repair vs improvement cost comparison */
  function rep() {
    var c = n("p_cost"), m = Math.min(12, Math.max(1, Math.round(n("p_month")) || 1)), tr = n("p_tax") / 100;
    var y1 = c * (12 - m + 0.5) / 12 / 27.5;
    set("p_o_rep", usd(c)); set("p_o_imp", usd(y1)); set("p_o_full", usd(c / 27.5)); set("p_o_diff", usd((c - y1) * tr));
  }

  /* Landlord: monthly cash flow */
  function cf() {
    var rent = n("c_rent"), vac = n("c_vac") / 100, mort = n("c_mort"), tax = n("c_tax"), ins = n("c_ins"), hoa = n("c_hoa"), utl = n("c_util"), mgmt = n("c_mgmt") / 100, maint = n("c_maint") / 100, capx = n("c_capex") / 100;
    var eff = rent * (1 - vac);
    var opex = tax + ins + hoa + utl + rent * (mgmt + maint + capx);
    var noi = eff - opex, cash = noi - mort;
    set("c_o_eff", usd(eff)); set("c_o_opex", usd(opex)); set("c_o_noi", usd(noi)); set("c_o_cash", usd(cash)); set("c_o_year", usd0(cash * 12));
    var be = (1 - mgmt - maint - capx) > 0 ? (tax + ins + hoa + utl + mort) / ((1 - vac) - (mgmt + maint + capx)) : 0;
    set("c_o_be", be > 0 ? usd(be) : "–");
  }

  /* Landlord: security deposits */
  function dpst() {
    var rec = n("s_rec"), kept = n("s_kept"), last = n("s_last"), ret = Math.max(0, rec - kept - last);
    set("s_o_inc", usd(kept + last)); set("s_o_ret", usd(ret)); set("s_o_hold", usd(rec));
  }

  /* Landlord: rental income */
  function inc() {
    var t = n("i_rent") + n("i_adv") + n("i_paid") + n("i_svc") + n("i_cancel") + n("i_dep");
    set("i_o_total", usd(t)); set("i_o_offset", usd(n("i_paid") + n("i_svc")));
  }

  /* Landlord: mileage */
  function mil() {
    var a = n("m_a") * n("m_ra") / 100, b = n("m_b") * n("m_rb") / 100;
    set("m_o_a", usd(a)); set("m_o_b", usd(b)); set("m_o_tot", usd(a + b));
  }

  var map = { etsy: etsy, rate: rate, exp: exp, dep: dep, rep: rep, cf: cf, dpst: dpst, inc: inc, mil: mil };
  Array.prototype.forEach.call(document.querySelectorAll("form[data-calc]"), function (f) { var fn = map[f.getAttribute("data-calc")]; if (fn) bind(f, fn); });
})();
