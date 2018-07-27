$(document).ready(function() {
     $(".find").click(function() {
         $("#emptybody tr:gt(0)").remove();
         var find = $("#request").val();

         $.getJSON("/find_city", {request : find}, function(data, textStatus, jqXHR) {
             $(".hidden").css("display", "block");
             for (var place of data){
                 $("#emptybody").append('<tr id="append"><td><input type="radio" id="radioButton" name="city" value='+ place.postal_code +'></td><td>'
                 + place.country_code + '</td><td>'
                 + place.postal_code + '</td><td>'
                 + place.place_name + '</td><td>'
                 + place.admin_name1 + '</td><td>'
                 + place.admin_code1 + '</td></tr>');
             }
        });
    });

    $('#repPass').change(function() {
                    var pass = $("#pass").val();
                    var pass_rep = $("#repPass").val();

                    if (pass != pass_rep) {
                        $("#repPass").css('border', 'red 1px solid');
                        $('#errorBlock').html('Passwords do not match');
                        var pass_rep = $("#repPass").val('');
                    }
                });
})