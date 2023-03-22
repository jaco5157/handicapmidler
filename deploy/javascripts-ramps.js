if (document.querySelector(".webshop-productinfo")) {
    // Change look of amount selector
    let amount = document.getElementById("amount");

    let minus = document.createElement('button');
    minus.id = "minus";
    minus.setAttribute("aria-label", "Dekrementer mængde");
    minus.setAttribute("type", "button");

    let plus = document.createElement('button');
    plus.id = "plus";
    plus.setAttribute("aria-label", "Inkrementer mængde");
    plus.setAttribute("type", "button");

    amount.parentNode.append(minus, amount, plus);

    minus.addEventListener("click", function (evt) {
        if (!amount.disabled) amount.stepDown();
        else warningBox.style.display = "block";
    })
    plus.addEventListener("click", function (evt) {
        if (!amount.disabled) amount.stepUp();
        else warningBox.style.display = "block";
    })

    let buyButton = document.querySelector(".buyWrapper input");
    buyButton.type = "submit";
    buyButton.value = "Læg i kurv";
    buyButton.className = "btn btn-success mt-1 buy-button col-lg-7";

    var imageInside = true;

    window.addEventListener("resize", placeImage);

    function placeImage() {
        let mediaQuery = window.matchMedia('(min-width: 768px)')
        // If width is less than "medium" and image is not inside
        if (!mediaQuery.matches && !imageInside) {
            // Move the image inside
            document.querySelector(".inventory-container").insertAdjacentElement("beforebegin", document.querySelector(".product-images"));
            imageInside = true;
        }
        // If width is greater than than "medium" and image is inside
        if (mediaQuery.matches && imageInside) {
            // Move the image outisde
            document.querySelector(".outside-section").insertAdjacentElement("afterbegin", document.querySelector(".product-images"));
            imageInside = false;
        }
    }

    // Fire once to correctly place image
    placeImage();
}