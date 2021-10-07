import $ from "$";
import React from "react";
import ReactDOM from "react-dom";
import {Provider} from "mobx-react";

import App from "./App";
import RobStore from "../stores/RobStore";

const startup = function(el, config, djangoForm) {
    const store = new RobStore();
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

// NEW:
// http://127.0.0.1:8000/summary/visual/assessment/1/risk-bias-heatmap-example/update/
// OLD:
// https://hawcproject.org/summary/visual/assessment/1/risk-bias-heatmap-example/update/

export default startup;
