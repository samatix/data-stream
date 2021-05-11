$(document).ready(function () {
    var table = $('#data').DataTable({
        "deferRender": true
    });
    var new_orders_table = $('#new_data').DataTable();

    $(function () {
        // Correctly decide between ws:// and wss://
        var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
        var ws_path = ws_scheme + '://' + window.location.host + "/data/stream/";
        console.log("Connecting to " + ws_path);
        var socket = new ReconnectingWebSocket(ws_path);
        console.log(socket);

        // Handle incoming websocket messages
        socket.onmessage = function (message) {
            // Decode the JSON
            var data = JSON.parse(message.data);

            // Handle errors
            if (data.error) {
                alert(data.error);
                return;
            }

            // If content received from the websocket
            if (data.content) {
                var data_content = JSON.parse(data.content);
                $("#datalog").append(data.content);
                // Measure the latency between the time when the websocket is sent and the time when it's received
                let latency = Date.now() - data_content.time * 1000;
                console.log("Elapsed time to get the realtime data : " + latency.toString());

                // Show the latency in the dashboard
                $("#position_latency").html(latency.toFixed(2));

                // If the command is to update existing data
                if (data_content.type === "data.update") {
                    var numberOfRows = table.data().length;

                    // Update only in the shown rows
                    for (var i = 0; i < numberOfRows; i++) {
                        var row = table.row(i);
                        var data_line = row.data();
                        if (data_line.id === data_content.id) {
                            row.data(data_content);
                            $(row.node()).addClass("table-success");
                            // Remove class after 5 seconds
                            setTimeout(function () {
                                $(row.node()).removeClass("table-success");
                            }, 5000);
                            break;
                        }
                    }

                    // Add the row to the broadcaster table
                    let amendedRow = new_orders_table.row.add(data_content).draw();
                    let amendedRowNode = amendedRow.node();
                    $(amendedRowNode).addClass("table-success");

                } else if (data_content.type === "data.new") {
                    // We draw the shown results as there is no way to append a new row to existing data when
                    // using datatable with serverside data. The draw request contacts the server to refresh the page
                    table.draw();
                    // We add the new orders to the boadcaster
                    let addedRow = new_orders_table.row.add(data_content).draw();
                    let addedRowNode = addedRow.node();
                    $(addedRowNode).addClass("table-warning");

                } else {
                    console.log(data_content.type + "Not recognised");
                }

            } else {
                console.log("Cannot handle message!");
            }
        };

        // Realtime button to subscribe or not to realtime data
        $("#realtime").click(function () {
            var realtime = $(this).attr("data-realtime-active");
            if (realtime == "True") {
                console.log("Realtime Deactivation");
                // Deactivate room
                $(this).removeClass("btn-success");
                $(this).addClass("btn-secondary");
                socket.send(JSON.stringify({
                    "command": "unsubscribe"
                }));
                $(this).attr("data-realtime-active", "False");
            } else {
                console.log("Realtime Activation");
                $(this).removeClass("btn-secondary");
                $(this).addClass("btn-success");
                socket.send(JSON.stringify({
                    "command": "subscribe"
                }));
                $(this).attr("data-realtime-active", "True");
            }
        });

        // Helpful debugging
        socket.onopen = function () {
            console.log("Connected to realtime socket");
        };
        socket.onclose = function () {
            console.log("Disconnected from realtime socket");
        }
    });
});
