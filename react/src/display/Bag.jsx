import React, { Component } from 'react';


class Bag extends Component {

    render() {
        const items = [];

        let panelclass = 'card-body bag-body'
        if (this.props.bag != null) {
            for (const [key, value] of this.props.bag.entries()) {
                items.push(<span key={key} className='tile'>{value}</span>)
            }
            if (this.props.bag.length <= 14) {
                panelclass = panelclass + ' bg-warning'
            }
        }
        return (
            <div className='card my-1'>
                <div className={panelclass}>{items}</div>
            </div>
        );
    }
}

export default Bag;