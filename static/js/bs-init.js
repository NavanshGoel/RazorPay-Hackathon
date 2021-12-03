document.addEventListener(
  "DOMContentLoaded",
  function () {
    var charts = document.querySelectorAll("[data-bss-chart]");

    for (var chart of charts) {
      chart.chart = new Chart(chart, JSON.parse(chart.dataset.bssChart));
    }
  },
  false
);

window.addEventListener("afterprint", () => {
  var charts = document.querySelectorAll("[data-bss-chart]");

  for (var chart of charts) {
    chart.chart.resize();
  }
});

window.addEventListener("beforeprint", () => {
  var charts = document.querySelectorAll("[data-bss-chart]");

  for (var chart of charts) {
    chart.chart.resize(600, 600);
  }
});
