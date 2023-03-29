if (document.querySelector(".webshop-productlist")) {
    let productList = document.querySelector(".ProductList_Custom_DIV");
    productList.classList += " row";

    Array.from(productList.children).forEach(function (product) {
        product.className += " col-sm-12 col-md-6 col-lg-4 col-xl-3";
        product.querySelector(".product-image img").className += " card-img-top";
        let buyButton = product.querySelector(".product-buy").firstChild;
        if(buyButton.nodeName == "A"){
            buyButton.className = "btn btn-primary col-12";
            buyButton.innerHTML = "Vælg variant";
        }
        if(buyButton.nodeName == "INPUT"){
            buyButton.className = "btn btn-success col-12";
            buyButton.value = "Læg i kurv";
        }
    });
}

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
    buyButton.className = "btn btn-success mt-1 buy-button col-12 col-lg-8 col-xl-7";

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

window.addEventListener("load", (event) => {
    let searchForm = document.getElementById("Search_Form");
    let searchField = searchForm.querySelector(".SearchField_SearchPage");
    let searchButton = searchForm.querySelector(".SubmitButton_SearchPage");

    searchForm.setAttribute("class", "d-flex me-auto ms-auto");
    searchForm.setAttribute("role", "search");

    searchField.className += " form-control me-2";
    searchField.setAttribute("type", "search");
    searchField.setAttribute("placeholder", "Søg efter produkter...");
    searchField.setAttribute("aria-label", "Søg efter produkter");
    searchField.setAttribute("size", "");

    searchButton.className += " btn btn-outline-light";
    searchButton.value = "Søg";
});
