import $ from "$";
import React from "react";
import {Provider} from "mobx-react";
import ReactDOM from "react-dom";

import {createRobHeatmapStore} from "../stores";
import App from "./App";

const robHeatmapFormAppStartup = function(el, config, djangoForm) {
    const store = createRobHeatmapStore();
    store.base.setConfig(config);
    store.base.setDjangoForm(djangoForm);

    const Root = (
        <Provider store={store}>
            <App />
        </Provider>
    );
    ReactDOM.render(Root, el);
    $(el).fadeIn();
};

export default robHeatmapFormAppStartup;
