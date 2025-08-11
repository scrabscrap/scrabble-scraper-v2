
function Bag({ bag }) {
    const items = [];
    let cnt_tiles = 0;
    let cnt_bag = 0;

    let panelclass = 'card-body bag-body';
    if (bag != null) {
        for (const [key, value] of bag.entries()) {
            if (value === '_') {
                items.push(<span key={key} className='tile'>&nbsp;</span>);
            } else {
                items.push(<span key={key} className='tile'>{value}</span>);
            }
        }
        cnt_tiles = bag.length;
        if (bag.length <= 14) {
            panelclass = panelclass + ' bg-warning';
        } else {
            cnt_bag = bag.length - 14;
        }
    }

    return (
        <div className='card my-1'>
            <div className={panelclass}>
                {items}
                <br />
                {cnt_tiles} tiles ({cnt_bag} in bag)
            </div>
        </div>
    );
}

export default Bag;