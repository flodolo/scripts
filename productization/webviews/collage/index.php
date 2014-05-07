<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset=utf-8>
    <title>Searchplugins Images</title>
    <style type="text/css">
        body { background-color: #FCFCFC; font-family: Arial, Verdana; font-size: 14px; margin: 0 auto; width: 300px;}
        h1 { margin-top: 20px;}
    </style>
</head>

<body>

<?php
    include_once('../locales.inc');
    $filename = '../searchplugins.json';

    $channel = 'beta';
    $products = ['browser', 'mobile', 'suite', 'mail'];
    $productnames = ['Firefox Desktop', 'Firefox Mobile (Android)', 'Seamonkey', 'Thunderbird'];

    $jsondata = file_get_contents($filename);
    $jsonarray = json_decode($jsondata, true);

    $html_output = '';
    $images = [];

    foreach ($products as $product_index => $product) {
        $html_output .= "<h1>{$productnames[$product_index]}</h1>\n";
        foreach ($locales as $locale) {
            if ($locale != 'en-US') {
                if (array_key_exists($product, $jsonarray[$locale])) {
                    if (array_key_exists($channel, $jsonarray[$locale][$product])) {
                        // I have searchplugins for this locale
                        foreach ($jsonarray[$locale][$product][$channel] as $key => $singlesp) {
                            if ($key != 'p12n') {
                                foreach ($singlesp['images'] as $imageindex) {
                                    array_push($images, $imageindex);
                                }
                            }
                        }
                    }
                }
            }
        }
        $images = array_unique($images);
        foreach ($images as $imageindex) {
            $html_output .= "<img style='width: 16px; height: 16px; padding: 2px;' src='{$jsonarray['images'][$imageindex]}' />\n";
        }
    }


    //$html_output .= "<p>Total: " + count($images) + "</p>";
    echo $html_output;

