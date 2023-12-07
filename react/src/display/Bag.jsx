import React, { Component } from 'react';


class Bag extends Component {

    render() {
        const items = [];

        if (this.props.bag != null) {
            for (const [key, value] of this.props.bag.entries()) {
                items.push(<span key={key} className='tile'>{value}</span>)
            }
        }
        return (
            <div className='card my-1'>
                <div className='card-body bag-body'>{items}</div>
            </div>
        );
    }
}

export default Bag;