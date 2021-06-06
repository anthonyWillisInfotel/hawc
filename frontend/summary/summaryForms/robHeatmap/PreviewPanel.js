import $ from "$";
import PropTypes from "prop-types";
import React, {Component} from "react";
import {inject, observer} from "mobx-react";

import {MissingData, RefreshRequired} from "../heatmap/common";

@inject("store")
@observer
class PreviewPanel extends Component {
    componentDidMount() {
        // const {settingsHash, dataset} = this.props.store.base,
        //     {settings} = this.props.store.subclass;
        // const el = document.getElementById(settingsHash);
        // if (el) {
        //     $(el).append("hi");
        // }
    }

    render() {
        const {hasDataset, dataRefreshRequired, settingsHash} = this.props.store.base;
        let content;
        if (!hasDataset) {
            content = <div id={settingsHash}>{settingsHash}</div>;
        } else if (dataRefreshRequired) {
            content = <div id={settingsHash}>{settingsHash}</div>;
        } else {
            content = <div id={settingsHash}>{settingsHash}</div>;
        }
        return (
            <div>
                <legend>Preview</legend>
                <p className="form-text text-muted">Preview the settings for this visualization.</p>
                {content}
            </div>
        );
    }
}
PreviewPanel.propTypes = {
    store: PropTypes.object,
};
export default PreviewPanel;
