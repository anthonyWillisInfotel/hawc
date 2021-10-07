import PropTypes from "prop-types";
import React, {Component} from "react";
import {inject, observer} from "mobx-react";
import {Tab, Tabs, TabList, TabPanel} from "react-tabs";

@inject("store")
@observer
class VisualCustomizationPanel extends Component {
    render() {
        return (
            <div>
                <legend>Visualization customization</legend>
                <p className="form-text text-muted">
                    Customize the look, feel, and layout of the current visual.
                </p>
                {this.renderForm()}
            </div>
        );
    }
    renderForm() {
        const {
            visualCustomizationPanelActiveTab,
            changeActiveVisualCustomizationTab,
        } = this.props.store.subclass;
        return (
            <Tabs
                selectedIndex={visualCustomizationPanelActiveTab}
                onSelect={changeActiveVisualCustomizationTab}>
                <TabList>
                    <Tab>General settings</Tab>
                    <Tab>Included metrics</Tab>
                    <Tab>Included judgments</Tab>
                    <Tab>Legend Settings</Tab>
                </TabList>
                <TabPanel>
                    <p>A</p>
                </TabPanel>
                <TabPanel>
                    <p>B</p>
                </TabPanel>
                <TabPanel>
                    <p>C</p>
                </TabPanel>
                <TabPanel>
                    <p>D</p>
                </TabPanel>
                {/* TODO - 1. fix these panels */}
            </Tabs>
        );
    }
}
VisualCustomizationPanel.propTypes = {
    store: PropTypes.object,
};
export default VisualCustomizationPanel;
