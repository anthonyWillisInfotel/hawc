import {action, observable} from "mobx";

import BaseStore from "./BaseStore";

class RobStore {
    constructor() {
        this.base = new BaseStore(this);
        this.subclass = this;
    }

    getDefaultSettings() {
        return {};
    }

    @observable settings = null;

    @action.bound setFromJsonSettings(settings) {
        this.settings = settings;
    }

    @observable visualCustomizationPanelActiveTab = 0;
    @action.bound changeActiveVisualCustomizationTab(index) {
        this.visualCustomizationPanelActiveTab = index;
        return true;
    }
}

export default RobStore;
