/*global define*/
/*jslint white:true,browser:true*/
define([
    'common/runtime',
    'common/busEventManager',
    'common/props',
    'common/ui',
    'common/html',
    'common/jupyter'
], function(
    Runtime,
    BusEventManager,
    Props,
    UI,
    html,
    JupyterInterop
) {
    'use strict';

    var t = html.tag,
        div = t('div'),
        p = t('p');

    function factory(config) {
        var cell = config.cell,
            runtime = Runtime.make(),
            eventManager = BusEventManager.make({
                bus: runtime.bus()
            }),
            bus = runtime.bus().makeChannelBus({ description: 'output cell bus' }),

            // To be instantiated at attach()
            ui,

            // To be instantiated in start()
            cellBus;

        function doDeleteCell() {
            var parentCellId = Props.getDataItem(cell.metadata, 'kbase.outputCell.parentCellId');
            var content = div([
                p([
                    'Deleting this cell will remove the data visualization, ',
                    'but will not delete the data object, which will still be available ',
                    'in the data panel.'
                ]),
                p(['Parent cell id is ', parentCellId]),
                p('Continue to delete this data cell?')
            ]);
            ui.showConfirmDialog({ title: 'Confirm Cell Deletion', body: content })
                .then(function(confirmed) {
                    if (!confirmed) {
                        return;
                    }
                    runtime.bus().send({
                        jobId: Props.getDataItem(cell.metadata, 'kbase.outputCell.jobId'),
                        outputCellId: Props.getDataItem(cell.metadata, 'kbase.attributes.id')
                    }, {
                        channel: {
                            cell: parentCellId
                        },
                        key: {
                            type: 'output-cell-removed'
                        }
                    });

                    bus.emit('stop');

                    JupyterInterop.deleteCell(cell);
                });
        }

        // Widget API

        eventManager.add(bus.on('run', function(message) {
            // container = message.node;
            ui = UI.make({ node: message.node });

            // Events for comm from the parent.
            eventManager.add(bus.on('stop', function() {
                eventManager.removeAll();
            }));

            cellBus = runtime.bus().makeChannelBus({
                name: {
                    cell: Props.getDataItem(cell.metadata, 'kbase.attributes.id')
                },
                description: 'A cell channel'
            });

            eventManager.add(cellBus.on('delete-cell', function() {
                doDeleteCell();
            }));
        }));

        return {
            bus: bus
        };
    }

    return {
        make: function(config) {
            return factory(config);
        }
    };
});