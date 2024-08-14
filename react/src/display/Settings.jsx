import React, { Component } from 'react';

class Settings extends Component {
    constructor(props) {
        super(props);
        this.state = {
            show: false,
            obs: props.settings.obs,
            obsbank: this.props.settings.obsbank,
            header_text: props.settings.header_text,
            theme2020: props.settings.theme2020
        };
        this.handleObs = this.handleObs.bind(this);
        this.handleObsBank = this.handleObsBank.bind(this);
        this.handleHeader = this.handleHeader.bind(this);
        this.handleTheme = this.handleTheme.bind(this)
    }

    toggleShow = () => {
        if (this.state.show) {
            // reset fields on close without save
            this.setState({
                obs: this.props.settings.obs,
                obsbank: this.props.settings.obsbank,
                header_text: this.props.settings.header_text,
                theme2020: this.props.settings.theme2020
            })
        }
        this.setState({ show: !this.state.show })
    };

    saveValues = () => {
        this.setState({ show: !this.state.show })
        // set cookie
        const settings = {
            obs: this.state.obs,
            obsbank: this.state.obsbank,
            websocket: this.props.settings.websocket,
            header_text: this.props.settings.header_text,
            theme2020: this.state.theme2020
        }
        this.props.updateSettings(settings)
    };

    componentDidMount() {
        this.setState({
            show: false,
            obs: this.props.settings.obs,
            obsbank: this.props.settings.obsbank,
            header_text: this.props.settings.header_text,
            theme2020: this.props.settings.theme2020
        })
    }

    // componentDidUpdate(prevProps) { }
    // componentWillUnmount() { }

    handleObs(event) {
        this.setState({ obs: !this.state.obs })
    }

    handleObsBank(event) {
        this.setState({ obsbank: !this.state.obsbank })
    }

    handleHeader(event) {
        this.setState({ header_text: event.target.value })
    }

    handleTheme(event) {
        this.setState({ theme2020: !this.state.theme2020 })
    }

    render() {
        return (
            <span>
                <button className='btn btn-sm btn-link p-1' onClick={this.toggleShow} title='Settings'>&#x2699;</button>
                <div className={this.state.show ? '' : 'hidden'} tabIndex='-1'>
                    <div className='modal-dialog modal-dialog-centered' style={{ minWidth: '300px' }} >
                        <div className='modal-content'>
                            <div className='modal-header'>
                                <h5 className='modal-title'>Settings</h5>
                                <button type='button' className='close' data-dismiss='modal' onClick={this.toggleShow} aria-label='Close'>
                                    <span aria-hidden='true'>&times;</span>
                                </button>
                            </div>
                            <div className='modal-body justify-content-left text-left m-auto'>
                                <div className='form-check'>
                                    <input className='form-check-input' type='checkbox' onChange={this.handleObs}
                                        checked={this.state.obs} id='obs'>
                                    </input>
                                    <label className='form-check-label' htmlFor='obs'>
                                        OBS Layout
                                    </label>
                                </div>
                                <div className='form-check'>
                                    <input className='form-check-input' type='checkbox' onChange={this.handleObsBank}
                                        checked={this.state.obsbank} id='obsbank'>
                                    </input>
                                    <label className='form-check-label' htmlFor='obsbank'>
                                        OBS Bank Camera
                                    </label>
                                </div>
                                <div className='form-check'>
                                    <input className='form-check-input' type='checkbox' onChange={this.handleTheme}
                                        checked={this.state.theme2020} id='theme'>
                                    </input>
                                    <label className='form-check-label' htmlFor='theme'>
                                        2020 Theme
                                    </label>
                                </div>
                            </div>
                            <div className='modal-footer'>
                                <button type='button' className='btn btn-secondary' onClick={this.toggleShow} data-dismiss='modal'>Close</button>
                                <button type='button' className='btn btn-primary' onClick={this.saveValues}>Save changes</button>
                            </div>
                        </div>
                    </div>
                </div>
            </span >
        );
    }
}

export default Settings;