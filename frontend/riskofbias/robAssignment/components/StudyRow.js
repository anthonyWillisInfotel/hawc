import React, {Component} from "react";
import PropTypes from "prop-types";
import {inject, observer} from "mobx-react";

import CreateNewRob from "./CreateNewRob";
import RobItem from "./RobItem";

@inject("store")
@observer
class StudyRow extends Component {
    render() {
        const {study} = this.props,
            {individualReviewsRequired} = this.props.store,
            {edit} = this.props.store.config;

        const individuals = study.robs.filter(rob => !rob.final),
            finals = study.robs.filter(rob => rob.final);

        return (
            <tr>
                <td>
                    <a href={study.url} target="_blank" rel="noreferrer">
                        {study.short_citation}
                    </a>
                </td>
                {individualReviewsRequired ? (
                    <td>
                        {individuals.length > 0 ? (
                            individuals.map(rob => <RobItem key={rob.id} study={study} rob={rob} />)
                        ) : (
                            <p>
                                <i>No individual reviews exist.</i>
                            </p>
                        )}
                        {edit ? <CreateNewRob study={study} final={false} /> : null}
                    </td>
                ) : (
                    <td>
                        <i>Individual reviews are not required.</i>
                    </td>
                )}
                <td>
                    {finals.length > 0 ? (
                        finals.map(rob => <RobItem key={rob.id} study={study} rob={rob} />)
                    ) : (
                        <p>
                            <i>No final reviews exist.</i>
                        </p>
                    )}
                    {edit ? <CreateNewRob study={study} final={true} /> : null}
                </td>
            </tr>
        );
    }
}
StudyRow.propTypes = {
    study: PropTypes.object.isRequired,
    store: PropTypes.object,
};

export default StudyRow;
