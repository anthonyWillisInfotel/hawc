import {action} from "mobx";

class RobHeatmapStore {
    constructor(rootStore) {
        this.root = rootStore;
    }

    @action.bound setFromJsonSettings(settings, firstTime) {}
}

export default RobHeatmapStore;
