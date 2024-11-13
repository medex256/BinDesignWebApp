function logMessage() {
    fetch('/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        console.log('scan qr code');
    });
}