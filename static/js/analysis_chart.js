function TimeRangePlot(
    container, chart_canvas, url, date, refresh_callback, chart_options
) {

    var initial_date = date;
    var current_date = date;
    var next_date = null;
    var prev_date = null;

    var chart_canvas = chart_canvas
    var chart = null;
    var url = url;

    var time_modes = TIME_MODES
    var time_mode = time_modes[0];

    var stores = [CURRENT_STORE];



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
            },
            onClick: click_function
        }
    } else {
        var chart_options = chart_options;
    }


    container.find('.time_mode').click(function (event) {
        time_mode = $(event.target).data('value');
        refresh_date_data(initial_date);
    });
     


    refresh_date_data(current_date);


    function click_function(data, v) {
        console.log(data, v);
    }


    function refresh_date_data(date) {
        var year = date.getFullYear();
        var month = date.getMonth() + 1;
        var day = date.getDate();

        var request_url = url+'?year='+year+'&month='+month+'&day='+day+'&t_mode='+time_mode+'&stores='+stores.join(',')

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
                //chart.data.datasets = res.chart_data.datasets;
                var i = 0;
                for (i in res.chart_data.datasets) {
                    var dataset = res.chart_data.datasets[i];

                    if (!chart.data.datasets[i] || chart.data.datasets[i].store_id != dataset.store_id
                    ) {
                        chart.data.datasets[i] = dataset;
                    } else {
                        chart.data.datasets[i].data = dataset.data;    
                    }
                }
                i = parseInt(i);
                chart.data.datasets.splice(i + 1, chart.data.datasets.length);
                chart.data.labels = res.chart_data.labels;
                chart.update();
            }

            next_date = new Date(Date.parse( res.next_date ));
            prev_date = new Date(Date.parse( res.prev_date ));
            current_date = new Date(Date.parse( res.current_date ));

            container.find('.chart-card-title').text(res.title);

            // call custom callback with the received data
            if (refresh_callback)
                refresh_callback(res, current_date);
        })
        .fail(function (res) {
        });
    }


    this.add_store = function(v) {
        var intv = parseInt(v); 
        if (stores.indexOf(intv) == -1) {
            stores.push(intv);
        }
        refresh_date_data(current_date);
    }
    this.remove_store = function(v) {
        var intv = parseInt(v); 
        if (stores.indexOf(intv) != -1) {
            var index = stores.indexOf(intv);
            stores.splice(index, 1);
        }
        refresh_date_data(current_date);
    }

    return this;
}