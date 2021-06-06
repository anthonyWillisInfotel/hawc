import PropTypes from "prop-types";
import React, {Component} from "react";
import {inject, observer} from "mobx-react";
import {Tab, Tabs, TabList, TabPanel} from "react-tabs";

@inject("store")
@observer
class VisualCustomizationPanel extends Component {
    render() {
        let content = this.renderForm();
        return (
            <div>
                <legend>Visualization customization</legend>
                <p className="form-text text-muted">
                    Customize the look, feel, and layout of the current visual.
                </p>
                {content}
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
                    <Tab>Included scores</Tab>
                    <Tab>Legend settings</Tab>
                </TabList>
                <TabPanel>1</TabPanel>
                <TabPanel>2</TabPanel>
                <TabPanel>3</TabPanel>
                <TabPanel>4</TabPanel>
            </Tabs>
        );
    }
}
VisualCustomizationPanel.propTypes = {
    store: PropTypes.object,
};
export default VisualCustomizationPanel;
