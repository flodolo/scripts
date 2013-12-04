<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset=utf-8>
    <title>Searchplugins Images</title>
    <style type="text/css">
        body { background-color: #FCFCFC; font-family: Arial, Verdana; font-size: 14px; padding: 10px; }
        p { margin-top: 2px; }
        h2 { clear: both; }
        table {padding: 0; margin: 20px 0; border-collapse: collapse; color: #333; background: #F3F5F7; margin-top: 20px;}
        table a {color: #3A4856; text-decoration: none; border-bottom: 1px solid #DDD;}
        table a:visited {color: #777;}
        table a:hover {color: #000;}
        table thead th {background: #EAECEE; padding: 15px 10px; color: #000; text-align: center; font-weight: bold; vertical-align: top;}
        table tr th {background: #EAECEE;}
        table td.firstsection {padding-left: 40px; border-left: 1px solid #DDD;}
        table td.lastsection {padding-right: 40px; border-right: 1px solid #DDD;}
        table .lastsection:last-child {border-right: 0};
        table tbody, table thead {border-left: 1px solid #DDD; border-right: 1px solid #DDD;}
        table tbody {border-bottom: 1px solid #DDD;}
        table tbody td, table tbody th {padding: 5px 20px; text-align: left;}
        table tbody td {border-bottom: 1px solid #DDD}
        table tbody tr {background: #F5F5F5;}
        table tbody tr.odd {background: #F0F2F4;}
        table tbody tr:hover {background: #EAECEE; color: #111;}
        table img { display: block; margin: 0 auto 5px;}
        td.warnings {color: #F00; font-weight: bold;}
        td.warnings span {color: #FFC130;}
        td.warnings img {float: left; margin-right: 5px;}
        div.navigation { width: 100%; clear: both; padding-top: 10px; }
        ul.switcher { float: left; }
        ul.switcher li { float: left; display: block; margin: 0 5px; width: 80px; text-align: center; padding: 10px 5px; background-color: #DCDCDC; text-transform: uppercase; border: 1px solid #000; list-style: none;}
        ul.switcher li a { text-decoration: none; }
    </style>
</head>

<body>

<?php
    include_once('../locales.inc');
    $filename = '../searchplugins.json';

    $jsondata = file_get_contents($filename);
    $jsonarray = json_decode($jsondata, true);

    $channels = array('trunk', 'aurora', 'beta', 'release');
    $products = array('browser', 'metro', 'mobile');
    $productnames = array('Firefox Desktop', 'Firefox Metro', 'Firefox Mobile (Android)');

    $channel = !empty($_REQUEST['channel']) ? $_REQUEST['channel'] : 'aurora';

    $html_output = "<h1>Searchplugin Images Analysis - " . $channel . "</h1>\n";
    $html_output .= '<p id="update">Last update: ' . $jsonarray["creation_date"] . "</p>\n";
    $html_output .= '<div class="navigation">
    <p>Switch to a different branch</p>
    <ul class="switcher">
    ';
    foreach ($channels as $element) {
        $html_output .= '<li><a href="?channel=' . $element . '">' . $element . '</a></li>';
    }
    $html_output .= "\n</ul>\n</div>";

    $html_output .= '
    <div class="navigation">
    <p>Jump to a product</p>
    <ul class="switcher">
    ';
    foreach ($products as $element) {
        $html_output .= '<li><a href="#' . $element . '">' . $element . '</a></li>';
    }
    $html_output .= "\n</ul>\n</div>";

    foreach ($products as $i=>$product) {
        $html_output .= "<h2><a href='#" . $products[$i] . "' id='" . $products[$i] . "' >" . $productnames[$i] . "</a></h2>\n";
        $yahoo_total = $yahoo_enUS = $bing_total = $bing_enUS = $ebay_total = $ebay_enUS = 0;
        $html_output .= '<table>
                <thead>
                    <tr>
                        <th>Locale</th>
                        <th>Icon</th>
                        <th>Name</th>
                        <th>Description</th>
                        <th>Warnings</th>
                    </tr>
                </thead>
                <tbody>' . "\n";

        foreach ($locales as $locale) {
            if (array_key_exists($product, $jsonarray[$locale])) {
                if (array_key_exists($channel, $jsonarray[$locale][$product])) {
                    // I have searchplugins for this locale
                    foreach ($jsonarray[$locale][$product][$channel] as $key => $singlesp) {
                        if ($key != 'p12n') {
                            $spfilename = strtolower($singlesp['file']);
                            if (strpos($spfilename, 'yahoo') !== false
                            || strpos($spfilename, 'bing')!== false
                            || strpos($spfilename, 'ebay')!== false) {
                                // Print only Yahoo and Bing

                                // Increment counters
                                if (strpos($spfilename, 'yahoo') !== false) {
                                    // It's Yahoo
                                    $yahoo_total++;
                                    if (strpos($singlesp['description'], 'en-US') !== false) {
                                        // It's the en-US version
                                        $yahoo_enUS++;
                                    }
                                }
                                if (strpos($spfilename, 'bing') !== false) {
                                    // It's Bing
                                    $bing_total++;
                                    if (strpos($singlesp['description'], 'en-US') !== false) {
                                        // It's the en-US version
                                        $bing_enUS++;
                                    }
                                }
                                if (strpos($spfilename, 'ebay') !== false) {
                                    // It's eBay
                                    $ebay_total++;
                                    if (strpos($singlesp['description'], 'en-US') !== false) {
                                        // It's the en-US version
                                        $ebay_enUS++;
                                    }
                                }

                                $html_output .= '                   <tr>
                                  <td>' . $locale . '</td>
                                  <td>';

                                foreach ($singlesp['images'] as $imageindex) {
                                    $html_output .= '<img src="' . $jsonarray['images'][$imageindex] . '" alt="searchplugin icon" />';
                                }

                                $html_output .='</td>' . "\n";
                                if ( $singlesp['name'] == 'not available') {
                                    $html_output .=  '                      <td>' . $singlesp['name'] . ' (' . $singlesp['file'] . ")</td>\n";
                                } else {
                                    $html_output .=  '                      <td>' . $singlesp['name'] . ' (' . $singlesp['file'] . ")</td>\n";
                                }
                                if ( strpos($singlesp['description'], 'not available')) {
                                    $html_output .=  '                      <td>' . $singlesp['description'] . "</td></tr>\n";
                                } else {
                                    $html_output .=  '                      <td>' . $singlesp['description'] . "</td>
                                </tr>\n";
                                }
                            }
                        }
                    }
                }
            }
        }
        $html_output .= "</tbody>
                            </table>
                        ";
        $html_output .= "<p><strong>Yahoo:</strong> {$yahoo_total} ({$yahoo_enUS} en-US)\n";
        $html_output .= "<p><strong>Bing:</strong> {$bing_total} ({$bing_enUS} en-US)\n";
        $html_output .= "<p><strong>eBay:</strong> {$ebay_total} ({$ebay_enUS} en-US)\n";
    }

    echo $html_output;
