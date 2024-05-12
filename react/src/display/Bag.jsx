import React, { Component } from 'react';


class Bag extends Component {

    render() {
        const items = [];
        let cnt_tiles = 0;
        let cnt_bag = 0;

        let panelclass = 'card-body bag-body'
        if (this.props.bag != null) {
            for (const [key, value] of this.props.bag.entries()) {
                items.push(<span key={key} className='tile'>{value}</span>)
            }
            cnt_tiles = this.props.bag.length
            if (this.props.bag.length <= 14) {
                panelclass = panelclass + ' bg-warning'
            } else {
                cnt_bag = this.props.bag.length - 14
            }
        }
        return (
            <div className='card my-1'>
                <div className={panelclass}>{items}<br/>{cnt_tiles} tiles ({cnt_bag} in bag)</div>
            </div>
        );
    }
}

export default Bag;