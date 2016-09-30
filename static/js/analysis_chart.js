function TimeRangePlot(
    container, chart_canvas, url, date, refresh_callback, chart_options
) {

    var current_date = date;
    var next_date = null;
    var prev_date = null;

    var chart_canvas = chart_canvas
    var chart = null;
    var url = url;

    if (!chart_options) {
        var chart_options = {
            scales: {
                yAxes: [{
                    ticks: {
                        suggestedMin: 0,
                        min: 0,
                        beginAtZero: true
                    }
                }]
            }
        }
    } else {
        var chart_options = chart_options;
    }
     


    refresh_date_data(current_date);



    function refresh_date_data(date) {
        var year = date.getFullYear();
        var month = date.getMonth() + 1;
        var day = date.getDate();

        var request_url = url+'?year='+year+'&month='+month+'&day='+day

        $.ajax({
            url: request_url
        })
        .done(function (res) {
            if (!chart) {
                // generate chart
                var ctx = chart_canvas.get(0).getContext("2d");
                chart = new Chart(ctx, {
                    type: 'line', data: res.chart_data,
                    options: chart_options 
                });

                container.find('.btn-prev').click(function () {
                    refresh_date_data( prev_date );
                });
                container.find('.btn-next').click(function () {
                    refresh_date_data( next_date );
                });

            } else {
                // update chart data
                for (var i in res.chart_data.datasets) {
                    chart.data.datasets[i].data = res.chart_data.datasets[i].data;
                }
                chart.update();
            }

            next_date = new Date(Date.parse( res.next_date ));
            prev_date = new Date(Date.parse( res.prev_date ));
            current_date = new Date(Date.parse( res.current_date ));

            if (today_date.getTime() === current_date.getTime()) {
                container.find('.chart-card-title').text(
                    "{{=T('Today')}}"
                );
            } else {
                container.find('.chart-card-title').text(
                    current_date.toLocaleDateString()
                );
            }

            // call custom callback with the received data
            if (refresh_callback)
                refresh_callback(res, current_date);
        })
        .fail(function (res) {
        });
    }


    return this;
}