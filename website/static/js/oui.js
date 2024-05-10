$(document).ready(function () {
  $(".card").viewportChecker({
    // Class to add to the elements when they are visible
    offset: 300,
    repeat: false,
    classToAdd: "visible",
  });
});

$(document).ready(function () {
  $(".hero2").viewportChecker({
    // Class to add to the elements when they are visible
    offset: 350,
    repeat: false,
    classToAdd: "visible",
  });
});

//https://stackoverflow.com/questions/26667562/how-to-start-animations-when-element-appears-on-screen

var myChart = document.getElementsByClassName("myChart")[0].getContext("2d");

var gradient = myChart.createLinearGradient(0, 0, 800, 0); //x0, y0, x1, y1
gradient.addColorStop(0, "#A48CED");
gradient.addColorStop(1, "#4B13EC");

var SRSCharte = new Chart(myChart, {
  type: "bar",
  data: {
    labels: ["FSRS v4 (optimized)", "LSTM", "FSRS v3", "SM2", "HLR"],
    datasets: [
      {
        label: "Racine de l'erreur quadratique moyen (en %)",
        data: [5.9, 8.6, 10.7, 18.0, 20.9],
        borderRadius: 10,
        backgroundColor: [gradient], //primaire
      },
    ],
  },
  options: {
    responsive: true,
    indexAxis: "y",
    scales: {
      x: {
        ticks: {
          color: "#f5f5ff",
          beginAtZero: true,
          font: {
            family: "Poppins",
            size: 13,
          },
        }, //couleur texte
        grid: {
          display: true,
          color: "#312f42",
        },
        min: 4,
        max: 22, //échelle COMPLETEMENT biaisée exprès xD (pour faire + impressionant comme dans les conférences)
        title: {
          display: true,
          color: "#f5f5ff", //texte ?
          text: "Lower is better",
          font: {
            family: "Poppins",
            size: 15,
          },
        },
      },
      y: {
        grid: {
          display: false,
        },
        ticks: {
          color: "#f5f5ff", //texte ?
          beginAtZero: true,
          font: {
            family: "Poppins",
            size: 13,
          },
        }, //couleur texte
      },
    },
    plugins: {
      legend: {
        labels: {
          color: "#FFFFFF",
          font: {
            family: "Poppins",
            size: 20,
          },
        },
      },
    },
  },
});

var hauteur = window.outerHeight;
var hauteurPresentation = document.getElementById("presentation").offsetHeight;
var padding = (hauteur - hauteurPresentation) / 4;
var paddingBot = padding + 30;

document
  .getElementById("presentation")
  .setAttribute(
    "style",
    "padding-top:" + padding + "px;padding-bottom:" + paddingBot + "px;"
  );
