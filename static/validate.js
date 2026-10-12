(function () {
  var path = location.pathname;

  function val(form, name) {
    return form.elements[name] ? form.elements[name].value : "";
  }

  function rules(form) {
    var errs = [];
    if (path === "/register") {
      if (!val(form, "name").trim()) errs.push(["name", "Name is required"]);
      if (!val(form, "email").trim()) errs.push(["email", "Email is required"]);
      var p = val(form, "password"), c = val(form, "confirm_password");
      if (!p) errs.push(["password", "Password is required"]);
      if (!c) errs.push(["confirm_password", "Confirm password is required"]);
      if (p && c && p !== c) errs.push(["confirm_password", "Passwords do not match"]);
    } else if (path === "/login") {
      if (!val(form, "email").trim()) errs.push(["email", "Email is required"]);
      if (!val(form, "password")) errs.push(["password", "Password is required"]);
    } else if (path === "/todos" && form.elements["title"]) {
      var t = val(form, "title").trim();
      if (!t) errs.push(["title", "Title is required"]);
      else if (t.length > 200) errs.push(["title", "Title is too long (200 characters at most)"]);
    }
    return errs;
  }

  function showError(input, msg) {
    var p = document.createElement("p");
    p.className = "error js-error";
    p.textContent = msg;
    input.insertAdjacentElement("afterend", p);
  }

  function clearErrors(form) {
    form.querySelectorAll(".error").forEach(function (e) { e.remove(); });
  }

  document.querySelectorAll("form").forEach(function (form) {
    if (form.elements["title"]) form.elements["title"].removeAttribute("maxlength");

    form.addEventListener("submit", function (ev) {
      clearErrors(form);
      var errs = rules(form);
      if (errs.length) {
        ev.preventDefault();
        var shown = {};
        errs.forEach(function (e) {
          if (shown[e[0]]) return;
          shown[e[0]] = true;
          showError(form.elements[e[0]], e[1]);
        });
        form.elements[errs[0][0]].focus();
      }
    });

    form.addEventListener("input", function (ev) {
      var next = ev.target.nextElementSibling;
      if (next && next.classList.contains("js-error")) next.remove();
    });
  });
})();
