import PropTypes from "prop-types";
import React, {Component} from "react";
import {inject, observer} from "mobx-react";

@inject("store")
@observer
class DataPanel extends Component {
    render() {
        return (
            <div>
                <ul>
                    <li>Study selector</li>
                    <li>Sort order</li>
                    <li>Prefilter (system, organ, effect, subtype)</li>
                </ul>
            </div>
            /* TODO - 3. fix data */
            /* TODO - 4. get data from api? */
            /* TODO - 5. extend/rename robHeatmap to robHeatmap and robBarchart */
        );
    }
}

DataPanel.propTypes = {
    store: PropTypes.object,
};
export default DataPanel;
