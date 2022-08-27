<?php
error_reporting(0);
$file_dir = "/www/data/json/";
$page = 1;
$totalFiles = glob($file_dir . "*");
if ($totalFiles){
    $page = count($totalFiles);
}
$start_page=1;
$cover=$_GET['cover'];
// 是否请求封面图片
if ($cover!='true'){
    $start_page = 236; // 236到最新页都是1920x1080
}
$json_string = file_get_contents($file_dir.rand($start_page,$page).".json"); 
$data = json_decode($json_string,true);
$imgurl = "";
if ($cover=='true'){
    $imgurl="https://cdn.panghai.top".$data["data"]["data"][rand(0,9)]["path"];
    $imgurl = str_replace("top/bing","top/compress-bing",$imgurl);
}else{
    $imgurl = $data["data"]["data"][rand(0,9)]["url"];
}
header("Location: $imgurl");