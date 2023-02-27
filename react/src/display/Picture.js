import React, { Component } from 'react';

class Picture extends Component {

    render() {
        if (this.props.image == null) {
            return (<div className='card moves'>
                <div className='card-body'>
                    <center><div>picture not available</div></center>
                </div>
            </div>);
        } else {
            return (<div className='card moves'>
                <div className='card-body justify-content-center'>
                    <img src={this.props.image} className='img-fluid picture' alt=' ' />
                </div>
            </div>);
        }
    }
}

export default Picture;