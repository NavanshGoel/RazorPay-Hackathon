document.addEventListener(
  "DOMContentLoaded",
  function () {
    var charts = document.querySelectorAll("[data-bss-chart]");

    for (var chart of charts) {
      console.log(chart.dataset.bssChart);
      chart.chart = new Chart(chart, JSON.parse(chart.dataset.bssChart));
    }
  },
  false
);

