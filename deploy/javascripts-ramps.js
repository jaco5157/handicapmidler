function createSearchBar() {
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
}

createSearchBar();

if (document.querySelector(".ProductList_Custom_DIV")) {
    createProductList();
}

function createProductList() {
    let productList = document.querySelector(".ProductList_Custom_DIV");
    productList.classList += " row";

    Array.from(productList.children).forEach(function (product) {
        product.className += " col-sm-12 col-md-6 col-lg-4 col-xl-3 mb-4";
        let buyButton = product.querySelector(".product-buy").firstChild;
        if (buyButton.nodeName == "A") {
            buyButton.className = "btn btn-success w-100";
            buyButton.innerHTML = "Vælg variant";
        }
        if (buyButton.nodeName == "INPUT") {
            buyButton.className = "btn btn-success w-100";
            buyButton.value = "Læg i kurv";
            buyButton.type = "submit";
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

if (document.querySelector(".webshop-checkout")) {
    let checkoutLogin = document.getElementById("customer_lookup_submit");
    let checkoutComplete = document.getElementById("confirm-complete-button");
    checkoutLogin.className += " btn btn-success w-100";
    checkoutComplete.className = "btn btn-success w-100";

    Array.from(document.getElementsByClassName("showfield-all")).forEach(function (field) {
        if (field.querySelector("select")) return;
        field.querySelector("input").setAttribute("placeholder", field.querySelector("span").textContent);
    });

    function styleShippingAndPaymentMethods(methods) {
        methods.querySelectorAll("label").forEach(function (inputLabel) {
            if (!inputLabel.querySelector("input").checked) {
                inputLabel.className = "";
                return;
            }
            inputLabel.className = "selected-method"
        })
    }

    // Initial styling
    styleShippingAndPaymentMethods(document.getElementById("column-shipping-payment"));

    // Style when changing shipping method
    document.getElementById("column-shipping-payment").addEventListener("change", (event) => styleShippingAndPaymentMethods(event.currentTarget));

    // Style when ZIP changed
    $(document).ajaxStop(function () {
        styleShippingAndPaymentMethods(document.getElementById("column-shipping-payment"));
    });
}

if (document.querySelector(".webshop-frontpage")) {
    var text = ["hjemmet", "virksomheden", "gæsterne"];
    var counter = 0;
    var elem = document.getElementById("text-spinner");
    var inst = setInterval(change, 3000);
    
    function change() {
      elem.innerHTML = text[counter % text.length];
      counter++;
    }
}
