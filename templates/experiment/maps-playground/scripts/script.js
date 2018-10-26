
console.log('here');

// Stores a list of the markers currently displayed
markers = [];

// Sets the center location of the map
function SetCenter(center) {
  map.setCenter(center);
}

// Removes all existing markers from the map. Each marker is an
// object that is displayed over the map. We need to do two things
// to clear them:
// 1) Remove them from the map
// 2) Cleaning them from the list which stores them
function ClearMarkers() {
  for (var i = 0; i < markers.length; i++) {
    markers[i].setMap(null);  // Remove from map
  }
  markers = [];  // Empty the array
}

// Handler for the "coordinates" form.
function CenterOnCoords(e){
  ClearMarkers();  // Remove markers if any
  e.preventDefault();  // We don't want this form to reset the page.
  console.log('Address submitted');
  var lat = $('#lat').val();
  var lon = $('#lon').val();
  if (lat === "" || lon === "") {
    // We need non-empty coordinates.
    console.log("Not valid");
    window.alert("Need a valid set of coordinates!")
    return false;
  } else {
    // Maps API takes bad parameters and ignores them, so we
    // are good.
    $('#address').val("");  // Remove text from the address box if there's something
    // Send a POST request to the server, but without refreshing the page.
    // This is called AJAX (Asynchronous Javascript And XML).
    // We don't expect anything in return from the Server.
    $.post( "record_request", { type: "coords",
                                lat: lat,
                                lon: lon } );
    // The request is sent, let's now center the map on the requested coordinates.
    SetCenter({lat: parseFloat(lat),
               lng: parseFloat(lon)});
    // We don't want to zoom in too much.
    if (map.getZoom() > 13) {
      map.setZoom(13);
    }
    return true;
  }
}

// If the user enters an address, we need to convert it into coordinates.
// A JS Object that the google Maps API provides helps us with that.
// The execution happens in the background.
// When Geocoder is done, it will call this function with the result.
function GeocoderCallback(results, status) {
  if (status === "OK") {
    console.log("We've got " + results.length + " results");
    var bounds = new google.maps.LatLngBounds();
    // There could be more than one results.
    for(var i = 0; i < results.length; i++) {
      var location = results[i].geometry.location;
      // Create new marker and place it on the map.
      var marker = new google.maps.Marker({
        position: location,
        map: map,
        title: results[i].formatted_address
      });
      // Save marker in the list, we will need it later to remove it if we want.
      markers.push(marker);
      // Increase the area to be visualized if necessary.
      bounds.extend(marker.getPosition());
    }
    // Let's zoom so that all pins are displayed.
    map.fitBounds(bounds);
    // We don't want to zoom in too much.
    if (map.getZoom() > 13) {
      map.setZoom(13);
    }
  } else {
    console.log("The geocoder failed.")
  }
}

// Convert an address into precise locations, one or more, and calls the callback
// function when done.
function GeotagAddress(search_address) {
  var geocoder = new google.maps.Geocoder();
  geocoder.geocode(
    {address: search_address},  // Arguments for the search.
    GeocoderCallback  // The function that will be called when the conversion is done.
  );
}

// Handler for the "address" form.
function CenterOnAddress(e){
    ClearMarkers();  // Remove markers if any
    e.preventDefault();  // We don't want this form to reset the page.
    console.log('Address submitted');
    var address = $('#address').val();
    if (address === "") {
      console.log("Not valid");
      window.alert("Need a valid address!")
      return false;
    } else {
      console.log("Valid Address");
      $('#lat').val("");
      $('#lon').val("");
      // Send a POST request to the server, but without refreshing the page.
      // This is called AJAX (Asynchronous Javascript And XML).
      // We don't expect anything in return from the Server.
      $.post( "record_request", { type: "address",
                                  address: address } );
      // Request sent, now while the backend stores the search, we want the map
      // to locate the requested address(es) and display them.
      GeotagAddress(address);
      return true;
    }
}

// Initialization for the Maps APIs
function initialize() {
   var mapOptions = {
     center: { lat: -34.397, lng: 150.644},
     zoom: 8
   };
   map = new google.maps.Map(document.getElementById('map-canvas'),
       mapOptions);
}

// The google Map frame has a number of events like any other HTML element.
// Here we set an handler to inialize the map when the map loads. You can
// add listeners for "click", "move" and so on...
google.maps.event.addDomListener(window, 'load', initialize);

$(document).ready(
  function() {
    $('#coord_form').on('submit', CenterOnCoords);
    $('#address_form').on('submit', CenterOnAddress);
    console.log("done");
  }
);
