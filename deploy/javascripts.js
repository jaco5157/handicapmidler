/*
 GENERAL SCRIPTS
*/
//Seachbar
$(function () {
  var submitIcon = $(".nbsp");
  var submitButton = $(".SubmitButton_SearchPage");
  var inputBox = $(".SearchField_SearchPage");
  var searchBox = $(".SearchPage_TD");
  var isOpen = false;
  inputBox.attr("placeholder", "Søg på Handicapmidler.dk");
  submitIcon.click(function () {
    var inputVal = $(".SearchField_SearchPage").val();
    inputVal = $.trim(inputVal).length;
    if ($("body").width() >= 800) {
      if (inputVal !== 0) {
        submitButton.click();
      } else {
        inputBox.focus();
      }
    } else if (isOpen === false) {
      inputBox.val("");
      searchBox.addClass("SearchPage_TD-open");
      inputBox.focus();
      isOpen = true;
    } else if (inputVal !== 0) {
      submitButton.click();
    } else {
      searchBox.removeClass("SearchPage_TD-open");
      inputBox.focusout();
      isOpen = false;
    }
  });
  //When clicking anywhere other than the searchbox, close the box
  submitIcon.mouseup(function () {
    return false;
  });
  searchBox.mouseup(function () {
    return false;
  });
  $(document).mouseup(function () {
    if (isOpen === true) {
      searchBox.removeClass("SearchPage_TD-open");
      isOpen = false;
    }
  });
});

//Productmenu slidetoggle
var currentWidth = $("body").width();
$('.Heading_Productmenu').click(function () {
  if (currentWidth < 800) {
    $('#ProductMenu_List').slideToggle();
  }
});
$(window).resize(function () {
  if (currentWidth === $("body").width()) {
    return false;
  } else if ($("body").width() < 800) {
    $('#ProductMenu_List').slideUp();
  } else {
    $('#ProductMenu_List').slideDown();
  }
  currentWidth = $("body").width();
});
/*
 END OF GENERAL SCRIPTS
*/

