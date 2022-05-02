$(document).ready(function(){
    var size = document.querySelectorAll('#size');
    var price = document.querySelectorAll('#price');
    
    size.forEach((link, index) => {
        link.addEventListener('change', function(){
            if(this.value != ""){
                $.ajax({
                    url: '/fetchdata',
                    type: 'POST',
                    data: {id:this.value},
                    success: function(data){
                        price[index].innerHTML = data;
                    }
                })
            }else{
                price[index].innerHTML = "";
            }
        })
    });

    var detailBtn = document.querySelectorAll('#orderdetails');
    detailBtn.forEach(link => {
        link.addEventListener('click', function(){
            var orderid = this.getAttribute('data-id');
            $.ajax({
                url: '/fetchorderdetails',
                type: 'POST',
                data: {orderid:orderid},
                success: function(data){
                    $('#details').html(data);
                }
            })
        })
    })
});