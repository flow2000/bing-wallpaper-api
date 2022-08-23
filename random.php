<?php
error_reporting(0);
$file_dir = "/www/data/json/";
$page = 1;
$totalFiles = glob($file_dir . "*");
if ($totalFiles){
    $page = count($totalFiles);
}
$json_string = file_get_contents($file_dir.rand(1,$page).".json"); 
$data = json_decode($json_string,true);
$imgurl = $data["data"]["data"][rand(0,9)]["url"];
header("Location: $imgurl");