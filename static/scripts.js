let map;
let markers = [];
let newPlaces = [];


$(document).ready(function() {
    $(".sort").click(function() {
        var sort = this.id;
        update (sort);
    });
    update();

    let styles = [
    // Hide Google's labels
        {
            featureType: "all",
            elementType: "labels",
            stylers: [
                {visibility: "off"}
            ]
        },
        {
            featureType: "road",
            elementType: "labels",
            stylers: [
                {visibility: "on"}
            ]
        },
    ];
    // Options for map
    let options = {

        center: {lat: latitude, lng: longitude},
        disableDefaultUI: true,
        mapTypeId: 'hybrid',
        maxZoom: 20,
        panControl: true,
        styles: styles,
        zoom: 15,
        zoomControl: true
    };

    var canvas = $("#map-canvas").get(0);

    map = new google.maps.Map(canvas, options);

    google.maps.event.addListener(map, 'click', function(e) {
        for (var add of newPlaces){
            add.setMap(null);
        }
        var addImage ="/static/img/add.png";
        var location = e.latLng;
        var newPlace = new google.maps.Marker({
             position: location,
             animation: google.maps.Animation.DROP,
             map: map,
             icon: addImage
         });
        newPlaces.push(newPlace);
         var addplace = '<form action="/add_place" method="post">';
             addplace += '<input id="lat" name="lat" type="hidden" value='+location.lat()+'>';
             addplace += '<input id="lng" name="lng" type="hidden" value='+location.lng()+'>';
             addplace += '<button class="btn btn-success" type="submit">ADD NEW PLACE</button>';
             addplace += "</form>";

         google.maps.event.addListener(newPlace, "click", function(e) {
             var infoWindow = new google.maps.InfoWindow({
                 content: addplace,
             });
            infoWindow.open(map, newPlace);
         });
    });
});

// Add marker for place to map

function addMarker(place){
    var image ="/static/img/places.png";
    var myLatLng = { lat: place.lat, lng: place.lng };
    var marker = new google.maps.Marker({
        position: myLatLng,
        map: map,
        title: place.name,
        icon:image
    });

        var information = "<h5>"+place.name+"</h5>";
            information += '<a class="btn btn-info" href="/places/'+ place.id +'" role="button">See details</a>';
    // Open an InfoWindow When Clicking on The Marker
      google.maps.event.addListener(marker, 'click', function() {
        var placeInfo = new google.maps.InfoWindow({
                 content: information,
             });
        placeInfo.open(map, marker);
        });
      markers.push(marker);
}

function removeMarkers(){
    for (var marker of markers){
        marker.setMap(null);
    }
}

function update(sort = ""){
    let parameters = {
        postalCode: postalCode,
        sort: sort
    };
    $.getJSON("/places", parameters, function(data, textStatus, jqXHR) {
       removeMarkers();
       for (let i = 0; i < data.length; i++){
           addMarker(data[i]);
       }
    });
}




