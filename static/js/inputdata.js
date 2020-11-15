
  window.addEventListener( "pageshow", function ( event ) {
    var historyTraversal = event.persisted ||
                           ( typeof window.performance != "undefined" &&
                                window.performance.navigation.type === 2 );
    if ( historyTraversal ) {
      // Handle page restore.
      window.location.reload();
    }
  });


  $('form').on('submit',function(e) {
        $("#progressIdinputData").show();
  });
