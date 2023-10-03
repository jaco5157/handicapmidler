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

function createProductList(productListName) {
    if (document.querySelector(productListName)) {
        let productList = document.querySelector(productListName);
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
            if (buyButton.nodeName == "IMG") {
                let newButton = document.createElement("span");
                newButton.textContent = "Læg i kurv";
                newButton.className = "btn btn-success w-100";
                newButton.onclick = buyButton.onclick;
                buyButton.insertAdjacentElement("beforebegin", newButton);
                buyButton.remove();
            }
        });
    }
}
createProductList(".ProductList_Custom_DIV");
createProductList(".CustomersAlsoBought_Custom_DIV");


if (document.querySelector(".webshop-productinfo")) {
    if (document.querySelector(".inventory-container")) {
        var inventoryAmount = document.getElementById("inventory-amount");
        if (inventoryAmount.textContent > 100) inventoryAmount.textContent = "100+";
    }

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

    // Style product documentation
    document.getElementById("documentation").querySelectorAll("a").forEach(function (item) {
        item.textContent = item.nextSibling.textContent.trim();
        item.nextSibling.remove();
        item.className = "btn btn-outline-light mb-2 mb-md-0 me-2";
    });

    // Move image when page size changes
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
// webshop-orderstep4 webshop-checkout webshop-terms
if (document.querySelector(".webshop-orderstep4, .webshop-checkout, .webshop-terms")) {
    document.querySelector("main").className += " container py-5";
}


if (document.querySelector(".webshop-checkout")) {

    // Set width of buttons
    if (document.getElementById("customer_lookup_submit")) {
        let checkoutLogin = document.getElementById("customer_lookup_submit");
        checkoutLogin.className += " btn btn-success w-100";
    }
    let checkoutComplete = document.getElementById("confirm-complete-button");
    checkoutComplete.className = "btn btn-success w-100";

    // Set placeholder text for all textboxes
    Array.from(document.getElementsByClassName("showfield-all")).forEach(function (field) {
        if (field.querySelector("select")) return;
        field.querySelector("input").setAttribute("placeholder", field.querySelector("span").textContent);
    });

    // Hide password textbox initially
    var passwordInput = document.getElementById("checkout_password").parentElement;
    passwordInput.style.display = "none";

    // Add textbox for creating password
    let passwordCheckboxString = '<div class="checkout-row"><div class="div-checkout-checkbox"><input autocomplete="false" type="checkbox" class="checkout-checkbox" value="1" id="checkout_create_account" name="checkout_create_account"></div><div class="div-checkout-checkbox-label"><label for="checkout_create_account" class="right-label">Jeg vil gerne oprette en konto</label></div></div>';
    let passwordCheckbox = htmlToElement(passwordCheckboxString);

    // Display password textbox if checkbox is checked
    passwordCheckbox.querySelector("#checkout_create_account").addEventListener('click', function handleClick(event) {
        if (event.target.checked) {
            passwordInput.style.display = 'block';
        } else {
            passwordInput.style.display = 'none';
        }
    });

    passwordInput.insertAdjacentElement("beforebegin", passwordCheckbox);
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

// Creates template element that can be queried
function htmlToElement(html) {
    var template = document.createElement('template');
    html = html.trim(); // Never return a text node of whitespace as the result
    template.innerHTML = html;
    return template.content.firstChild;
}