
function Picture({ image }) {
    if (image == null) {
        return (
            <div className='card moves'>
                <div className='card-body'>
                    <center><div>picture not available</div></center>
                </div>
            </div>
        );
    } else {
        return (
            <div className='card moves'>
                <div className='card-body justify-content-center'>
                    <img src={image} className='img-fluid picture' alt=' ' />
                </div>
            </div>
        );
    }
}

export default Picture;