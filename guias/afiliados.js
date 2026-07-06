// afiliados.js — interruptor central de monetización de las Guías de Chile.
//
// ÚNICO paso para encender los ingresos (acción humana #7 en agente/ESTADO.md):
// rellenar los IDs de afiliado de abajo y hacer commit. Nada más.
// Mientras estén vacíos, los botones funcionan como enlaces normales (sin comisión).
window.PSR_AFILIADOS = {
  viator_pid: "",    // ID de partner Viator, ej: "P00123456"
  civitatis_aid: ""  // ID de afiliado Civitatis, ej: "12345"
};

document.addEventListener("DOMContentLoaded", function () {
  var ids = window.PSR_AFILIADOS;
  document.querySelectorAll("a[data-afiliado]").forEach(function (a) {
    try {
      var url = new URL(a.href);
      if (a.dataset.afiliado === "viator" && ids.viator_pid) {
        url.searchParams.set("pid", ids.viator_pid);
        url.searchParams.set("mcid", "42383");
        url.searchParams.set("medium", "link");
      } else if (a.dataset.afiliado === "civitatis" && ids.civitatis_aid) {
        url.searchParams.set("aid", ids.civitatis_aid);
      }
      a.href = url.toString();
      a.rel = "sponsored noopener";
      a.target = "_blank";
    } catch (e) { /* URL inválida: dejar el enlace tal cual */ }
  });
});
