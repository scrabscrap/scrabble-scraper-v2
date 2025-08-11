import { useEffect, useState } from 'react';

function Settings({ settings, updateSettings }) {
    const [show, setShow] = useState(false);
    const [obs, setObs] = useState(settings.obs);
    const [obsbank, setObsbank] = useState(settings.obsbank);
    const [theme2020, setTheme2020] = useState(settings.theme2020);

    // Wenn sich die übergebenen Settings ändern, lokale Werte synchronisieren
    useEffect(() => {
        setObs(settings.obs);
        setObsbank(settings.obsbank);
        setTheme2020(settings.theme2020);
    }, [settings.obs, settings.obsbank, settings.theme2020]);

    const toggleShow = () => {
        if (show) {
            // Reset fields on close without save
            setObs(settings.obs);
            setObsbank(settings.obsbank);
            setTheme2020(settings.theme2020);
        }
        setShow(!show);
    };

    const saveValues = () => {
        setShow(false);
        const newSettings = {
            ...settings,
            obs,
            obsbank,
            theme2020
        };
        updateSettings(newSettings);
    };

    return (
        <span>
            <button className='btn btn-sm btn-link p-1' onClick={toggleShow} title='Settings'>&#x2699;</button>
            <div className={show ? '' : 'hidden'} tabIndex='-1'>
                <div className='modal-dialog modal-dialog-centered' style={{ minWidth: '300px' }} >
                    <div className='modal-content'>
                        <div className='modal-header'>
                            <h5 className='modal-title'>Settings</h5>
                            <button type='button' className='close' data-dismiss='modal' onClick={toggleShow} aria-label='Close'>
                                <span aria-hidden='true'>&times;</span>
                            </button>
                        </div>
                        <div className='modal-body justify-content-left text-left m-auto'>
                            <div className='form-check'>
                                <input className='form-check-input' type='checkbox'
                                    onChange={() => setObs(!obs)}
                                    checked={obs} id='obs' />
                                <label className='form-check-label' htmlFor='obs'>
                                    OBS Layout
                                </label>
                            </div>
                            <div className='form-check'>
                                <input className='form-check-input' type='checkbox'
                                    onChange={() => setObsbank(!obsbank)}
                                    checked={obsbank} id='obsbank' />
                                <label className='form-check-label' htmlFor='obsbank'>
                                    OBS Bank Camera
                                </label>
                            </div>
                            <div className='form-check'>
                                <input className='form-check-input' type='checkbox'
                                    onChange={() => setTheme2020(!theme2020)}
                                    checked={theme2020} id='theme' />
                                <label className='form-check-label' htmlFor='theme'>
                                    2020 Theme
                                </label>
                            </div>
                        </div>
                        <div className='modal-footer'>
                            <button type='button' className='btn btn-secondary' onClick={toggleShow} data-dismiss='modal'>Close</button>
                            <button type='button' className='btn btn-primary' onClick={saveValues}>Save changes</button>
                        </div>
                    </div>
                </div>
            </div>
        </span>
    );
}

export default Settings;