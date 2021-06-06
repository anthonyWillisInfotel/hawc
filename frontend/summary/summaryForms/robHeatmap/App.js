import PropTypes from "prop-types";
import React, {Component} from "react";
import {inject, observer} from "mobx-react";
import {Tab, Tabs, TabList, TabPanel} from "react-tabs";

import OverallPanel from "./OverallPanel";
import PreviewPanel from "./PreviewPanel";
import VisualCustomizationPanel from "./VisualCustomizationPanel";

@inject("store")
@observer
class App extends Component {
    render() {
        const {cancel_url} = this.props.store.base.config,
            {handleSubmit, handleTabChange} = this.props.store.base,
            handleTabSelection = (newIndex, lastIndex) => {
                handleTabChange(newIndex, lastIndex);
            };

        return (
            <div>
                <Tabs onSelect={handleTabSelection}>
                    <TabList>
                        <Tab>Visualization settings</Tab>
                        <Tab>Figure customization</Tab>
                        <Tab>Preview</Tab>
                    </TabList>
                    <TabPanel>
                        <OverallPanel />
                    </TabPanel>
                    <TabPanel>
                        <VisualCustomizationPanel />
                    </TabPanel>
                    <TabPanel>
                        <PreviewPanel />
                    </TabPanel>
                </Tabs>
                <div className="form-actions">
                    <input
                        type="submit"
                        name="save"
                        value="Save"
                        className="btn btn-primary"
                        onClick={handleSubmit}
                    />
                    <span>&nbsp;</span>
                    <a role="button" className="btn btn-secondary" href={cancel_url}>
                        Cancel
                    </a>
                </div>
            </div>
        );
    }
}
App.propTypes = {
    store: PropTypes.object,
};
export default App;
