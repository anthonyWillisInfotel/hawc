import PropTypes from "prop-types";
import React, {Component} from "react";
import {inject, observer} from "mobx-react";

@inject("store")
@observer
class PreviewPanel extends Component {
    componentDidMount() {
        const {settingsHash, dataset} = this.props.store.base,
            {settings} = this.props.store.subclass;
        const el = document.getElementById(settingsHash);
        if (el) {
            console.log("abc");
            {
                /* TODO - 2. fix preview */
            }
        }
    }

    render() {
        const {settingsHash} = this.props.store.base;
        let content = <div id={settingsHash}>{settingsHash}</div>;
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
