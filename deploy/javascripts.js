//Add div, span to cookie box
document.querySelectorAll('.cookie-policy-consents-container label').forEach(element => {
  element.innerHTML += '<div><span></span></div>';
});

//Seachbar
$(function() {
  var submitIcon = $(".nbsp");
  var submitButton = $(".SubmitButton_SearchPage");
  var inputBox = $(".SearchField_SearchPage");
  var searchBox = $(".SearchPage_TD");
  var isOpen = false;
  submitIcon.click(function() {
    var inputVal = $(".SearchField_SearchPage").val();
    inputVal = $.trim(inputVal).length;
    if (isOpen === false) {
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
  submitIcon.mouseup(function() {
    return false;
  });
  searchBox.mouseup(function() {
    return false;
  });
  $(document).mouseup(function() {
    if (isOpen === true) {
      searchBox.removeClass("SearchPage_TD-open");
    }
  });
});

//Productmenu slidetoggle
var currentWidth = $("body").width();
$('.Heading_Productmenu').click(function() {
  if(currentWidth < 800){
    $('#ProductMenu_List').slideToggle();
  }
});
$(window).resize(function() {
  if(currentWidth === $("body").width()) {
    return false;
  } else if($("body").width() < 800){
    $('#ProductMenu_List').slideUp();
  } else {
    $('#ProductMenu_List').slideDown();
  }
  currentWidth = $("body").width();
});

//Scripts to be run on product page
if(document.querySelector(".webshop-productinfo") !== null){
  
  if(document.querySelector(".selectors") !== null) document.querySelector(".selectors").firstElementChild.className += " active";

  var amount = document.getElementById("amount");

  //Change look of amount selector
  var minus = document.createElement('button');
  minus.id = "minus";
  minus.setAttribute("aria-label", "Fjern mængde");
  minus.setAttribute("type", "button");
  var plus = document.createElement('button');
  plus.id = "plus";
  plus.setAttribute("aria-label", "Tilføj mængde");
  plus.setAttribute("type", "button");
  amount.parentNode.append(minus, amount, plus);

  var warningBox = document.getElementById("warning");
  minus.addEventListener("click", function(evt){
    if(!amount.disabled) amount.stepDown();
    else warningBox.style.display = "block"; 
  })
  plus.addEventListener("click", function(evt){
    if(!amount.disabled) amount.stepUp();
    else warningBox.style.display = "block"; 
  })

  //Check if tabs are empty. If so, remove, click the first tab
  var i, tabs, tabContent, tabLinks;
  tabs = document.querySelector(".tab");
  tabContent = document.getElementsByClassName("tabContent");
  tabLinks = document.getElementsByClassName("tabLinks");
  for (i = 0; i < tabLinks.length; i++) {
    if(tabContent[i].textContent.trim() == ""){
      tabLinks[i].remove();
      tabLinks.splice(i,1);
      tabContent[i].remove();
      tabContent.splice(i,1);
      i--;
    }
  }
  if(tabs.firstElementChild == null){
    tabs.remove();
  } else {
    tabLinks[0].click();
  }

  //Check if documentation exists. If true, add image
  var img = document.createElement('img');
  img.className = "center";
  img.setAttribute("src", "/images/logo/sprites.svg#pdf");
  img.setAttribute("width", "100");
  img.setAttribute("height", "100");
  document.getElementsByClassName("documentation").forEach(function(item){
    if(item.firstChild !== null){
      item.insertAdjacentElement("afterbegin", img.cloneNode(true))};
    }
  );

  //Replace links with child element for addons
  if(document.querySelector(".Related_Custom_DIV") !== null){
    document.querySelector(".Related_Custom_DIV").querySelectorAll("a").forEach(function (item){
      item.insertAdjacentElement('beforebegin',item.firstChild);
      item.remove();
    });
  }

  //Add to basket event
  document.querySelector(".buyWrapper input").addEventListener('click', async function (e) {
    e.preventDefault();
    var amountVal = amount.value;
    try{
      if(amount.disabled) {
        warningBox.style.display = "block"; 
        return;
      }
      var productParam = "";
      var amountParam = "";
      document.getElementsByClassName("addon").forEach(function (item) {
        if(item.querySelector('input').checked){
          productParam += "|" + item.querySelector('span.addonNumber').textContent;
          amountParam += "|" + amountVal;
        }
      });
      fetchurl = "/shop/showbasket.html?AddMultiple=1&ProductID=" + productParam + "&Amount=" + amountParam;
      await fetch(fetchurl).then(function (response) {
        if (!response.ok) throw new Error('Der opstod en fejl, prøv venligst igen.');
        document.querySelector('form[name="myform"]').submit();
      })
    } catch(err) {
      warningBox.textContent = err;
      warningBox.style.display = "block"; 
    }
  });
}

//Add active class to tab when clicked
function openTab(evt, tabName) {
  var i, tabContent, tabLinks;
  tabContent = document.getElementsByClassName("tabContent");
  tabLinks = document.getElementsByClassName("tabLinks");
  for (i = 0; i < tabContent.length; i++) {
    tabContent[i].className = tabContent[i].className.replace(" active", "");
    tabLinks[i].className = tabLinks[i].className.replace(" active", "");
  }
  document.getElementById(tabName).className += " active";
  evt.currentTarget.className += " active";
}

if(document.querySelector(".webshop-productlist") !== null){
  document.getElementsByClassName("BuyButton_ProductList").forEach(function (item){
    if(item.type == "text") item.setAttribute("aria-label", "Indtast antal produkter til køb");
    if(item.type == "image") item.setAttribute("aria-label", "Læg i kurv");
    if(item.nodeName == "IMG") {
        item.setAttribute("alt","Vælg variant");
        item.setAttribute("width","317px");
        item.setAttribute("height","40px");
        item.parentElement.setAttribute("title","Vælg variant");
    }
  })
}

//Add another button to OrderStep1 and OrderStep2
if(document.querySelector(".webshop-orderstep1") !== null){
  document.querySelector(".halfColumn").insertAdjacentElement('afterend',document.querySelector(".OrderStep1_Next_TD").cloneNode(true))
}

if(document.querySelector(".webshop-orderstep2") !== null){
  document.querySelector(".BackgroundColor1_OrderStep2 tbody tr").insertAdjacentElement('afterend',document.querySelector(".OrderStep2_Methods_Next_TD").parentElement.cloneNode(true));
}