/*
 PRODUCT PAGE SCRIPTS
*/
if (document.querySelector(".webshop-productinfo")) {

  var amount = document.getElementById("amount");

  // Mark first image selector as active
  if (document.querySelector(".selectors")) document.querySelector(".selectors").firstElementChild.className += " active";

  // Create color pickers if any color variants
  if (avGroups) {
    selectOther = [];
    var selectColor;
    avGroups.forEach(group => {
      groupIndex = avGroups.indexOf(group);
      if (group.Name == 'Farve') {
        selectColor = document.querySelector('.VariantGroupPosition-' + (groupIndex + 1) + ' .RadioButton_Container_ProductInfo');
        createColorPicker(selectColor);
      } else {
        selectOther.push(document.querySelector('.VariantGroupPosition-' + (groupIndex + 1) + ' select.OptionSelect_ProductInfo'));
      }
    });
    if (selectColor) {
      selectOther.forEach(select => {
        select.addEventListener('change', () => createColorPicker(selectColor))
      })
    }
  }

  // Change look of amount selector
  var minus = document.createElement('button');
  minus.id = "minus";
  minus.setAttribute("aria-label", "Dekrementer mængde");
  minus.setAttribute("type", "button");
  var plus = document.createElement('button');
  plus.id = "plus";
  plus.setAttribute("aria-label", "Inkrementer mængde");
  plus.setAttribute("type", "button");
  amount.parentNode.append(minus, amount, plus);

  document.querySelector(".buyWrapper input").setAttribute("alt", "Læg i kurv");

  if (document.querySelector(".inventory-container")) {
    var inventoryItem = document.querySelector(".inventory-item-stock .inventory-item-header");
    var inventoryAmount = document.getElementById("inventory-amount");
    if (inventoryAmount.textContent > 100) inventoryAmount.textContent = "100+";
    if (inventoryAmount.textContent < 10 && inventoryAmount.textContent > 0) inventoryItem.parentNode.className += " inventory-item-low-stock";
    if (inventoryAmount.textContent <= 0) {
      inventoryItem.parentNode.className += " inventory-item-no-stock";
      var expectedDeliveryDate = document.querySelector("#delivery-time");
      if (expectedDeliveryDate.textContent.trim() == "0001-01-01T00:00:00") {
        expectedDeliveryDate.textContent = "Kan ikke beregne leveringsdato"
      } else {
        expectedDeliveryDate.textContent = "På lager d. " + new Date(expectedDeliveryDate.textContent.trim()).toLocaleDateString("da-DK", { year: 'numeric', month: 'long', day: 'numeric' })
      }
    }
  }

  if (document.querySelector(".Choose_Variant")) {
    document.querySelector(".Choose_Variant").addEventListener("click", function (evt) {
      window.location.hash = "#prodInfo";
      document.querySelector(".Variants").style.border = "1px solid #4583ed";
      document.querySelector(".Variants").style.borderRadius = "7px";
      document.querySelector(".Variants").style.boxShadow = "0 0 2px #4583ed";
      document.querySelector(".VariantGroupLabel").style.padding = "5px";
    })
  }

  var warningBox = document.getElementById("warning");
  minus.addEventListener("click", function (evt) {
    if (!amount.disabled) amount.stepDown();
    else warningBox.style.display = "block";
  })
  plus.addEventListener("click", function (evt) {
    if (!amount.disabled) amount.stepUp();
    else warningBox.style.display = "block";
  })

  //Check if tabs are empty. If so, remove, click the first tab
  var tabs, tabContent, tabLinks;
  tabs = document.querySelector(".tab");
  tabContent = document.getElementsByClassName("tab-content");
  tabLinks = document.getElementsByClassName("tab-links");
  for (let i = tabLinks.length - 1; i >= 0; i--) {
    if (tabContent[i].textContent.trim()) continue
    tabLinks[i].remove();
    tabContent[i].remove();
  }
  tabLinks = document.getElementsByClassName("tab-links");
  if (tabs.textContent.trim()) {
    tabLinks[0].click();
    if (!amount.disabled) document.querySelector(".more-info-button").style.display = "block";
  }
  else tabs.remove();

  //Check if documentation exists. If true, add image
  var img = document.createElement('img');
  img.className = "center";
  img.setAttribute("src", "/images/logo/sprites.svg#pdf");
  img.setAttribute("width", "100");
  img.setAttribute("height", "100");
  document.getElementsByClassName("documentation").forEach(function (item) {
    if (item.firstChild) {
      item.firstChild.setAttribute("title", "Download dokumentation");
      item.insertAdjacentElement("afterbegin", img.cloneNode(true))
    };
  }
  );

  //Replace links with child element for addons
  if (document.querySelector(".Related_Custom_DIV")) {
    document.querySelector(".Related_Custom_DIV").querySelectorAll("a").forEach(function (item) {
      item.insertAdjacentElement('beforebegin', item.firstChild);
      item.remove();
    });
  }

  //Add to basket event
  document.querySelector(".buyWrapper input").addEventListener('click', async function (e) {
    e.preventDefault();
    var amountVal = amount.value;
    try {
      if (amount.disabled) {
        warningBox.style.display = "block";
        return;
      }
      var productParam = "";
      var amountParam = "";
      document.querySelectorAll(".addon").forEach(function (item) {
        if (item.querySelector('input').checked) {
          productParam += "|" + item.querySelector('span.addon-number').textContent;
          amountParam += "|" + amountVal;
        }
      });
      fetchurl = "/shop/showbasket.html?AddMultiple=1&ProductID=" + productParam + "&Amount=" + amountParam;
      await fetch(fetchurl).then(function (response) {
        if (!response.ok) throw new Error('Der opstod en fejl, prøv venligst igen.');
        document.querySelector('form[name="myform"]').submit();
      })
    } catch (err) {
      warningBox.textContent = err;
      warningBox.style.display = "block";
    }
  });
}

//Create color picker
function createColorPicker(select) {
  select.classList.add('flex-container', 'flex-gap', 'centertext')
  select.querySelectorAll('.advanced-variant-item-container').forEach((option, i) => {
    var input = option.querySelector('input');
    value = input.value.toLowerCase().replace(" ", "-").split("/");
    div = option.querySelector('div');
    div.classList.add('variant-color');
    div.setAttribute('style', 'background-color: var(--' + value[0] + ')');
    option.insertAdjacentElement('afterbegin', div);
    div.addEventListener('click', () => input.click());
    if (value[1]) {
      span = document.createElement('span');
      span.setAttribute('style', 'background-color: var(--' + value[1] + ')');
      div.appendChild(span);
    }
  })
}

//Add active class to tab when clicked
function openTab(evt, tabName) {
  var i, tabContent, tabLinks;
  tabContent = document.getElementsByClassName("tab-content");
  tabLinks = document.getElementsByClassName("tab-links");
  for (i = 0; i < tabContent.length; i++) {
    tabContent[i].className = tabContent[i].className.replace(" active", "");
    tabLinks[i].className = tabLinks[i].className.replace(" active", "");
  }
  document.getElementById(tabName).className += " active";
  evt.currentTarget.className += " active";
}

