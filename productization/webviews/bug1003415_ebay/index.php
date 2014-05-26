<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset=utf-8>
    <title>eBay checks</title>
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
    </style>
</head>

<body>

<?php
    include_once('../locales.inc');
    $filename = '../searchplugins.json';

    $jsondata = file_get_contents($filename);
    $jsonarray = json_decode($jsondata, true);

    $channel = 'aurora';
    $products = array('browser', 'mobile');
    $productnames = array('Firefox Desktop', 'Firefox Mobile (Android)');
    $html_output = '';
    $details = "
    <h1>Details localized versions</h1>
        <table>
            <thead>
                <tr>
                    <th>Product</th>
                    <th>Locale</th>
                    <th>Name</th>
                    <th>File</th>
                </tr>
            </thead>
            <tbody>
    ";

    $available_variants = [];

    echo "<p>Last update: {$jsonarray['creation_date']}</p>\n";

    foreach ($products as $i=>$product) {
        $html_output .= "<h1>{$productnames[$i]} - {$channel}</h1>";
        $locale_list = '';
        $nonen_locale_list = '';
        foreach ($locales as $locale) {
            if (array_key_exists($product, $jsonarray[$locale])) {
                if (array_key_exists($channel, $jsonarray[$locale][$product])) {
                    // I have searchplugins for this locale
                    foreach ($jsonarray[$locale][$product][$channel] as $key => $singlesp) {
                        if ($key != 'p12n') {
                            $spfilename = strtolower($singlesp['file']);
                            if (strpos($spfilename, 'ebay') !== false) {
                               $locale_list .= "{$locale}, ";
                               if (strpos($singlesp['description'], 'en-US') === false) {
                                    $nonen_locale_list .= "{$locale}, ";
                                    $details .= "<tr>
                                        <td>$productnames[$i]</td>
                                        <td>$locale</td>
                                        <td>{$singlesp['name']}</td>
                                        <td>{$singlesp['file']}</td>
                                    </tr>\n";
                                    $pluginname = $productnames[$i] . ' - ' . $singlesp['file'];
                                    if (! in_array($pluginname, $available_variants)) {
                                        array_push($available_variants, $pluginname);
                                    }
                               }
                            }
                        }
                    }
                }
            }
        }
        $html_output .= "<p>List of locales with eBay (en-US version): {$locale_list}</p>";
        $html_output .= "<p>List of locales with localized versions of eBay: {$nonen_locale_list}</p>";
    }

    echo $html_output;
    echo '<h1>Available variants</h1><ul>';
    foreach ($available_variants as $name) {
        echo "<li>$name</li>\n";
    }
    echo '</ul>';
    echo $details . "</tbody>\n</table></body></html>";

