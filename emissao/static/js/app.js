/* Gestão Tech — máscaras, estados de carregamento e acessibilidade. */
(function () {
  "use strict";

  // máscara de CPF: 000.000.000-00
  var cpf = document.querySelector("[data-mascara-cpf]");
  if (cpf) {
    var soDigitos = function (v) { return (v || "").replace(/\D/g, "").slice(0, 11); };
    var formatar = function (d) {
      return d.replace(/^(\d{3})(\d)/, "$1.$2")
              .replace(/^(\d{3})\.(\d{3})(\d)/, "$1.$2.$3")
              .replace(/^(\d{3})\.(\d{3})\.(\d{3})(\d)/, "$1.$2.$3-$4");
    };
    cpf.value = formatar(soDigitos(cpf.value));
    cpf.addEventListener("input", function () {
      var pos = cpf.selectionStart, antes = cpf.value.length;
      cpf.value = formatar(soDigitos(cpf.value));
      var dif = cpf.value.length - antes;
      try { cpf.setSelectionRange(pos + dif, pos + dif); } catch (e) {}
    });
  }

  // máscara do código de validação: OFC-XXXX-XXXX-XXXX
  var cod = document.querySelector("[data-mascara-codigo]");
  if (cod) {
    var fmt = function (v) {
      var s = (v || "").toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 15);
      var partes = [s.slice(0, 3), s.slice(3, 7), s.slice(7, 11), s.slice(11, 15)];
      return partes.filter(function (p) { return p.length; }).join("-");
    };
    cod.value = fmt(cod.value);
    cod.addEventListener("input", function () { cod.value = fmt(cod.value); });
  }

  // estado de carregamento no botão de busca / download
  var form = document.querySelector("[data-form-busca]");
  if (form) {
    form.addEventListener("submit", function (e) {
      var btn = form.querySelector("[data-botao-busca]");
      if (!btn) return;
      if (!form.checkValidity()) { e.preventDefault(); form.reportValidity(); return; }
      btn.classList.add("carregando");
      var r = btn.querySelector(".rotulo");
      if (r) r.textContent = "Buscando…";
      btn.setAttribute("aria-busy", "true");
    });
  }
  document.querySelectorAll("[data-botao-download]").forEach(function (a) {
    a.addEventListener("click", function () {
      a.classList.add("carregando");
      var r = a.querySelector(".rotulo");
      if (r) r.textContent = "Gerando PDF…";
    });
  });
})();
