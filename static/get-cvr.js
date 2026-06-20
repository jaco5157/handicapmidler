var trWarning = document.createElement("tr");
var tdWarning = document.createElement("td");
var warningBox = document.getElementById("warning");
var cvrButton = document.getElementById("cvr-button");
trWarning.append(tdWarning);
trWarning.append(warningBox);
document.getElementById("Field2_4").insertAdjacentElement("afterend", trWarning);
document.getElementById("cvrnr").insertAdjacentElement("afterend", cvrButton);

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
                if (responseData["error"]) return;
                document.getElementById("company").value = responseData["name"];
                document.getElementById("address").value = responseData["address"];
                document.getElementById("zipcode").value = responseData["zipcode"];
                document.getElementById("city").value = responseData["city"];
                document.getElementById("phone").value = responseData["phone"];
                document.getElementById("email").value = responseData["email"];
            }
            if (this.readyState == 4 && this.status != 200) throw new Error('Der opstod en fejl, prøv venligst igen.');
        };
        xhttp.open("GET", fetchurl, true);
        xhttp.send();
    } catch (err) {
        console.log(err)
    }
});