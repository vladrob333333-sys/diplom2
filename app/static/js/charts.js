// Общие функции для графиков
function createPieChart(ctx, labels, data, colors) {
    return new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors
            }]
        }
    });
}
