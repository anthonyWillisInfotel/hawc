import React, { Component, PropTypes } from 'react';
import { connect } from 'react-redux';

import { fetchStudy } from 'robAllTable/actions';
import Loading from 'shared/components/Loading';
import DomainCell from 'robAllTable/components/DomainCell';
import './AggregateGraph.css';


class AggregateGraph extends Component {

    componentWillMount(){
        let { dispatch, study_id } = this.props;
        dispatch(fetchStudy(study_id));
    }

    format_qualities(){
        let { qualities } = this.props;
        let domains = _.map(qualities, (quality) => {
            let score = quality;
            score.domain = quality.metric.domain.id;
            score.domain_text = quality.metric.domain.name;
            return score;
        });
        return d3.nest()
                 .key((d) => {return d.metric.domain.name;})
                 .entries(domains);
    }

    render(){
        let { itemsLoaded, qualities } = this.props;
        if (!itemsLoaded) return <Loading />;
        let domains = this.format_qualities();
        console.log("domains", domains);
        return (
            <div className='aggregate-graph'>
                    {_.map(domains, (domain) => {
                        return <DomainCell key={domain.key}
                                           domain={domain}
                                           domain_n={qualities.length} />;
                    })}
            </div>
        );
    }
}

function mapStateToProps(state){
    return {
        study_id: state.config.study.id,
        itemsLoaded: state.study.itemsLoaded,
        qualities: state.study.qualities,
    };
}

export default connect(mapStateToProps)(AggregateGraph);
