let allNews = [];



// ==========================
// 加载新闻
// ==========================

fetch("articles.json")


.then(response => response.json())


.then(data => {


    allNews = data;



    // 首页30条
    showNews(
        balanceNews(allNews,30)
    );


})


.catch(error => {


    document.getElementById("news").innerHTML =
    "新闻加载失败";


});






// ==========================
// 中国38% 国际62%混排
// ==========================

function balanceNews(list, limit){



    let china =
    list.filter(
        item => item.category=="中国"
    );



    let international =
    list.filter(
        item => item.category=="国际"
    );




    // 随机排序

    china.sort(
        ()=>Math.random()-0.5
    );


    international.sort(
        ()=>Math.random()-0.5
    );



    let result=[];



    // 30条
    // 中国11
    // 国际19

    let chinaCount=11;

    let internationalCount=19;




    while(result.length < limit){



        let pool=[];



        if(internationalCount>0
        &&
        international.length){

            pool.push("国际");

        }



        if(chinaCount>0
        &&
        china.length){

            pool.push("中国");

        }





        if(pool.length==0){

            break;

        }





        let type =
        pool[
            Math.floor(
                Math.random()*pool.length
            )
        ];





        if(type=="国际"){


            result.push(
                international.shift()
            );


            internationalCount--;


        }


        else{


            result.push(
                china.shift()
            );


            chinaCount--;


        }



    }



    return result;



}









// ==========================
// 显示新闻
// ==========================

function showNews(list){



let html="";




list.forEach(item=>{


html += `


<article>


<h2>

<a href="${item.link}" target="_blank">

${item.title}

</a>

</h2>





<div class="info">


${item.category}

|

${item.source}

|

${item.time}


</div>





${item.image ?


`

<img src="${item.image}" loading="lazy">


`

:

""

}






<p>

${item.summary}

</p>





</article>


`;



});




document.getElementById("news").innerHTML = html;



}









// ==========================
// 分类按钮
// ==========================

function filterNews(category){



if(category=="全部"){


showNews(
balanceNews(allNews,30)
);



return;


}





let result =

allNews.filter(

item =>
item.category == category

);





// 中国、国际各20条

result =

result

.sort(
()=>Math.random()-0.5
)

.slice(0,20);





showNews(result);



}
