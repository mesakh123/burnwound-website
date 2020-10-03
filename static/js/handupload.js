
  window.addEventListener( "pageshow", function ( event ) {
    var historyTraversal = event.persisted ||
                           ( typeof window.performance != "undefined" &&
                                window.performance.navigation.type === 2 );
    if ( historyTraversal ) {
      // Handle page restore.
      window.location.reload();
    }
  });


  function convertFile(file) {
      return new Promise((resolve,reject)=>{
          let reader = new FileReader()
          reader.onload = () => { resolve(reader.result) }
          reader.onerror = () => { reject(reader.error) }
          reader.readAsDataURL(file)
      })
  }
$("input").change(function(e) {
    console.log("input starting");
        var files = e.originalEvent.srcElement.files;
        $.map(files, file => {
          convertFile(file).
            then(data => {
                insRow(URL.createObjectURL(file),data);
              })
            .catch(err => console.log(err));
        });
});


function insRow(image_url,image) {
    if(document.getElementById("handupload")){
      document.getElementById("handupload").remove();
    }
    var ele = document.createElement('img');
    ele.setAttribute('id','handupload')
    ele.setAttribute('src', image_url);
    ele.setAttribute('name', "images");
    ele.setAttribute('value',image);
    ele.setAttribute('class', "img-fluid upload-image");
    ele.setAttribute('style',style="max-width:300px;max-height:300px;");
    $("#here").after(ele);
}



  $('form').submit(function(e) {
          e.preventDefault();
         var img_ele = document.getElementsByClassName("upload-image")
         var formData = new FormData(this);
         console.log("formdata catched file number : "+img_ele.length);
         if(img_ele.length==0){
            alert('上傳照片不能為空');
            window.location.reload();
         }
         else{
           for (var i=0; i < img_ele.length; i++) {
             formData.append('images', img_ele.item(i).getAttribute("value"));
           }
            $('body').scrollTop(0);
            $("#progressId").show();
            $.ajax({
                xhr : function(){
                  var xhr = new window.XMLHttpRequest();
                  xhr.upload.addEventListener('progress',function(e){
                      if(e.lengthComputable){
                          var percent = Math.round((e.loaded / e.total)*50);
                          $("#progressbar").attr("aria-valuenow",percent*2).css("width",percent+"%").text(percent*2+"%");
                      }
                  });
                  return xhr;
                },
                url: "",
                type: 'POST',
                data: formData,
                cache: false,
                contentType: false,
                processData: false,
                complete: function(xmlHttp) {
                  // xmlHttp is a XMLHttpRquest object
                  $('form').each(function(){
                      //this.reset();   //Here form fields will be cleared.
                  });
                  if (xmlHttp.status == 200) {
                    top.location.href ="/demo/inputdata/";
                  }
                  else{
                    top.location.href = '/demo/';
                  }
                }
            });

         };


  });
