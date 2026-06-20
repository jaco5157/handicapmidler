if (avGroups) {
    var selectOther = [];
    var selectColor;
    var selectColorIndex;
    avGroups.forEach(group => {
        groupIndex = avGroups.indexOf(group);
        select = document.querySelector('.VariantGroupPosition-' + (groupIndex + 1) + ' select.OptionSelect_ProductInfo');
        if(group.Name == 'Farve'){
            selectColor = select;
            select.classList.add("hidden");
            selectColorIndex = groupIndex;
            createColorPicker(selectColor, selectColorIndex);
        } else selectOther.push(select);
    });
    if(selectColor){
        selectOther.forEach(select => {
            select.addEventListener('change', () => createColorPicker(selectColor, selectColorIndex))
        })
    }
}

function createColorPicker(select, index){
    var wrapper;
    if(!document.querySelector('.variant-color-wrapper')){
        wrapper = document.createElement('div');
        wrapper.classList.add('variant-color-wrapper','flex-container', 'flex-gap', 'centertext')
    } else {
        wrapper = document.querySelector('.variant-color-wrapper')
        wrapper.innerHTML = "";
    }
    select.querySelectorAll('option').forEach((option, i) => {
        if (i == 0) return;
        var div = document.createElement('div');
        var label = document.createElement('label');
        var radio = document.createElement('input');
        var value = option.value;
        var variantText = document.createTextNode(option.value)
        div.classList.add("variant-color");
        radio.setAttribute('type', 'radio');
        radio.setAttribute('name', 'Farve');
        radio.setAttribute('value', value);

        label.appendChild(radio);
        div.append(label, variantText);
        wrapper.appendChild(div);
        
        var value = option.value.toLowerCase();
        value = value.replace(" ", "-");
        value = value.split("/");
        label.setAttribute('style', 'background-color: var(--'+value[0]+')');
        if(value[1]) {
            var span = document.createElement('span');
            span.setAttribute('style', 'background-color: var(--'+value[1]+')');
            label.appendChild(span);
        }
        if (option.selected) {
            radio.checked = true;
            div.classList.add('selected');
        }
        radio.addEventListener('change', () => {
            selectVariant(radio.value, index, select);
            div.classList.add('selected');
        })
    })
    select.insertAdjacentElement('beforebegin', wrapper);
}

function selectVariant(val, index, select) {
    var selectJ = $(select)
    var option = selectJ.find('option[value="' + val + '"]');
    selectJ[0].selectedIndex = option.index();

    //Der skal opdateres på to forskellige måder alt efter hvilken type variant det drejer sig om.
    //Dandomains eget id
    if (ProductVariantMasterID === "") {
        if (typeof (UpdateBuyControls) === "function") {
            UpdateBuyControls();
        }
    } else {
        avComboSelected(index);
    }
}