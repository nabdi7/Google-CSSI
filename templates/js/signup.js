// (document).ready(function(){
//   M.updateTextFields();
// });


// Chip/Tags for entering 'Courses' on signup form
document.addEventListener('DOMContentLoaded', function() {
  var elems = document.querySelectorAll('.chips');
  var instances = M.Chips.init(elems,options);
});

var chip = {
  tag: 'chip content'
  // image: ''
}


var instance = M.Chips.getInstance(elem);
