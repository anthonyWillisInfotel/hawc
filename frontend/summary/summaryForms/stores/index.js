import BaseStore from "./BaseStore";
import ExploratoryHeatmapStore from "./ExploratoryHeatmapStore";
import RobHeatmapStore from "./RobHeatmapStore";

class ExploratoryHeatmap {
    constructor() {
        this.base = new BaseStore(this);
        this.subclass = new ExploratoryHeatmapStore(this);
    }
}

class RobHeatmap {
    constructor() {
        this.base = new BaseStore(this);
        this.subclass = new RobHeatmapStore(this);
    }
}

const createExploratoryHeatmapStore = () => new ExploratoryHeatmap(),
    createRobHeatmapStore = () => new RobHeatmap();

export {createExploratoryHeatmapStore, createRobHeatmapStore};
