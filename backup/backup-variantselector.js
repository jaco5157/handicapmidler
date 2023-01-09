$(document).ready(function() {
    if($("body.webshop-productinfo").length > 0){
        avGroups.forEach(function (item) {
            if(item.Name == "Farve"){
                var itemIndex = avGroups.indexOf(item) + 1;
                $('.VariantGroupPosition-'+itemIndex).find('select.OptionSelect_ProductInfo').each(function(i, selectE){
                    console.log(avGroups.indexOf(item))
                    var select = $(selectE);
                    select.find('option').each(function(j, optionE){
                        var option = $(optionE);
                        var radio = $('<input type="radio" />');
                        var selectName = select.attr('name');
                        if(typeof(selectName) === "undefined"){
                            selectName = "defnam";
                        }
                        radio.attr('name', selectName).attr('value', option.val());
                        if (option.is(':selected')){
                            radio.attr('checked', 'checked');
                        }
        
                        //Spring første element over da det altid er "Vælg variant" eller noget lignende.
                        if(j !== 0){
                            select.before(
                                $("<label />").append(radio)
                            );
        
                            radio.change(function(event) {
                                selectVariant($(this).attr("value"), $(this).attr("name"), select);
                            });
                        }
                    });
                    select.hide();
                });
                }
            });
            
    }
});


function selectVariant(val, id, select){
    var option = select.find('option[value="' + val + '"]');
    select[0].selectedIndex = option.index();

    //Der skal opdateres på to forskellige måder alt efter hvilken type variant det drejer sig om.

    //Dandomains eget id
    if(ProductVariantMasterID === ""){
        if(typeof(UpdateBuyControls) === "function"){
            UpdateBuyControls();
        }
    }else{
        avComboSelected(0);
    }
}