/*
  END OF PRODUCT PAGE SCRIPTS
*/


/*
 PRODUCTLIST SCRIPTS
*/
function interactableProducts() {
  if (document.querySelector(".webshop-productlist, .CustomersAlsoBought_Custom_DIV, .webshop-frontpage")) {
    // Go to product page when clicking a product
    document.querySelectorAll(".productlist .product, .CustomersAlsoBought_Custom_DIV .product").forEach(function (product) {
      product.addEventListener("click", function (event) {
        // Dont do anything if user clicks the add to basket button
        if (event.target.nodeName == "INPUT" || event.target.nodeName == "IMG" || event.target.nodeName == "SELECT") return false;
        product.querySelector("a").click();
      })
    })
    // Add attributes to input fields
    document.getElementsByClassName("BuyButton_ProductList").forEach(function (item) {
      if (item.type == "text") item.setAttribute("aria-label", "Indtast antal produkter til køb");
      if (item.type == "image") item.setAttribute("aria-label", "Læg i kurv");
      if (item.nodeName == "IMG") {
        item.setAttribute("alt", "Vælg variant");
        item.setAttribute("width", "317px");
        item.setAttribute("height", "40px");
        item.parentElement.setAttribute("title", "Vælg variant");
      }
    })
  }
}
interactableProducts();

/*
 END OF PRODUCTLIST SCRIPTS
*/

/*
 ORDERSTEP SCRIPTS
*/
//Add another button to OrderStep1 and OrderStep2
if (document.querySelector(".webshop-orderstep1")) {
  document.querySelector(".halfColumn").insertAdjacentElement('afterend', document.querySelector(".OrderStep1_Next_TD").cloneNode(true))

  var trWarning = document.createElement("tr");
  var tdWarning = document.createElement("td");
  var warningBox = document.getElementById("warning");
  var cvrButton = document.getElementById("cvr-button");
  trWarning.append(tdWarning);
  trWarning.append(warningBox);
  document.getElementById("Field2_4").insertAdjacentElement("afterend", trWarning);
  document.getElementById("cvrnr").insertAdjacentElement("afterend", cvrButton);
  trWarning.className = "warning-field";
  tdWarning.className = "LabelColumn";

  cvrButton.addEventListener('click', function (e) {
    e.preventDefault();
    var cvr = document.getElementById("cvrnr").value.trim();
    var fetchurl = 'https://cvrapi.dk/api?country=dk&vat=' + cvr;
    try {
      if (cvr == '') {
        warningBox.style.display = "block";
        return;
      }
      var xhttp = new XMLHttpRequest();
      xhttp.onreadystatechange = function () {
        if (this.readyState == 4 && this.status == 200) {
          var responseData = JSON.parse(this.response);
          if (responseData["error"]) throw new Error('Der opstod en fejl, prøv venligst igen.');
          document.getElementById("company").value = responseData["name"];
          document.getElementById("address").value = responseData["address"];
          document.getElementById("zipcode").value = responseData["zipcode"];
          document.getElementById("city").value = responseData["city"];
          document.getElementById("phone").value = responseData["phone"];
          document.getElementById("email").value = responseData["email"];
          warningBox.style.display = "none";
        }
        if (this.readyState == 4 && this.status != 200) throw new Error('Der opstod en fejl, prøv venligst igen.');
      };
      xhttp.open("GET", fetchurl, true);
      xhttp.send();
    } catch (err) {
      warningBox.style.display = "block";
    }
  });
}

window.onload = (event) => {
  if (document.querySelector(".webshop-orderstep2")) {
    document.querySelector(".BackgroundColor1_OrderStep2 tbody tr").insertAdjacentElement('afterend', document.querySelector(".OrderStep2_Methods_Next_TD").parentElement.cloneNode(true));

    addClickBox();
    document.querySelector(".webshop-orderstep2").addEventListener("click", function (event) {
      addClickBox();
      event.target.click();
      event.stopPropagation();
    })
  }
};

function addClickBox() {
  document.querySelectorAll(".checkout-payment-method, #ShippingMethod_54, #ShippingMethod_55, #ShippingMethod_56, #ShippingMethod_57, #GLS_ParselShops_55 tr").forEach(function (item) {
    item.addEventListener("click", function (event) {
      item.querySelector("input").click();
      event.stopPropagation();
    })
  })
}
/*
 END OF ORDERSTEP SCRIPTS
*/