import Settings from './Settings';

function Header({
    tournament,
    time,
    highlight_reload,
    settings,
    updateSettings,
    commit
}) {
    const items = [];
    for (let i in tournament) {
        if (tournament[i] !== ' ') {
            items.push(<span key={i} className='tile'>{tournament[i].toUpperCase()}</span>);
        } else {
            items.push(<span key={i} className='tile'>&nbsp;</span>);
        }
    }

    let timestr = time.slice(0, time.indexOf('.')); // cut off nano sec
    let commitstr = import.meta.env.VITE_APP_VERSION;
    if (import.meta.env.VITE_APP_VERSION !== commit) {
        commitstr = import.meta.env.VITE_APP_VERSION + '/' + commit;
    }

    const buttonclass = highlight_reload
        ? 'btn btn-link text-danger p-1'
        : 'btn btn-link text-muted p-1';

    return (
        <div className='header bg-body'>
            <div className='card-body'>
                <div className='row'>
                    <div className='justify-content-center text-center m-auto'>
                        {items}
                    </div>
                </div>
                <div className='row'>
                    <div className='justify-content-center text-center m-auto'>
                        <span className='text-muted'>
                            {timestr}&nbsp;{settings.websocket ? 'ws' : '  '}&nbsp;
                            v{import.meta.env.PACKAGE_VERSION}-{commitstr}
                        </span>
                        <span>
                            <button
                                className={buttonclass}
                                onClick={() => window.location.reload()}
                                title='Reload'
                            >
                                &#x21BB;
                            </button>
                        </span>
                        <Settings settings={settings} updateSettings={updateSettings} />
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Header;