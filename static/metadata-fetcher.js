(async () => {
    var response = await fetch('https://www.handicapmidler.dk/shop/anti-tip-beskytter-med-442p.html');
    switch (response.status) {
        // status "OK"
        case 200:
			let dataHolder = document.createElement("div");
            dataHolder.innerHTML = await response.text();
			let image = dataHolder.querySelector("meta[property='og:image']").content;
			let title = dataHolder.querySelector("meta[property='og:title']").content;
			let url = dataHolder.querySelector("meta[property='og:url']").content;
			console.log(image);
			console.log(title);
			console.log(url);
            break;
        // status "Not Found"
        case 404:
            console.log('Not Found');
            break;
    }
})();