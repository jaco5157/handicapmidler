if (avGroups) {
    var selectOther = [];
    var selectColor;
    avGroups.forEach(group => {
        groupIndex = avGroups.indexOf(group);
        if(group.Name == 'Farve'){
            selectColor = document.querySelector('.VariantGroupPosition-' + (groupIndex + 1) + ' .RadioButton_Container_ProductInfo');
            createColorPicker(selectColor);
        } else {
            selectOther.push(document.querySelector('.VariantGroupPosition-' + (groupIndex + 1) + ' select.OptionSelect_ProductInfo'));
        }
    });
    if(selectColor){
        selectOther.forEach(select => {
            select.addEventListener('change', () => createColorPicker(selectColor))
        })
    }
}

function createColorPicker(select){
    select.classList.add('flex-container', 'flex-gap', 'centertext')
    select.querySelectorAll('.advanced-variant-item-container').forEach((option, i) => {
        input = option.querySelector('input')
        value = input.value.toLowerCase().replace(" ", "-").split("/");
        div = option.querySelector('div');
        div.classList.add('variant-color');
        div.setAttribute('style', 'background-color: var(--'+value[0]+')');
        option.insertAdjacentElement('afterbegin', div);
        if(value[1]) {
            var span = document.createElement('span');
            span.setAttribute('style', 'background-color: var(--'+value[1]+')');
            div.appendChild(span);
        }
        div.addEventListener('click', () => input.click())
    })
}